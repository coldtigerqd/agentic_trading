#!/usr/bin/env python3
"""
一键增量同步脚本

在当前环境（Claude Code）中运行一次完整的增量数据同步。
这个脚本会：
1. 检查市场状态
2. 获取观察列表
3. 调用 ThetaData MCP 获取数据
4. 增量保存到数据库

使用方法：
    python scripts/run_sync_once.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from skills import sync_watchlist_incremental, process_snapshot_and_cache


def main():
    print("\n" + "=" * 70)
    print("🚀 一键增量数据同步")
    print("=" * 70 + "\n")

    # 步骤 1: 检查同步需求
    print("步骤 1: 检查市场状态和观察列表...")
    sync_info = sync_watchlist_incremental(skip_if_market_closed=False)

    print(f"\n市场状态:")
    print(f"  会话: {sync_info['market_status']['session']}")
    print(f"  开盘: {'是' if sync_info['market_status']['market_open'] else '否'}")

    if not sync_info['should_sync']:
        print(f"\n⏭️  {sync_info['message']}")
        print("\n" + "=" * 70 + "\n")
        return

    symbols = sync_info['symbols_to_sync']
    print(f"\n需要同步: {len(symbols)} 个股票")
    print(f"股票列表: {', '.join(symbols)}")

    # 步骤 2: 实际同步（需要 Claude Code 调用 MCP）
    print("\n" + "-" * 70)
    print("步骤 2: 开始增量同步...\n")

    print("⚠️  此脚本需要 Claude Code 环境才能调用 ThetaData MCP")
    print("\n请通过以下方式运行：\n")

    # 生成实际可执行的代码
    print("```python")
    print("# === 在 Claude Code 会话中执行以下代码 ===")
    print()
    print("from skills import sync_watchlist_incremental, process_snapshot_and_cache")
    print()
    print("# 获取同步列表")
    print("sync_info = sync_watchlist_incremental(skip_if_market_closed=False)")
    print()
    print("if sync_info['should_sync']:")
    print("    symbols = sync_info['symbols_to_sync']")
    print("    print(f'📊 开始同步 {len(symbols)} 个股票...')")
    print()
    print("    stats = {'new_bars': 0, 'duplicates': 0, 'errors': 0}")
    print()
    print("    for i, symbol in enumerate(symbols, 1):")
    print("        try:")
    print("            print(f'[{i}/{len(symbols)}] {symbol}...', end=' ')")
    print()
    print("            # 调用 ThetaData MCP 获取快照")
    print("            snapshot = mcp__ThetaData__stock_snapshot_ohlc(symbol=[symbol])")
    print()
    print("            # 处理并缓存")
    print("            result = process_snapshot_and_cache(symbol, snapshot)")
    print()
    print("            if result['success']:")
    print("                if result['bars_added'] > 0:")
    print("                    print(f\"✅ 新增\")")
    print("                    stats['new_bars'] += 1")
    print("                else:")
    print("                    print(f\"⏭️  已存在\")")
    print("                    stats['duplicates'] += 1")
    print("            else:")
    print("                print(f\"❌ {result['error']}\")")
    print("                stats['errors'] += 1")
    print()
    print("        except Exception as e:")
    print("            print(f'❌ 异常: {e}')")
    print("            stats['errors'] += 1")
    print()
    print("    print(f\"\\n✅ 同步完成:\")")
    print("    print(f\"  新增: {stats['new_bars']}\")")
    print("    print(f\"  重复: {stats['duplicates']}\")")
    print("    print(f\"  失败: {stats['errors']}\")")
    print("else:")
    print("    print(f\"⏭️  {sync_info['message']}\")")
    print("```")
    print()

    print("\n" + "=" * 70)
    print("💡 提示")
    print("=" * 70)
    print("""
如果你想设置自动化同步（每10分钟），可以使用：

1. Cron 任务（推荐生产环境）：
   crontab -e
   # 添加：
   */10 * * * * cd /home/adt/project/agentic_trading && python runtime/data_sync_daemon.py --once

2. 后台守护进程：
   nohup python runtime/data_sync_daemon.py --interval 10 > logs/data_sync.log 2>&1 &

3. Commander 集成：
   在 Commander 工作流中添加上述代码即可自动同步

详细文档：docs/QUICK_START_INCREMENTAL_SYNC.md
    """)


if __name__ == '__main__':
    main()
