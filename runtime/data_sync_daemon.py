#!/usr/bin/env python3
"""
数据同步守护进程

每10分钟自动同步观察列表数据到本地数据库。

⚠️  数据延迟说明：
    本系统使用 ThetaData v3 免费计划（venue='utp_cta'），数据相对实盘有 15 分钟延迟。
    这是正常现象，不影响历史数据分析和策略回测。

特性：
- ✅ 增量更新：只获取新数据，自动去重
- ✅ 市场感知：只在交易时段主动同步
- ✅ 错误重试：网络失败自动重试
- ✅ 完整日志：记录所有同步活动
- ✅ 时区感知：所有时间使用美东时区 (ET/America/New_York)

使用方法：
    # 直接运行（前台）
    python runtime/data_sync_daemon.py

    # 后台运行
    nohup python runtime/data_sync_daemon.py > logs/data_sync.log 2>&1 &

    # 使用 systemd（推荐生产环境）
    sudo systemctl start agentic-data-sync

    # 使用 cron（每10分钟）
    */10 * * * * cd /path/to/agentic_trading && python runtime/data_sync_daemon.py --once
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import time
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List

# Import skills
from skills import (
    sync_watchlist_incremental,
    process_snapshot_and_cache,
    get_data_freshness_report
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/data_sync.log') if Path('logs').exists() else logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_sync_cycle() -> Dict:
    """
    执行一次完整的数据同步周期

    Returns:
        同步统计信息
    """
    logger.info("=" * 70)
    logger.info("📊 Starting Data Sync Cycle")
    logger.info("=" * 70)

    cycle_start = time.time()

    # 1. 调用增量同步技能（会自动检查市场状态）
    sync_result = sync_watchlist_incremental(skip_if_market_closed=True)

    # 2. 解析市场状态
    market_status = sync_result.get('market_status', {})
    logger.info(f"🕒 Timestamp: {market_status.get('timestamp', 'N/A')}")
    logger.info(f"📈 Market Status: {market_status.get('session', 'UNKNOWN')}")
    logger.info(f"🔓 Market Open: {'✅ YES' if market_status.get('market_open') else '❌ NO'}")

    if market_status.get('next_market_open'):
        logger.info(f"⏰ Next Open: {market_status['next_market_open']}")

    logger.info(f"⏱️  Data Delay: 📍 15 minutes (ThetaData v3 免费计划)")

    # 3. 检查是否成功同步
    if not sync_result.get('success'):
        # 市场关闭或其他错误
        errors = sync_result.get('errors', [])
        reason = errors[0] if errors else "Unknown reason"
        logger.info(f"⏭️  Skip Reason: {reason}")
        logger.info("=" * 70 + "\n")
        return {
            'synced': False,
            'reason': reason,
            'market_status': market_status,
            'stats': {
                'total': sync_result.get('total_symbols', 0),
                'success': 0,
                'failed': 0
            }
        }

    # 4. 输出同步统计信息
    total_symbols = sync_result.get('total_symbols', 0)
    synced_count = sync_result.get('synced_count', 0)
    failed_count = sync_result.get('failed_count', 0)
    execution_time = sync_result.get('execution_time', 0)

    logger.info(f"\n📋 Total Symbols: {total_symbols}")
    logger.info(f"✅ Synced: {synced_count}")
    logger.info(f"❌ Failed: {failed_count}")
    logger.info(f"⏱️  Execution Time: {execution_time:.2f}s")

    # 5. 显示详细结果（前10个）
    results = sync_result.get('results', [])
    if results:
        logger.info("\n" + "─" * 70)
        logger.info("Sample Results (first 10):")
        logger.info("─" * 70)
        for i, result in enumerate(results[:10], 1):
            symbol = result.get('symbol', 'UNKNOWN')
            status = result.get('status', 'unknown')

            if status == 'synced':
                bars_added = result.get('bars_added', 0)
                timestamp = result.get('timestamp', 'N/A')
                if bars_added > 0:
                    logger.info(f"  [{i}] ✅ {symbol}: New bar @ {timestamp}")
                else:
                    logger.info(f"  [{i}] ⏭️  {symbol}: Duplicate (already in DB)")
            else:
                error = result.get('error', 'Unknown error')
                logger.info(f"  [{i}] ❌ {symbol}: {error}")

    # 6. 显示错误（如果有）
    errors = sync_result.get('errors', [])
    if errors:
        logger.warning("\n⚠️  Errors:")
        for err in errors[:5]:  # 只显示前5个错误
            logger.warning(f"   - {err}")

    logger.info("\n" + "=" * 70)
    logger.info("📊 Sync Cycle Complete")
    logger.info("=" * 70 + "\n")

    return {
        'synced': True,
        'stats': {
            'total': total_symbols,
            'success': synced_count,
            'failed': failed_count,
            'execution_time': execution_time
        },
        'market_status': market_status
    }


def run_continuous(interval_minutes: int = 10):
    """
    持续运行同步守护进程

    Args:
        interval_minutes: 同步间隔（分钟）
    """
    logger.info("🚀 Agentic AlphaHive - Data Sync Daemon")
    logger.info("=" * 70)
    logger.info(f"⏰ Sync Interval: {interval_minutes} minutes")
    logger.info(f"💾 Database: data_lake/trades.db")
    logger.info(f"🛑 Press Ctrl+C to stop")
    logger.info("=" * 70 + "\n")

    cycle_count = 0

    try:
        while True:
            cycle_count += 1
            logger.info(f"🔄 Cycle #{cycle_count}")

            # 执行同步
            result = run_sync_cycle()

            # 计算下次同步时间
            wait_seconds = interval_minutes * 60
            next_sync = datetime.now() + timedelta(seconds=wait_seconds)

            logger.info(f"⏳ Waiting {interval_minutes} minutes...")
            logger.info(f"⏰ Next sync: {next_sync.strftime('%Y-%m-%d %H:%M:%S')}\n")

            time.sleep(wait_seconds)

    except KeyboardInterrupt:
        logger.info("\n\n🛑 Shutdown signal received")
        logger.info(f"✅ Completed {cycle_count} sync cycles")
        logger.info("👋 Data Sync Daemon stopped\n")


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description='增量市场数据同步守护进程',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行一次后退出
  python runtime/data_sync_daemon.py --once

  # 持续运行（每10分钟同步）
  python runtime/data_sync_daemon.py --interval 10

  # 后台运行
  nohup python runtime/data_sync_daemon.py --interval 10 > logs/data_sync.log 2>&1 &

  # 使用 cron（每10分钟）
  */10 * * * * cd /path/to/agentic_trading && python runtime/data_sync_daemon.py --once

注意：
  1. 数据来源：ThetaData v3 API (venue='utp_cta')
  2. 数据延迟：相对实盘有 15 分钟延迟（免费计划限制）
  3. 时区处理：所有时间戳使用美东时区 (ET/America/New_York)
  4. 市场感知：只在交易时段主动同步数据
        """
    )

    parser.add_argument(
        '--once',
        action='store_true',
        help='只运行一次同步后退出'
    )

    parser.add_argument(
        '--interval',
        type=int,
        default=10,
        help='持续模式的同步间隔（分钟），默认10分钟'
    )

    args = parser.parse_args()

    # 确保 logs 目录存在
    Path('logs').mkdir(exist_ok=True)

    if args.once:
        logger.info("Mode: Single Sync\n")
        result = run_sync_cycle()
        if result['synced']:
            logger.info(f"✅ Sync completed: {result['stats']['success']}/{result['stats']['total']} symbols")
            sys.exit(0)
        else:
            logger.info(f"⏭️  Sync skipped: {result['reason']}")
            sys.exit(0)
    else:
        logger.info(f"Mode: Continuous (every {args.interval} minutes)\n")
        run_continuous(args.interval)


if __name__ == '__main__':
    main()
