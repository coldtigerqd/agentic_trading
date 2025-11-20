"""
ThetaData Terminal 客户端

连接到本地运行的 Theta Terminal（localhost:25503）
不依赖 MCP，直接使用 HTTP 请求。

前置条件：
    Theta Terminal 必须正在运行
    启动命令: java -jar ThetaTerminalv3.jar
"""

import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
import pytz
import httpx
import csv
import io

logger = logging.getLogger(__name__)
ET = pytz.timezone('US/Eastern')


class ThetaDataClient:
    """ThetaData Terminal 客户端（本地服务器）"""

    def __init__(self, host: str = "localhost", port: int = 25503):
        """
        初始化客户端

        Args:
            host: Theta Terminal 主机地址
            port: Theta Terminal 端口
        """
        self.base_url = f"http://{host}:{port}/v3"

    def _make_request(self, endpoint: str, params: Dict = None) -> List[List[str]]:
        """
        发起 API 请求（CSV 格式）

        使用 httpx.stream() 进行流式读取，这是 ThetaData 推荐的方式。

        Args:
            endpoint: API 端点
            params: 请求参数

        Returns:
            CSV 数据（列表的列表）
        """
        url = f"{self.base_url}/{endpoint}"
        params = params or {}

        try:
            # 使用 httpx.stream() 进行流式读取（ThetaData 推荐方式）
            with httpx.stream("GET", url, params=params, timeout=60) as response:
                response.raise_for_status()

                rows = []
                for line in response.iter_lines():
                    if line:
                        for row in csv.reader(io.StringIO(line)):
                            rows.append(row)

                return rows

        except httpx.TimeoutException:
            logger.error(f"Request timeout for {endpoint}")
            raise
        except httpx.ConnectError:
            logger.error("Cannot connect to Theta Terminal. Is it running?")
            logger.error("Start it with: java -jar ThetaTerminalv3.jar")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for {endpoint}: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request failed for {endpoint}: {e}")
            raise

    def get_quote_snapshot(self, symbol: str, venue: str = "UTP_CTA") -> Dict:
        """
        获取股票实时报价快照

        Args:
            symbol: 股票代码
            venue: 数据源 (默认 "UTP_CTA" = 15分钟延迟数据，可用于免费订阅)

        Returns:
            {
                'timestamp': str,
                'symbol': str,
                'bid': float,
                'bid_size': int,
                'bid_exchange': str,
                'bid_condition': str,
                'ask': float,
                'ask_size': int,
                'ask_exchange': str,
                'ask_condition': str,
                'mid': float (calculated)
            }
        """
        endpoint = "stock/snapshot/quote"
        params = {'symbol': symbol, 'venue': venue}

        rows = self._make_request(endpoint, params)

        # 跳过表头，解析数据
        if len(rows) < 2:
            raise Exception(f"No data returned for {symbol}")

        # CSV 格式（根据 ThetaData API 文档）：
        # timestamp, symbol, bid_size, bid_exchange, bid, bid_condition,
        # ask_size, ask_exchange, ask, ask_condition
        data_row = rows[1]  # 第一行是表头，第二行是数据

        bid = float(data_row[4]) if len(data_row) > 4 and data_row[4] else 0.0
        ask = float(data_row[8]) if len(data_row) > 8 and data_row[8] else 0.0
        mid = (bid + ask) / 2 if bid > 0 and ask > 0 else 0.0

        return {
            'timestamp': data_row[0] if len(data_row) > 0 else None,
            'symbol': data_row[1] if len(data_row) > 1 else symbol,
            'bid_size': int(data_row[2]) if len(data_row) > 2 and data_row[2] else 0,
            'bid_exchange': data_row[3] if len(data_row) > 3 else '',
            'bid': bid,
            'bid_condition': data_row[5] if len(data_row) > 5 else '',
            'ask_size': int(data_row[6]) if len(data_row) > 6 and data_row[6] else 0,
            'ask_exchange': data_row[7] if len(data_row) > 7 else '',
            'ask': ask,
            'ask_condition': data_row[9] if len(data_row) > 9 else '',
            'mid': mid
        }

    def get_ohlc_snapshot(self, symbol: str, venue: str = "UTP_CTA") -> Dict:
        """
        获取当日 OHLC 快照

        Args:
            symbol: 股票代码
            venue: 数据源 (默认 "UTP_CTA" = 15分钟延迟数据，可用于免费订阅)

        Returns:
            {
                'timestamp': str,
                'symbol': str,
                'open': float,
                'high': float,
                'low': float,
                'close': float,
                'volume': int,
                'count': int
            }
        """
        endpoint = "stock/snapshot/ohlc"
        params = {'symbol': symbol, 'venue': venue}

        rows = self._make_request(endpoint, params)

        # 跳过表头，解析数据
        if len(rows) < 2:
            raise Exception(f"No data returned for {symbol}")

        # CSV 格式（根据 ThetaData API 文档）：
        # timestamp, symbol, open, high, low, close, volume, count
        data_row = rows[1]

        return {
            'timestamp': data_row[0] if len(data_row) > 0 else None,
            'symbol': data_row[1] if len(data_row) > 1 else symbol,
            'open': float(data_row[2]) if len(data_row) > 2 and data_row[2] else 0.0,
            'high': float(data_row[3]) if len(data_row) > 3 and data_row[3] else 0.0,
            'low': float(data_row[4]) if len(data_row) > 4 and data_row[4] else 0.0,
            'close': float(data_row[5]) if len(data_row) > 5 and data_row[5] else 0.0,
            'volume': int(data_row[6]) if len(data_row) > 6 and data_row[6] else 0,
            'count': int(data_row[7]) if len(data_row) > 7 and data_row[7] else 0
        }

    def get_historical_ohlc(
        self,
        symbol: str,
        interval: str = '5min',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """
        获取历史 OHLC 数据

        Args:
            symbol: 股票代码
            interval: 时间周期 ('1min', '5min', '15min', '1h', 'daily')
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            List of OHLC bars
        """
        # 将间隔转换为 ThetaData 格式
        interval_map = {
            '1min': '1',
            '5min': '5',
            '15min': '15',
            '1h': '60',
            'daily': 'D'
        }

        theta_interval = interval_map.get(interval, '5')

        endpoint = "hist/stock/ohlc"
        params = {
            'root': symbol,
            'ivl': theta_interval
        }

        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        data = self._make_request(endpoint, params)

        # 解析响应（格式取决于实际 API）
        bars = []
        if 'response' in data and data['response'] == 'Success':
            # 假设数据在 'data' 字段中
            raw_bars = data.get('data', [])
            for bar in raw_bars:
                bars.append({
                    'timestamp': bar.get('ms_of_day'),
                    'open': bar.get('open'),
                    'high': bar.get('high'),
                    'low': bar.get('low'),
                    'close': bar.get('close'),
                    'volume': bar.get('volume')
                })

        return bars


def fetch_snapshot_with_rest(symbol: str) -> Dict:
    """
    使用 REST API 获取股票快照（便捷函数）

    Args:
        symbol: 股票代码

    Returns:
        OHLC 快照数据
    """
    client = ThetaDataClient()

    try:
        # 首先尝试获取 OHLC 快照
        ohlc = client.get_ohlc_snapshot(symbol)

        # 如果 OHLC 数据不完整，尝试从报价推算
        if ohlc['close'] == 0:
            quote = client.get_quote_snapshot(symbol)
            # 使用 mid price 作为近似值
            last_price = quote['mid']

            ohlc = {
                'timestamp': quote['timestamp'],
                'symbol': quote['symbol'],
                'open': last_price,
                'high': last_price,
                'low': last_price,
                'close': last_price,
                'volume': 0,  # Quote 快照不包含 volume
                'count': 0
            }

        logger.info(f"✓ Fetched {symbol}: ${ohlc['close']:.2f}")
        return ohlc

    except Exception as e:
        logger.error(f"✗ Failed to fetch {symbol}: {e}")
        raise


def batch_fetch_snapshots(symbols: List[str], delay: float = 0.2) -> Dict[str, Dict]:
    """
    批量获取快照数据

    Args:
        symbols: 股票代码列表
        delay: 请求间延迟（秒），避免 API 限流

    Returns:
        {symbol: snapshot_data}
    """
    results = {}

    for i, symbol in enumerate(symbols, 1):
        try:
            logger.info(f"[{i}/{len(symbols)}] Fetching {symbol}...")
            snapshot = fetch_snapshot_with_rest(symbol)
            results[symbol] = snapshot

            # 避免 API 限流
            if i < len(symbols):
                time.sleep(delay)

        except Exception as e:
            logger.error(f"Failed to fetch {symbol}: {e}")
            results[symbol] = None

    return results
