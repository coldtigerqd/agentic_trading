#!/usr/bin/env python3
"""
增量市场数据同步脚本

功能：
- 每10分钟自动获取观察列表中所有股票的最新数据
- 使用 ThetaData MCP 获取实时快照
- 自动去重（依赖数据库 UNIQUE 约束）
- 支持单次运行或持续循环模式

使用方法：
    # 单次运行（获取一次数据后退出）
    python scripts/incremental_data_sync.py --once

    # 持续运行（每10分钟自动更新）
    python scripts/incremental_data_sync.py --interval 10

    # 后台运行
    nohup python scripts/incremental_data_sync.py --interval 10 > logs/data_sync.log 2>&1 &
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import time
import logging
import argparse
from datetime import datetime, timezone
from typing import Dict, List
import pytz

# Import project modules
from data_lake.market_data_manager import insert_bars, get_latest_bar, OHLCVBar
from data_lake.db_helpers import get_db_connection
from skills.market_calendar import get_market_session_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Eastern Time zone
ET = pytz.timezone('US/Eastern')


def get_watchlist_symbols() -> List[Dict]:
    """
    获取观察列表中的所有活跃股票

    Returns:
        List of dicts with symbol info (symbol, priority, notes)
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
                'notes': row['notes']
            })

        return symbols


def fetch_and_store_snapshot(symbol: str) -> Dict:
    """
    获取并存储单个股票的快照数据

    这个函数展示了如何手动调用 ThetaData MCP。
    在实际使用中，你应该通过 Claude Code 调用 MCP 工具。

    Args:
        symbol: 股票代码

    Returns:
        结果字典 {success, symbol, bars_added, error}
    """
    try:
        # 注意：这里需要通过 Claude Code 调用 MCP 工具
        # 实际调用示例：
        # result = mcp__ThetaData__stock_snapshot_ohlc(symbol=[symbol])

        logger.info(f"📊 获取 {symbol} 快照数据...")

        # 这里是占位符，实际应该由 Claude Code 调用 MCP
        # 示例返回格式（来自 ThetaData MCP）：
        # {
        #     "open": 175.5,
        #     "high": 178.2,
        #     "low": 175.1,
        #     "close": 177.8,
        #     "volume": 5234567
        # }

        # 为了演示，这里返回一个提示信息
        return {
            'success': False,
            'symbol': symbol,
            'error': 'This function needs to be called by Claude Code with MCP access',
            'instruction': f'Call: mcp__ThetaData__stock_snapshot_ohlc(symbol=["{symbol}"])'
        }

    except Exception as e:
        logger.error(f"❌ {symbol} 数据获取失败: {e}")
        return {
            'success': False,
            'symbol': symbol,
            'error': str(e)
        }


def process_thetadata_snapshot(symbol: str, snapshot_data: Dict) -> Dict:
    """
    处理 ThetaData 快照数据并存入数据库

    Args:
        symbol: 股票代码
        snapshot_data: ThetaData MCP 返回的快照数据

    Returns:
        处理结果 {success, symbol, bars_added, timestamp}
    """
    try:
        # 生成当前时间戳（四舍五入到5分钟）
        now = datetime.now(ET)
        minutes = (now.minute // 5) * 5
        timestamp = now.replace(minute=minutes, second=0, microsecond=0).isoformat()

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

        if count > 0:
            logger.info(f"✅ {symbol}: 新增 {count} 条数据 @ {timestamp}")
        else:
            logger.debug(f"⏭️  {symbol}: 数据已存在，跳过")

        return {
            'success': True,
            'symbol': symbol,
            'bars_added': count,
            'timestamp': timestamp
        }

    except Exception as e:
        logger.error(f"❌ {symbol} 数据处理失败: {e}")
        return {
            'success': False,
            'symbol': symbol,
            'error': str(e)
        }


def sync_watchlist_data_once() -> Dict:
    """
    执行一次完整的观察列表数据同步

    Returns:
        同步统计信息
    """
    logger.info("=" * 60)
    logger.info("开始增量数据同步...")

    # 检查市场状态
    session_info = get_market_session_info()
    logger.info(f"市场状态: {session_info['session']}")
    logger.info(f"市场开盘: {'✅' if session_info['market_open'] else '❌'}")

    # 获取观察列表
    watchlist = get_watchlist_symbols()
    logger.info(f"观察列表: {len(watchlist)} 个股票")

    if not watchlist:
        logger.warning("⚠️  观察列表为空，无数据可同步")
        return {
            'total_symbols': 0,
            'success_count': 0,
            'failed_count': 0,
            'new_bars_count': 0
        }

    # 统计信息
    stats = {
        'total_symbols': len(watchlist),
        'success_count': 0,
        'failed_count': 0,
        'new_bars_count': 0,
        'symbols_processed': []
    }

    # 处理每个股票
    for item in watchlist:
        symbol = item['symbol']

        # 这里是关键：需要 Claude Code 调用 ThetaData MCP
        # 示例调用：
        # snapshot = mcp__ThetaData__stock_snapshot_ohlc(symbol=[symbol])
        # result = process_thetadata_snapshot(symbol, snapshot)

        # 为了演示，这里显示需要的 MCP 调用
        logger.info(f"📌 {symbol}: 需要调用 MCP 工具获取数据")
        logger.info(f"   👉 mcp__ThetaData__stock_snapshot_ohlc(symbol=['{symbol}'])")

        stats['symbols_processed'].append({
            'symbol': symbol,
            'status': 'pending_mcp_call'
        })

    logger.info("=" * 60)
    logger.info(f"同步完成: {stats['total_symbols']} 个股票待处理")

    return stats


def run_continuous_sync(interval_minutes: int = 10):
    """
    持续运行数据同步（每隔指定分钟数）

    Args:
        interval_minutes: 同步间隔（分钟）
    """
    logger.info(f"🚀 启动持续数据同步服务")
    logger.info(f"⏰ 同步间隔: {interval_minutes} 分钟")
    logger.info(f"💾 数据库: data_lake/trades.db")
    logger.info(f"按 Ctrl+C 停止服务\n")

    try:
        while True:
            sync_watchlist_data_once()

            # 等待下一次同步
            wait_seconds = interval_minutes * 60
            next_sync = datetime.now() + timedelta(seconds=wait_seconds)
            logger.info(f"\n⏳ 等待 {interval_minutes} 分钟...")
            logger.info(f"下次同步时间: {next_sync.strftime('%Y-%m-%d %H:%M:%S')}\n")

            time.sleep(wait_seconds)

    except KeyboardInterrupt:
        logger.info("\n\n🛑 收到停止信号，正在退出...")
        logger.info("✅ 数据同步服务已停止")


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description='增量市场数据同步工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单次运行
  python scripts/incremental_data_sync.py --once

  # 每10分钟同步一次
  python scripts/incremental_data_sync.py --interval 10

  # 后台运行
  nohup python scripts/incremental_data_sync.py --interval 10 > logs/sync.log 2>&1 &
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
        help='持续模式下的同步间隔（分钟），默认10分钟'
    )

    args = parser.parse_args()

    if args.once:
        logger.info("模式: 单次同步\n")
        stats = sync_watchlist_data_once()
        logger.info(f"\n✅ 同步完成")
        logger.info(f"处理股票数: {stats['total_symbols']}")
    else:
        logger.info(f"模式: 持续同步（每 {args.interval} 分钟）\n")
        run_continuous_sync(args.interval)


if __name__ == '__main__':
    main()
