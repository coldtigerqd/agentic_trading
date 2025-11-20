#!/usr/bin/env python3
"""
增量数据同步演示脚本

展示如何使用 ThetaData MCP 和 skills 进行增量数据同步。
此脚本可以直接运行，或作为 Commander 工作流的参考。

使用方法：
    python scripts/demo_incremental_sync.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from skills import (
    sync_watchlist_incremental,
    process_snapshot_and_cache,
    get_data_freshness_report
)


def main():
    """演示增量同步工作流"""

    print("=" * 70)
    print("📊 增量数据同步演示")
    print("=" * 70)

    # 步骤 1: 检查哪些股票需要同步
    print("\n步骤 1: 检查同步需求...")
    sync_info = sync_watchlist_incremental(skip_if_market_closed=True)

    print(f"\n市场状态:")
    print(f"  会话: {sync_info['market_status']['session']}")
    print(f"  开盘: {'是' if sync_info['market_status']['market_open'] else '否'}")

    if not sync_info['should_sync']:
        print(f"\n⏭️  跳过同步: {sync_info['message']}")
        return

    symbols = sync_info['symbols_to_sync']
    print(f"\n需要同步的股票: {len(symbols)} 个")
    print(f"股票列表: {', '.join(symbols[:5])}{'...' if len(symbols) > 5 else ''}")

    # 步骤 2: 获取数据新鲜度报告
    print("\n步骤 2: 检查数据新鲜度...")
    freshness = get_data_freshness_report(symbols[:5])  # 只检查前5个

    print("\n数据新鲜度:")
    for item in freshness['symbols']:
        age = item['age_minutes']
        status = "❌ 过时" if item['is_stale'] else "✅ 新鲜"
        age_str = f"{age:.1f}分钟前" if age else "无数据"
        print(f"  {item['symbol']:6s}: {status} ({age_str})")

    # 步骤 3: 演示如何同步（需要 Claude Code 调用 MCP）
    print("\n步骤 3: 执行同步（需要 Claude Code）...")
    print("\n⚠️  此脚本无法直接调用 MCP 工具（需要 Claude Code 环境）")
    print("\n在 Claude Code 环境中，应该这样调用:\n")

    for symbol in symbols[:3]:  # 演示前3个
        print(f"# 同步 {symbol}:")
        print(f"snapshot = mcp__ThetaData__stock_snapshot_ohlc(symbol=['{symbol}'])")
        print(f"result = process_snapshot_and_cache('{symbol}', snapshot)")
        print(f"print(f'✅ {{result[\"symbol\"]}}: {{result[\"bars_added\"]}} bars added')")
        print()

    print("\n" + "=" * 70)
    print("📚 集成说明:")
    print("=" * 70)
    print("""
1. 在 Commander 工作流中调用:
   ───────────────────────────────────
   from skills import sync_watchlist_incremental, process_snapshot_and_cache

   # 获取需要同步的股票
   sync_info = sync_watchlist_incremental()

   # 对每个股票调用 MCP
   for symbol in sync_info['symbols_to_sync']:
       # Claude Code 调用 ThetaData MCP
       snapshot = mcp__ThetaData__stock_snapshot_ohlc(symbol=[symbol])

       # 处理并缓存
       result = process_snapshot_and_cache(symbol, snapshot)

       if result['success'] and result['bars_added'] > 0:
           print(f"✅ {symbol}: 新增数据")


2. 使用定时任务:
   ───────────────────────────────────
   # 方法 A: 使用 cron（每10分钟）
   */10 * * * * cd /path/to/agentic_trading && python runtime/data_sync_daemon.py --once

   # 方法 B: 后台守护进程
   nohup python runtime/data_sync_daemon.py --interval 10 > logs/data_sync.log 2>&1 &


3. 增量更新原理:
   ───────────────────────────────────
   - 数据库有 UNIQUE(symbol, interval, timestamp) 约束
   - 重复的时间戳会被自动忽略（不会报错）
   - process_snapshot_and_cache() 返回 bars_added=0 表示数据已存在
   - 因此每次调用都是安全的，自动实现增量更新


4. 数据新鲜度验证:
   ───────────────────────────────────
   from skills import get_data_freshness_report

   report = get_data_freshness_report(['AAPL', 'NVDA', 'SPY'])

   for item in report['symbols']:
       if item['is_stale']:
           print(f"⚠️  {item['symbol']} 数据过时: {item['age_minutes']}分钟前")
    """)

    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
