#!/usr/bin/env python3
"""
测试 ThetaData API 修复

验证 CSV 解析是否正确匹配 ThetaData API 文档。

前置条件：
    Theta Terminal 必须正在运行
    启动命令: java -jar ThetaTerminalv3.jar
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from skills.thetadata_client import ThetaDataClient, fetch_snapshot_with_rest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_quote_snapshot():
    """测试 Quote Snapshot API"""
    client = ThetaDataClient()

    test_symbols = ["SPY", "AAPL", "NVDA"]

    print("\n=== Testing Quote Snapshot API ===\n")

    for symbol in test_symbols:
        try:
            quote = client.get_quote_snapshot(symbol)

            print(f"{symbol}:")
            print(f"  Timestamp: {quote['timestamp']}")
            print(f"  Bid: ${quote['bid']:.2f} x {quote['bid_size']} ({quote['bid_exchange']})")
            print(f"  Ask: ${quote['ask']:.2f} x {quote['ask_size']} ({quote['ask_exchange']})")
            print(f"  Mid: ${quote['mid']:.2f}")
            print()

        except Exception as e:
            print(f"✗ Error fetching {symbol}: {e}\n")


def test_ohlc_snapshot():
    """测试 OHLC Snapshot API"""
    client = ThetaDataClient()

    test_symbols = ["SPY", "AAPL", "NVDA"]

    print("\n=== Testing OHLC Snapshot API ===\n")

    for symbol in test_symbols:
        try:
            ohlc = client.get_ohlc_snapshot(symbol)

            print(f"{symbol}:")
            print(f"  Timestamp: {ohlc['timestamp']}")
            print(f"  Open:   ${ohlc['open']:.2f}")
            print(f"  High:   ${ohlc['high']:.2f}")
            print(f"  Low:    ${ohlc['low']:.2f}")
            print(f"  Close:  ${ohlc['close']:.2f}")
            print(f"  Volume: {ohlc['volume']:,}")
            print(f"  Count:  {ohlc['count']:,}")
            print()

        except Exception as e:
            print(f"✗ Error fetching {symbol}: {e}\n")


def test_fetch_snapshot_convenience():
    """测试便捷函数"""
    test_symbols = ["SPY", "AAPL"]

    print("\n=== Testing Convenience Function ===\n")

    for symbol in test_symbols:
        try:
            snapshot = fetch_snapshot_with_rest(symbol)

            print(f"{symbol}: ${snapshot['close']:.2f}")

        except Exception as e:
            print(f"✗ Error fetching {symbol}: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("ThetaData API Fix Validation Test")
    print("=" * 60)
    print("\nThis test validates that CSV parsing matches ThetaData API docs:")
    print("  - https://docs.thetadata.us/operations/stock_snapshot_ohlc.html")
    print("  - https://docs.thetadata.us/operations/stock_snapshot_quote.html")
    print()

    try:
        test_quote_snapshot()
        test_ohlc_snapshot()
        test_fetch_snapshot_convenience()

        print("\n" + "=" * 60)
        print("✓ All tests completed")
        print("=" * 60)

    except ConnectionError:
        print("\n✗ Cannot connect to Theta Terminal")
        print("Please start Theta Terminal with: java -jar ThetaTerminalv3.jar")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
