"""
市场数据获取模块

提供策略分析所需的历史K线数据：
- 从数据湖读取OHLCV数据
- 时间周期聚合（5分钟 -> 15分钟、1小时等）
- 格式化为LLM友好的数据结构
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Literal
from datetime import datetime
import pandas as pd

# 数据库路径
DB_PATH = Path(__file__).parent.parent / "data_lake" / "trades.db"


def aggregate_bars(
    df: pd.DataFrame,
    target_interval: Literal["15min", "1h", "1d"]
) -> pd.DataFrame:
    """
    聚合K线数据到目标时间周期

    Args:
        df: 原始数据（必须包含 timestamp, open, high, low, close, volume）
        target_interval: 目标周期（15min, 1h, 1d）

    Returns:
        聚合后的DataFrame
    """
    if df.empty:
        return df

    # 确保timestamp是datetime类型并转换为UTC
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df = df.set_index('timestamp')

    # 定义聚合规则
    resample_rules = {
        '15min': '15min',  # 15 minutes
        '1h': '1h',        # 1 hour
        '1d': '1D'         # 1 day
    }

    if target_interval not in resample_rules:
        raise ValueError(f"Unsupported interval: {target_interval}")

    # 聚合
    resampled = df.resample(resample_rules[target_interval]).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()

    resampled = resampled.reset_index()

    return resampled


def fetch_kline_data(
    symbol: str,
    interval: Literal["5min", "15min", "1h", "1d"] = "15min",
    limit: int = 600
) -> Optional[pd.DataFrame]:
    """
    获取K线数据

    Args:
        symbol: 标的符号（如 'SPY', 'AAPL'）
        interval: 时间周期（5min, 15min, 1h, 1d）
        limit: 返回的K线数量（从最新往前数）

    Returns:
        DataFrame包含: timestamp, open, high, low, close, volume
        如果无数据则返回None
    """
    if not DB_PATH.exists():
        print(f"错误: 数据库文件不存在 - {DB_PATH}")
        return None

    try:
        conn = sqlite3.connect(DB_PATH)

        # 查询最新的N条记录（5分钟周期）
        # 如果需要15分钟数据，我们需要获取更多5分钟数据然后聚合
        multiplier = 1
        if interval == "15min":
            multiplier = 3  # 3个5分钟 = 15分钟
        elif interval == "1h":
            multiplier = 12  # 12个5分钟 = 1小时
        elif interval == "1d":
            multiplier = 78  # 78个5分钟 ≈ 1个交易日（6.5小时）

        fetch_limit = limit * multiplier

        query = """
        SELECT timestamp, open, high, low, close, volume
        FROM market_data_bars
        WHERE symbol = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """

        df = pd.read_sql_query(query, conn, params=(symbol, fetch_limit))
        conn.close()

        if df.empty:
            print(f"警告: 标的 '{symbol}' 没有历史数据")
            return None

        # 反转顺序（从旧到新）
        df = df.iloc[::-1].reset_index(drop=True)

        # 如果需要聚合
        if interval != "5min":
            df = aggregate_bars(df, interval)

        # 取最后N条
        if len(df) > limit:
            df = df.tail(limit).reset_index(drop=True)

        return df

    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return None
    except Exception as e:
        print(f"获取K线数据时出错: {e}")
        return None


def format_kline_for_llm(df: pd.DataFrame, max_rows: int = 600) -> str:
    """
    将K线数据格式化为紧凑CSV格式（大幅减少token使用）

    策略：
    - 前N-50根：每3根抽样1根（保留趋势）
    - 最后50根：完整保留（保留细节）

    格式：idx,mmdd-hhmm,open,high,low,close,volume

    Args:
        df: K线数据DataFrame
        max_rows: 最多显示的行数

    Returns:
        格式化的CSV字符串
    """
    if df is None or df.empty:
        return "无数据"

    # 限制行数
    if len(df) > max_rows:
        df = df.tail(max_rows)

    df = df.copy()

    # 分离历史数据和近期数据
    if len(df) > 50:
        historical = df.iloc[:-50]
        recent = df.iloc[-50:]

        # 历史数据每3根抽样1根
        sampled_historical = historical.iloc[::3]

        # 合并抽样历史数据和完整近期数据
        df_final = pd.concat([sampled_historical, recent])
    else:
        df_final = df

    # 重置索引
    df_final = df_final.reset_index(drop=True)

    # 格式化时间戳为紧凑格式 mmdd-hhmm
    df_final['timestamp'] = pd.to_datetime(df_final['timestamp']).dt.strftime('%m%d-%H%M')

    # 构建CSV输出（紧凑格式，无空格）
    output = f"# K线数据 (总计{len(df_final)}条，原始{len(df)}条)\n"
    output += "# 格式: idx,mmdd-hhmm,open,high,low,close,volume\n\n"

    for idx, row in enumerate(df_final.itertuples(), 1):
        output += f"{idx},{row.timestamp},{row.open:.2f},{row.high:.2f},{row.low:.2f},{row.close:.2f},{int(row.volume)}\n"

    return output


def get_kline_summary(df: pd.DataFrame) -> Dict:
    """
    获取K线数据的统计摘要

    Args:
        df: K线数据DataFrame

    Returns:
        统计摘要字典
    """
    if df is None or df.empty:
        return {}

    return {
        'total_bars': len(df),
        'time_range': {
            'start': str(df['timestamp'].iloc[0]),
            'end': str(df['timestamp'].iloc[-1])
        },
        'price_range': {
            'highest': float(df['high'].max()),
            'lowest': float(df['low'].min()),
            'current': float(df['close'].iloc[-1])
        },
        'volume': {
            'total': int(df['volume'].sum()),
            'average': int(df['volume'].mean()),
            'max': int(df['volume'].max())
        }
    }


# 导出所有公共函数
__all__ = [
    'fetch_kline_data',
    'format_kline_for_llm',
    'get_kline_summary',
    'aggregate_bars'
]
