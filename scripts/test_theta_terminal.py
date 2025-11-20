#!/usr/bin/env python3
"""
测试 Theta Terminal 连接

验证 Theta Terminal 是否正常运行并可以获取数据。
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from skills.thetadata_client import ThetaDataClient


def main():
    print("=" * 70)
    print("🔍 Theta Terminal 连接测试")
    print("=" * 70)
    print()

    # 1. 测试连接
    print("步骤 1: 连接到 Theta Terminal...")
    try:
        client = ThetaDataClient(host="localhost", port=25503)
        print("✅ 客户端初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return

    # 2. 测试 OHLC 快照
    print("\n步骤 2: 获取 SPY OHLC 快照...")
    try:
        ohlc = client.get_ohlc_snapshot("SPY")
        print(f"✅ OHLC 数据:")
        print(f"   Open:   ${ohlc['open']:.2f}")
        print(f"   High:   ${ohlc['high']:.2f}")
        print(f"   Low:    ${ohlc['low']:.2f}")
        print(f"   Close:  ${ohlc['close']:.2f}")
        print(f"   Volume: {ohlc['volume']:,}")
    except Exception as e:
        print(f"❌ 获取失败: {e}")
        print("\n请检查:")
        print("  1. Theta Terminal 是否正在运行")
        print("  2. 启动命令: java -jar ThetaTerminalv3.jar")
        print("  3. Terminal 端口是否为 25503")
        return

    # 3. 测试报价快照
    print("\n步骤 3: 获取 AAPL 报价快照...")
    try:
        quote = client.get_quote_snapshot("AAPL")
        print(f"✅ 报价数据:")
        print(f"   Bid:    ${quote['bid']:.2f} x {quote['bid_size']}")
        print(f"   Ask:    ${quote['ask']:.2f} x {quote['ask_size']}")
        print(f"   Mid:    ${quote['mid']:.2f}")
        print(f"   Volume: {quote['volume']:,}")
    except Exception as e:
        print(f"❌ 获取失败: {e}")
        return

    # 4. 测试多个股票
    print("\n步骤 4: 批量获取数据...")
    symbols = ['SPY', 'QQQ', 'AAPL', 'NVDA']

    for symbol in symbols:
        try:
            ohlc = client.get_ohlc_snapshot(symbol)
            print(f"✅ {symbol:6s}: ${ohlc['close']:8.2f}  (Vol: {ohlc['volume']:,})")
        except Exception as e:
            print(f"❌ {symbol:6s}: {e}")

    print("\n" + "=" * 70)
    print("🎉 测试完成！")
    print("=" * 70)
    print("\n✅ Theta Terminal 连接正常，可以开始同步数据")
    print("\n下一步:")
    print("  运行增量同步: python scripts/sync_with_rest_api.py --once")


if __name__ == '__main__':
    main()
