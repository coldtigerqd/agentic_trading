#!/usr/bin/env python3
"""快速检查回填状态和数据库统计"""

import sqlite3
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "data_lake" / "trades.db"

def check_status():
    """检查回填状态"""
    if not DB_PATH.exists():
        print("⚠ 数据库文件不存在")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 获取所有股票的数据统计
    cursor.execute("""
        SELECT
            symbol,
            COUNT(*) as total_bars,
            MIN(timestamp) as earliest,
            MAX(timestamp) as latest
        FROM market_data_bars
        GROUP BY symbol
        ORDER BY symbol
    """)

    results = cursor.fetchall()

    print("=" * 70)
    print("历史数据回填状态")
    print("=" * 70)
    print()

    if not results:
        print("⚠ 数据库中还没有数据")
    else:
        print(f"{'股票':<10} {'数据条数':>10} {'最早日期':<25} {'最新日期':<25}")
        print("-" * 70)

        total_bars = 0
        for row in results:
            print(f"{row['symbol']:<10} {row['total_bars']:>10,} "
                  f"{row['earliest']:<25} {row['latest']:<25}")
            total_bars += row['total_bars']

        print("-" * 70)
        print(f"{'总计':<10} {total_bars:>10,}")
        print()

        # 计算预期数据量（3年 × 252个交易日/年 × 78条5分钟数据/天）
        expected_per_symbol = 3 * 252 * 78  # 约 59,000 条
        expected_total = expected_per_symbol * 10  # 10个股票

        progress = (total_bars / expected_total) * 100 if expected_total > 0 else 0

        print(f"预期总数据量: {expected_total:,} 条（10个股票 × 3年）")
        print(f"当前进度: {progress:.1f}%")

    print("=" * 70)

    conn.close()

if __name__ == '__main__':
    check_status()
