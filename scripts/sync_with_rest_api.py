#!/usr/bin/env python3
"""
使用 ThetaData REST API 的增量同步脚本

不依赖 MCP，直接通过 HTTP 请求获取数据。
更稳定、更可靠。

使用方法：
    # 设置 API 密钥（如果还没有在 .env 中）
    export THETADATA_API_KEY="your_api_key"

    # 运行一次同步
    python scripts/sync_with_rest_api.py --once

    # 持续运行（每10分钟）
    python scripts/sync_with_rest_api.py --interval 10
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import time
import logging
import argparse
from datetime import datetime, timedelta

from skills import sync_watchlist_incremental, process_snapshot_and_cache
from skills.thetadata_client import fetch_snapshot_with_rest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_sync_cycle() -> Dict:
    """执行一次完整的同步周期"""

    logger.info("=" * 70)
    logger.info("📊 增量数据同步（REST API）")
    logger.info("=" * 70)

    # 1. 获取同步列表
    sync_info = sync_watchlist_incremental(skip_if_market_closed=True)

    logger.info(f"市场状态: {sync_info['market_status']['session']}")
    logger.info(f"市场开盘: {'✅' if sync_info['market_status']['market_open'] else '❌'}")

    if not sync_info['should_sync']:
        logger.info(f"⏭️  {sync_info['message']}")
        logger.info("=" * 70 + "\n")
        return {
            'synced': False,
            'reason': sync_info['message']
        }

    symbols = sync_info['symbols_to_sync']
    logger.info(f"需要同步: {len(symbols)} 个股票")
    logger.info(f"股票列表: {', '.join(symbols)}\n")

    # 2. 同步每个股票
    stats = {
        'total': len(symbols),
        'success': 0,
        'new_bars': 0,
        'duplicates': 0,
        'failed': 0,
        'errors': []
    }

    logger.info("开始同步...\n")

    for i, symbol in enumerate(symbols, 1):
        try:
            logger.info(f"[{i}/{len(symbols)}] {symbol}...", end=' ')

            # 使用 REST API 获取快照
            snapshot = fetch_snapshot_with_rest(symbol)

            # 处理并缓存
            result = process_snapshot_and_cache(symbol, snapshot)

            if result['success']:
                if result['bars_added'] > 0:
                    logger.info(f"✅ 新增 @ {result['timestamp']}")
                    stats['new_bars'] += 1
                else:
                    logger.info(f"⏭️  已存在（跳过）")
                    stats['duplicates'] += 1
                stats['success'] += 1
            else:
                logger.error(f"❌ {result['error']}")
                stats['failed'] += 1
                stats['errors'].append({
                    'symbol': symbol,
                    'error': result['error']
                })

            # 避免 API 限流
            if i < len(symbols):
                time.sleep(0.2)

        except Exception as e:
            logger.error(f"❌ 异常: {e}")
            stats['failed'] += 1
            stats['errors'].append({
                'symbol': symbol,
                'error': str(e)
            })

    # 3. 输出统计
    logger.info("\n" + "=" * 70)
    logger.info("同步完成")
    logger.info("=" * 70)
    logger.info(f"✅ 成功:   {stats['success']}/{stats['total']}")
    logger.info(f"🆕 新增:   {stats['new_bars']}")
    logger.info(f"⏭️  重复:   {stats['duplicates']}")
    logger.info(f"❌ 失败:   {stats['failed']}")

    if stats['errors']:
        logger.warning("\n错误详情:")
        for err in stats['errors'][:5]:
            logger.warning(f"  {err['symbol']}: {err['error']}")

    logger.info("=" * 70 + "\n")

    return {
        'synced': True,
        'stats': stats
    }


def run_continuous(interval_minutes: int = 10):
    """持续运行同步"""

    logger.info("🚀 增量同步守护进程（REST API）")
    logger.info("=" * 70)
    logger.info(f"⏰ 同步间隔: {interval_minutes} 分钟")
    logger.info(f"🔧 使用: ThetaData REST API")
    logger.info(f"🛑 按 Ctrl+C 停止")
    logger.info("=" * 70 + "\n")

    cycle_count = 0

    try:
        while True:
            cycle_count += 1
            logger.info(f"🔄 周期 #{cycle_count}\n")

            run_sync_cycle()

            # 等待下次同步
            wait_seconds = interval_minutes * 60
            next_sync = datetime.now() + timedelta(seconds=wait_seconds)

            logger.info(f"⏳ 等待 {interval_minutes} 分钟...")
            logger.info(f"⏰ 下次同步: {next_sync.strftime('%Y-%m-%d %H:%M:%S')}\n")

            time.sleep(wait_seconds)

    except KeyboardInterrupt:
        logger.info("\n\n🛑 收到停止信号")
        logger.info(f"✅ 完成 {cycle_count} 个同步周期")
        logger.info("👋 守护进程已停止\n")


def main():
    """主入口"""

    parser = argparse.ArgumentParser(
        description='使用 REST API 的增量数据同步',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单次同步
  python scripts/sync_with_rest_api.py --once

  # 每10分钟同步
  python scripts/sync_with_rest_api.py --interval 10

  # 后台运行
  nohup python scripts/sync_with_rest_api.py --interval 10 > logs/sync_rest.log 2>&1 &

注意:
  需要设置环境变量 THETADATA_API_KEY
        """
    )

    parser.add_argument(
        '--once',
        action='store_true',
        help='只运行一次后退出'
    )

    parser.add_argument(
        '--interval',
        type=int,
        default=10,
        help='持续模式的同步间隔（分钟）'
    )

    args = parser.parse_args()

    # 检查 API 密钥
    import os
    if not os.getenv('THETADATA_API_KEY'):
        logger.error("❌ 未设置 THETADATA_API_KEY 环境变量")
        logger.error("请在 .env 文件中添加: THETADATA_API_KEY=your_key")
        sys.exit(1)

    # 确保 logs 目录存在
    Path('logs').mkdir(exist_ok=True)

    if args.once:
        logger.info("模式: 单次同步\n")
        result = run_sync_cycle()
        if result['synced']:
            logger.info("✅ 同步完成")
        sys.exit(0)
    else:
        logger.info(f"模式: 持续同步（每 {args.interval} 分钟）\n")
        run_continuous(args.interval)


if __name__ == '__main__':
    main()
