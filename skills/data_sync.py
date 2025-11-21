"""
数据同步技能

提供增量市场数据同步功能，供 Commander 调用。
"""

import logging
from datetime import datetime
from typing import Dict, List
import pytz
import httpx

from data_lake.market_data_manager import insert_bars, get_latest_bar, OHLCVBar
from data_lake.db_helpers import get_db_connection
from skills.market_calendar import get_market_session_info

logger = logging.getLogger(__name__)
ET = pytz.timezone('US/Eastern')

# ThetaData Terminal Server configuration
THETA_API_BASE_URL = "http://127.0.0.1:25503"  # ThetaData Terminal 端口


def fetch_stock_snapshot_quote(symbols: List[str]) -> Dict:
    """
    使用 httpx 从 ThetaData Terminal Server 获取股票快照 OHLC 数据

    Args:
        symbols: 股票代码列表

    Returns:
        {
            'success': bool,
            'data': List[Dict],  # 每个股票的快照数据
            'errors': List[str]
        }
    """
    try:
        # ThetaData snapshot API 端点 - 使用 OHLC (v3 API)
        url = f"{THETA_API_BASE_URL}/v3/stock/snapshot/ohlc"

        # 构建请求参数 (v3 使用 'symbol' 而不是 'root')
        params = {
            'symbol': ','.join(symbols),  # 逗号分隔的股票列表
            'venue': 'utp_cta',  # 使用 UTP & CTA 15 分钟延迟数据（无需高级订阅）
            'format': 'json'  # 指定返回 JSON 格式（默认是 CSV）
        }

        # 发送 HTTP GET 请求
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()

            # 解析响应
            result = response.json()

            # ThetaData v3 API 返回格式：
            # {
            #     "response": [
            #         {"symbol": "SPY", "open": 672.9, "high": 675.56, ...},
            #         {"symbol": "QQQ", "open": 611.67, "high": 614.03, ...}
            #     ]
            # }

            if 'response' not in result:
                return {
                    'success': False,
                    'data': [],
                    'errors': [f"Invalid response format: missing 'response' key"]
                }

            # v3 API 直接返回字典列表，无需转换
            snapshots = result['response']

            return {
                'success': True,
                'data': snapshots,
                'errors': []
            }

    except httpx.TimeoutException as e:
        logger.error(f"ThetaData API timeout: {e}")
        return {
            'success': False,
            'data': [],
            'errors': [f"API request timeout: {str(e)}"]
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"ThetaData API HTTP error: {e}")
        return {
            'success': False,
            'data': [],
            'errors': [f"HTTP {e.response.status_code}: {str(e)}"]
        }
    except Exception as e:
        logger.error(f"Failed to fetch snapshot: {e}")
        return {
            'success': False,
            'data': [],
            'errors': [f"Unexpected error: {str(e)}"]
        }


def fetch_stock_eod_data(symbols: List[str]) -> Dict:
    """
    从 ThetaData Terminal Server 获取股票 EOD 数据

    当市场关闭时使用此函数获取最新收盘数据。

    Args:
        symbols: 股票代码列表

    Returns:
        {
            'success': bool,
            'data': List[Dict],  # 每个股票的EOD数据
            'errors': List[str]
        }
    """
    try:
        # 获取昨天的日期（EOD数据通常在当天收盘后可用）
        from datetime import datetime, timedelta
        eastern = pytz.timezone('US/Eastern')
        yesterday = (datetime.now(eastern) - timedelta(days=1)).strftime('%Y-%m-%d')

        # ThetaData EOD API 端点
        url = f"{THETA_API_BASE_URL}/v3/stock/history/eod"

        eod_data = []
        errors = []

        # 逐个查询EOD数据（避免CSV格式解析问题）
        for symbol in symbols:
            try:
                params = {
                    'symbol': symbol,
                    'start_date': yesterday,
                    'end_date': yesterday
                }

                with httpx.Client(timeout=30.0) as client:
                    response = client.get(url, params=params)
                    response.raise_for_status()

                    # 解析CSV响应（EOD API返回CSV格式）
                    lines = response.text.strip().split('\n')
                    if len(lines) >= 2:  # 标题行 + 数据行
                        # 解析CSV数据
                        data_line = lines[1]
                        fields = data_line.split(',')

                        if len(fields) >= 7:
                            eod_record = {
                                'symbol': symbol,
                                'date': yesterday,
                                'timestamp': fields[0],  # created timestamp
                                'last_trade': fields[1],
                                'open': float(fields[2]),
                                'high': float(fields[3]),
                                'low': float(fields[4]),
                                'close': float(fields[5]),
                                'volume': int(fields[6])
                            }
                            eod_data.append(eod_record)
                        else:
                            errors.append(f"{symbol}: EOD数据格式不完整")
                    else:
                        errors.append(f"{symbol}: 无EOD数据")

            except Exception as e:
                errors.append(f"{symbol}: EOD获取失败 - {str(e)}")

        return {
            'success': len(eod_data) > 0,
            'data': eod_data,
            'errors': errors
        }

    except Exception as e:
        logger.error(f"Failed to fetch EOD data: {e}")
        return {
            'success': False,
            'data': [],
            'errors': [f"EOD API error: {str(e)}"]
        }


def get_watchlist_symbols() -> List[Dict]:
    """
    获取观察列表中的所有活跃股票

    Returns:
        List of dicts: [{'symbol': 'AAPL', 'priority': 10, 'notes': '...'}]
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT symbol, priority, notes
            FROM watchlist
            WHERE active = 1
            ORDER BY priority DESC, symbol ASC
        """)

        symbols = []
        for row in cursor.fetchall():
            symbols.append({
                'symbol': row['symbol'],
                'priority': row['priority'],
                'notes': row['notes'] or ''
            })

        return symbols


def process_snapshot_and_cache(symbol: str, snapshot_data: Dict) -> Dict:
    """
    处理 ThetaData 快照并缓存到数据库

    Args:
        symbol: 股票代码
        snapshot_data: ThetaData REST API 返回的快照数据
            {
                'timestamp': str,  # ISO format timestamp from ThetaData
                'open': float,
                'high': float,
                'low': float,
                'close': float,
                'volume': int,
                'vwap': float (optional)
            }

    Returns:
        {
            'success': bool,
            'symbol': str,
            'bars_added': int,  # 0 表示数据已存在（去重）
            'timestamp': str,
            'error': str (if failed)
        }
    """
    try:
        # 使用快照中的时间戳，或生成当前时间戳
        if 'timestamp' in snapshot_data and snapshot_data['timestamp']:
            # 解析 ThetaData 返回的时间戳
            timestamp_str = snapshot_data['timestamp']

            # 修复时间戳格式问题（例如：'2025-11-20T12:04:33.99' 只有2位毫秒）
            # ThetaData 可能返回不完整的毫秒数，需要补齐到3位
            if '.' in timestamp_str and not timestamp_str.endswith('Z'):
                parts = timestamp_str.rsplit('.', 1)
                if len(parts) == 2:
                    base, frac = parts
                    # 补齐毫秒数到3位
                    frac_digits = frac.split('+')[0].split('-')[0]  # 去除时区部分
                    if len(frac_digits) < 3:
                        frac = frac_digits.ljust(3, '0') + frac[len(frac_digits):]
                    timestamp_str = f"{base}.{frac}"

            snapshot_time = datetime.fromisoformat(timestamp_str)
            # 确保时区一致（如果是 naive，则本地化到 ET）
            if snapshot_time.tzinfo is None:
                snapshot_time = ET.localize(snapshot_time)
            else:
                snapshot_time = snapshot_time.astimezone(ET)
        else:
            # Fallback: 使用当前时间
            snapshot_time = datetime.now(ET)

        # 四舍五入到5分钟间隔（用于去重）
        minutes = (snapshot_time.minute // 5) * 5
        timestamp = snapshot_time.replace(minute=minutes, second=0, microsecond=0).isoformat()

        # 构造 OHLCV 数据条
        bar = OHLCVBar(
            symbol=symbol,
            timestamp=timestamp,
            open=float(snapshot_data.get('open', 0)),
            high=float(snapshot_data.get('high', 0)),
            low=float(snapshot_data.get('low', 0)),
            close=float(snapshot_data.get('close', 0)),
            volume=int(snapshot_data.get('volume', 0)),
            vwap=float(snapshot_data.get('vwap')) if snapshot_data.get('vwap') else None
        )

        # 插入数据库（自动去重）
        count = insert_bars(symbol, [bar])

        return {
            'success': True,
            'symbol': symbol,
            'bars_added': count,  # 0 = 已存在, 1 = 新增
            'timestamp': timestamp,
            'bar': bar.to_dict()
        }

    except Exception as e:
        logger.error(f"Failed to process {symbol} snapshot: {e}")
        return {
            'success': False,
            'symbol': symbol,
            'error': str(e)
        }


def sync_watchlist_incremental(
    skip_if_market_closed: bool = True,
    max_symbols: int = None
) -> Dict:
    """
    增量同步观察列表数据（直接从 ThetaData API 获取并缓存）

    使用 httpx 调用 ThetaData Terminal Server API 获取快照数据，
    并自动缓存到本地数据库。

    Args:
        skip_if_market_closed: 如果市场关闭，是否跳过同步
        max_symbols: 最多同步多少个股票（用于测试）

    Returns:
        {
            'success': bool,
            'market_status': dict,
            'total_symbols': int,
            'synced_count': int,
            'failed_count': int,
            'results': List[Dict],  # 每个股票的同步结果
            'errors': List[str],
            'execution_time': float
        }
    """
    import time
    start_time = time.time()

    # 检查市场状态
    session_info = get_market_session_info()

    if skip_if_market_closed and not session_info['market_open']:
        return {
            'success': False,
            'market_status': session_info,
            'total_symbols': 0,
            'synced_count': 0,
            'failed_count': 0,
            'results': [],
            'errors': [f"市场已关闭 ({session_info['session']})。下次开盘: {session_info.get('next_market_open', '未知')}"],
            'execution_time': time.time() - start_time
        }

    # 获取观察列表
    watchlist = get_watchlist_symbols()

    if not watchlist:
        return {
            'success': False,
            'market_status': session_info,
            'total_symbols': 0,
            'synced_count': 0,
            'failed_count': 0,
            'results': [],
            'errors': ['Watchlist is empty'],
            'execution_time': time.time() - start_time
        }

    # 提取股票代码
    symbols = [item['symbol'] for item in watchlist]

    # 限制数量（用于测试）
    if max_symbols:
        symbols = symbols[:max_symbols]

    # 根据市场状态选择数据源
    if session_info['market_open']:
        # 市场开盘：使用快照数据
        snapshot_result = fetch_stock_snapshot_quote(symbols)
        data_source = "snapshot"
    else:
        # 市场关闭：使用EOD数据
        snapshot_result = fetch_stock_eod_data(symbols)
        data_source = "eod"

    if not snapshot_result['success']:
        return {
            'success': False,
            'market_status': session_info,
            'total_symbols': len(symbols),
            'synced_count': 0,
            'failed_count': len(symbols),
            'results': [],
            'errors': [f"{data_source.upper()} API 失败: " + ", ".join(snapshot_result['errors'])],
            'execution_time': time.time() - start_time
        }

    # 处理每个快照数据并缓存到数据库
    results = []
    synced_count = 0
    failed_count = 0
    errors = []

    for snapshot in snapshot_result['data']:
        try:
            # 根据数据源格式提取股票代码和标准化数据
            if data_source == "snapshot":
                # 快照数据格式
                symbol = snapshot.get('symbol', 'UNKNOWN')
                normalized_snapshot = {
                    'timestamp': snapshot.get('timestamp'),
                    'open': snapshot.get('open'),
                    'high': snapshot.get('high'),
                    'low': snapshot.get('low'),
                    'close': snapshot.get('close'),
                    'volume': snapshot.get('volume'),
                    'vwap': snapshot.get('vwap')  # 可选字段
                }
            else:
                # EOD数据格式
                symbol = snapshot.get('symbol', 'UNKNOWN')
                # EOD数据需要转换时间戳格式
                eod_timestamp = snapshot.get('timestamp')
                if eod_timestamp:
                    # 为EOD数据创建5分钟间隔的时间戳（使用收盘时间）
                    from datetime import datetime, timedelta
                    eod_date = datetime.fromisoformat(eod_timestamp.replace('Z', '+00:00'))
                    # 使用收盘时间 16:00 ET 作为时间戳
                    close_time = eod_date.replace(hour=16, minute=0, second=0, microsecond=0)
                    if close_time.tzinfo is None:
                        close_time = ET.localize(close_time)
                    timestamp = close_time.isoformat()
                else:
                    timestamp = datetime.now(ET).isoformat()

                normalized_snapshot = {
                    'timestamp': timestamp,
                    'open': snapshot.get('open'),
                    'high': snapshot.get('high'),
                    'low': snapshot.get('low'),
                    'close': snapshot.get('close'),
                    'volume': snapshot.get('volume'),
                    'vwap': None  # EOD数据没有VWAP
                }

            # 缓存到数据库
            cache_result = process_snapshot_and_cache(symbol, normalized_snapshot)

            if cache_result['success']:
                synced_count += 1
                results.append({
                    'symbol': symbol,
                    'status': 'synced',
                    'bars_added': cache_result['bars_added'],
                    'timestamp': cache_result['timestamp']
                })
            else:
                failed_count += 1
                errors.append(f"{symbol}: {cache_result.get('error', 'Unknown error')}")
                results.append({
                    'symbol': symbol,
                    'status': 'failed',
                    'error': cache_result.get('error')
                })

        except Exception as e:
            failed_count += 1
            error_msg = f"Failed to process {snapshot.get('symbol', 'UNKNOWN')}: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
            results.append({
                'symbol': snapshot.get('symbol', 'UNKNOWN'),
                'status': 'error',
                'error': str(e)
            })

    execution_time = time.time() - start_time

    return {
        'success': synced_count > 0,
        'market_status': session_info,
        'data_source': data_source,  # 添加数据源信息
        'total_symbols': len(symbols),
        'synced_count': synced_count,
        'failed_count': failed_count,
        'results': results,
        'errors': errors,
        'execution_time': execution_time
    }


def get_data_freshness_report(symbols: List[str] = None) -> Dict:
    """
    获取数据新鲜度报告

    Args:
        symbols: 要检查的股票列表，None 表示检查所有观察列表股票

    Returns:
        {
            'timestamp': str,
            'symbols': [
                {
                    'symbol': str,
                    'latest_timestamp': str,
                    'age_minutes': float,
                    'is_stale': bool
                }
            ]
        }
    """
    if symbols is None:
        watchlist = get_watchlist_symbols()
        symbols = [item['symbol'] for item in watchlist]

    now = datetime.now(ET)
    report = {
        'timestamp': now.isoformat(),
        'symbols': []
    }

    for symbol in symbols:
        latest_bar = get_latest_bar(symbol)

        if latest_bar:
            latest_time = datetime.fromisoformat(latest_bar.timestamp)
            if latest_time.tzinfo is None:
                latest_time = ET.localize(latest_time)

            age_minutes = (now - latest_time).total_seconds() / 60

            report['symbols'].append({
                'symbol': symbol,
                'latest_timestamp': latest_bar.timestamp,
                'age_minutes': round(age_minutes, 2),
                'is_stale': age_minutes > 15  # 超过15分钟算过时
            })
        else:
            report['symbols'].append({
                'symbol': symbol,
                'latest_timestamp': None,
                'age_minutes': None,
                'is_stale': True
            })

    return report
