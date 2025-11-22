#!/usr/bin/env python3
"""
历史数据回填脚本

从 ThetaData Terminal 获取观察列表股票的历史数据并存储到本地数据库。
支持批量回填多个时间周期的数据。
"""

import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytz
import httpx
from data_lake.market_data_manager import insert_bars, OHLCVBar
from skills.data_sync import get_watchlist_symbols

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 时区
ET = pytz.timezone('US/Eastern')

# ThetaData Terminal Server 配置
THETA_API_BASE_URL = "http://127.0.0.1:25503"


def fetch_historical_ohlc_for_date(
    symbol: str,
    date: str,
    interval: str = "5m",
    start_time: str = "09:30:00",
    end_time: str = "16:00:00"
) -> List[Dict]:
    """
    从 ThetaData Terminal 获取单个交易日的历史 OHLC 数据

    Args:
        symbol: 股票代码
        date: 日期 (YYYY-MM-DD 格式)
        interval: 时间间隔 - '5m', '15m', '1h' 等
        start_time: 交易日开始时间
        end_time: 交易日结束时间

    Returns:
        List of OHLC bar dictionaries
    """
    try:
        # ThetaData v3 API 端点（正确路径）
        url = f"{THETA_API_BASE_URL}/v3/stock/history/ohlc"

        # 构建请求参数
        params = {
            'symbol': symbol,
            'date': date,  # YYYY-MM-DD 格式
            'interval': interval,  # 5m, 15m, 1h 等
            'venue': 'utp_cta',  # 使用 UTP & CTA 15 分钟延迟数据
            'start_time': start_time,
            'end_time': end_time,
            'format': 'json'
        }

        # 发送请求
        with httpx.Client(timeout=60.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()

            result = response.json()

            if 'response' not in result:
                logger.error(f"Invalid API response for {symbol} on {date}: {result}")
                return []

            bars = result['response']
            return bars

    except httpx.TimeoutException as e:
        logger.error(f"Timeout fetching {symbol} on {date}: {e}")
        return []
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP {e.response.status_code} fetching {symbol} on {date}")
        return []
    except Exception as e:
        logger.error(f"Failed to fetch {symbol} on {date}: {e}")
        return []


def parse_and_insert_bars(symbol: str, raw_bars: List[Dict]) -> int:
    """
    解析 ThetaData 返回的数据并插入数据库

    Args:
        symbol: 股票代码
        raw_bars: ThetaData API 返回的原始数据

    Returns:
        插入的 bar 数量
    """
    if not raw_bars:
        return 0

    bars = []
    for raw_bar in raw_bars:
        try:
            # 解析时间戳
            timestamp_str = raw_bar.get('timestamp')
            if not timestamp_str:
                continue

            # 转换为 datetime 对象
            bar_time = datetime.fromisoformat(timestamp_str)
            if bar_time.tzinfo is None:
                bar_time = ET.localize(bar_time)
            else:
                bar_time = bar_time.astimezone(ET)

            # 创建 OHLCVBar 对象
            bar = OHLCVBar(
                symbol=symbol,
                timestamp=bar_time.isoformat(),
                open=float(raw_bar.get('open', 0)),
                high=float(raw_bar.get('high', 0)),
                low=float(raw_bar.get('low', 0)),
                close=float(raw_bar.get('close', 0)),
                volume=int(raw_bar.get('volume', 0)),
                vwap=float(raw_bar.get('vwap')) if raw_bar.get('vwap') else None
            )
            bars.append(bar)

        except Exception as e:
            logger.warning(f"Failed to parse bar for {symbol}: {e}")
            continue

    # 批量插入数据库
    if bars:
        count = insert_bars(symbol, bars)
        return count

    return 0


def generate_trading_dates(start_date: datetime, end_date: datetime) -> List[str]:
    """
    生成交易日期列表（跳过周末）

    Args:
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        List of date strings in YYYY-MM-DD format
    """
    dates = []
    current = start_date

    while current <= end_date:
        # 跳过周末（0=周一, 5=周六, 6=周日）
        if current.weekday() < 5:
            dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    return dates


def backfill_symbol(
    symbol: str,
    days: int = 1095,  # 3年 = 1095天
    interval: str = "5m",
    rate_limit_delay: float = 0.2,
    max_dates_per_run: int = None
) -> Dict:
    """
    回填单个股票的历史数据

    Args:
        symbol: 股票代码
        days: 回填天数
        interval: 时间间隔（5m, 15m, 1h等）
        rate_limit_delay: API 请求间延迟（秒）
        max_dates_per_run: 每次运行最多获取多少天（用于测试和断点续传）

    Returns:
        回填结果字典
    """
    logger.info(f"Starting backfill for {symbol} ({interval}, {days} days)")

    # 计算日期范围
    end_date = datetime.now(ET).replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=days)

    # 生成交易日期列表
    trading_dates = generate_trading_dates(start_date, end_date)

    # 限制获取天数（用于测试或断点续传）
    if max_dates_per_run:
        trading_dates = trading_dates[:max_dates_per_run]

    logger.info(f"  → {symbol}: {len(trading_dates)} trading dates to fetch")

    all_bars = []
    failed_dates = []

    for i, date_str in enumerate(trading_dates):
        try:
            # 获取单个交易日的数据
            bars = fetch_historical_ohlc_for_date(symbol, date_str, interval)

            if bars:
                all_bars.extend(bars)

            # 显示进度
            if (i + 1) % 10 == 0:
                logger.info(f"  → {symbol}: {i + 1}/{len(trading_dates)} dates processed, {len(all_bars)} bars collected")

            # API 限流延迟
            time.sleep(rate_limit_delay)

        except Exception as e:
            logger.error(f"Failed to fetch {symbol} on {date_str}: {e}")
            failed_dates.append(date_str)
            continue

    if not all_bars:
        logger.warning(f"No data retrieved for {symbol}")
        return {
            'symbol': symbol,
            'interval': interval,
            'success': False,
            'bars_fetched': 0,
            'bars_inserted': 0,
            'failed_dates': failed_dates,
            'error': 'No data from API'
        }

    # 解析并插入数据库
    bars_inserted = parse_and_insert_bars(symbol, all_bars)

    logger.info(f"✓ {symbol}: {bars_inserted} bars inserted from {len(trading_dates)} dates ({interval})")

    return {
        'symbol': symbol,
        'interval': interval,
        'success': True,
        'dates_processed': len(trading_dates),
        'dates_failed': len(failed_dates),
        'bars_fetched': len(all_bars),
        'bars_inserted': bars_inserted,
        'date_range': f"{trading_dates[0]} to {trading_dates[-1]}"
    }


def backfill_watchlist(
    days: int = 1095,
    intervals: List[str] = None,
    max_symbols: int = None,
    max_dates_per_run: int = None
) -> Dict:
    """
    回填观察列表中所有股票的历史数据

    Args:
        days: 回填天数（默认3年）
        intervals: 要回填的时间间隔列表
        max_symbols: 最多回填多少个股票（用于测试）
        max_dates_per_run: 每个股票最多获取多少天（用于测试和断点续传）

    Returns:
        总体回填结果
    """
    if intervals is None:
        intervals = ["5m"]  # 只回填5分钟数据，其他间隔可以即时聚合

    start_time = time.time()

    # 获取观察列表
    watchlist = get_watchlist_symbols()
    symbols = [item['symbol'] for item in watchlist]

    if max_symbols:
        symbols = symbols[:max_symbols]

    logger.info(f"=" * 60)
    logger.info(f"BACKFILL TASK STARTED")
    logger.info(f"Symbols: {len(symbols)}")
    logger.info(f"Intervals: {intervals}")
    logger.info(f"Days: {days}")
    if max_dates_per_run:
        logger.info(f"Max dates per run: {max_dates_per_run}")
    logger.info(f"=" * 60)

    results = []
    total_bars = 0
    failed_count = 0

    for symbol in symbols:
        for interval in intervals:
            try:
                result = backfill_symbol(
                    symbol=symbol,
                    days=days,
                    interval=interval,
                    max_dates_per_run=max_dates_per_run
                )
                results.append(result)

                if result['success']:
                    total_bars += result['bars_inserted']
                else:
                    failed_count += 1

            except Exception as e:
                logger.error(f"Failed to backfill {symbol} ({interval}): {e}")
                failed_count += 1
                results.append({
                    'symbol': symbol,
                    'interval': interval,
                    'success': False,
                    'error': str(e)
                })

    execution_time = time.time() - start_time

    logger.info(f"=" * 60)
    logger.info(f"BACKFILL TASK COMPLETED")
    logger.info(f"Execution time: {execution_time:.1f}s ({execution_time/60:.1f} min)")
    logger.info(f"Total bars inserted: {total_bars}")
    logger.info(f"Failed tasks: {failed_count}")
    logger.info(f"=" * 60)

    return {
        'success': failed_count == 0,
        'total_symbols': len(symbols),
        'total_bars_inserted': total_bars,
        'failed_count': failed_count,
        'execution_time': execution_time,
        'results': results
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='回填历史市场数据')
    parser.add_argument('--days', type=int, default=1095, help='回填天数（默认3年=1095天）')
    parser.add_argument('--interval', type=str, default='5m', help='时间间隔（5m, 15m, 1h）')
    parser.add_argument('--max-symbols', type=int, help='最多回填多少个股票（用于测试）')
    parser.add_argument('--max-dates', type=int, help='每个股票最多获取多少天（用于测试和断点续传）')

    args = parser.parse_args()

    # 执行回填
    result = backfill_watchlist(
        days=args.days,
        intervals=[args.interval],
        max_symbols=args.max_symbols,
        max_dates_per_run=args.max_dates
    )

    # 打印结果摘要
    print(f"\n{'=' * 60}")
    if result['success']:
        print(f"✓ 回填成功！")
    else:
        print(f"✗ 回填部分失败")

    print(f"  总股票数: {result['total_symbols']}")
    print(f"  插入数据条数: {result['total_bars_inserted']}")
    print(f"  失败任务数: {result['failed_count']}")
    print(f"  执行时间: {result['execution_time']:.1f}秒 ({result['execution_time']/60:.1f}分钟)")
    print(f"{'=' * 60}\n")

    sys.exit(0 if result['success'] else 1)
