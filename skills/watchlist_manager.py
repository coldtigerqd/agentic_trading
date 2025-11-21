"""
基于性能的自动观察列表管理与轮换。

通过跟踪交易性能和轮换表现不佳的标的来管理标的观察列表。
使用 Sharpe 比率、胜率、平均盈亏和交易频率的综合评分。
"""

import sqlite3
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

# 数据库路径
DB_PATH = Path(__file__).parent.parent / "data_lake" / "trades.db"

# 板块映射，用于强制多样化
SECTOR_MAP = {
    # 广泛市场 ETF
    "SPY": "Broad Market", "QQQ": "Technology", "IWM": "Broad Market",
    "DIA": "Broad Market", "VTI": "Broad Market",

    # 板块 ETF
    "XLF": "Financial", "XLE": "Energy", "XLK": "Technology",
    "XLV": "Healthcare", "XLI": "Industrial", "XLP": "Consumer Staples",
    "XLY": "Consumer Discretionary", "XLU": "Utilities", "XLRE": "Real Estate",
    "XLB": "Materials", "XLC": "Communication",

    # 科技股
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology",
    "META": "Technology", "NVDA": "Technology", "AMD": "Technology",
    "TSLA": "Consumer Discretionary", "NFLX": "Communication",
    "AMZN": "Consumer Discretionary", "SHOP": "Technology",

    # 半导体
    "TSM": "Technology", "INTC": "Technology", "QCOM": "Technology",
    "AVGO": "Technology", "MU": "Technology",

    # 其他
    "JPM": "Financial", "BAC": "Financial", "GS": "Financial",
    "XOM": "Energy", "CVX": "Energy",
}

# 未映射标的的默认板块
DEFAULT_SECTOR = "Other"

# 配置常量
SHARPE_WEIGHT = 0.40
WIN_RATE_WEIGHT = 0.30
AVG_PNL_WEIGHT = 0.20
FREQ_WEIGHT = 0.10

MAX_SECTOR_PCT = 0.30  # 每个板块最多 30%
MAX_CHURN_PER_WEEK = 3  # 每周最多 3 次标的更改
ROTATION_PCT = 0.20  # 底部 20% 符合轮换条件
MIN_TRADES_FOR_SCORING = 5  # 有效评分所需的最少交易数


def get_symbol_sector(symbol: str) -> str:
    """
    获取标的所属板块。

    Args:
        symbol: 交易标的

    Returns:
        板块名称
    """
    return SECTOR_MAP.get(symbol, DEFAULT_SECTOR)


def calculate_sharpe_ratio(pnls: List[float], risk_free_rate: float = 0.0) -> float:
    """
    从盈亏序列计算 Sharpe 比率。

    Sharpe = (平均回报 - 无风险利率) / 回报标准差

    Args:
        pnls: 盈亏值列表
        risk_free_rate: 无风险利率（年化，默认 0%）

    Returns:
        Sharpe 比率（越高越好）
    """
    if len(pnls) < 2:
        return 0.0

    returns = np.array(pnls)
    mean_return = np.mean(returns)
    std_return = np.std(returns, ddof=1)

    if std_return == 0:
        return 0.0 if mean_return <= risk_free_rate else np.inf

    sharpe = (mean_return - risk_free_rate) / std_return
    return sharpe


def calculate_symbol_score(
    symbol: str,
    lookback_days: int = 30,
    db_path: Optional[Path] = None
) -> Dict:
    """
    计算标的的综合性能评分。

    评分组成（加权）：
    - Sharpe 比率：40%
    - 胜率：30%
    - 平均盈亏：20%
    - 交易频率：10%

    Args:
        symbol: 要评分的交易标的
        lookback_days: 回溯的天数
        db_path: 数据库路径（默认：DB_PATH）

    Returns:
        包含评分组成和综合评分的字典：
        {
            "symbol": str,
            "score": float,  # 0-100 的综合评分
            "sharpe_ratio": float,
            "win_rate": float,  # 0.0-1.0
            "avg_pnl": float,  # 每笔交易的平均利润
            "trade_count": int,
            "sector": str,
            "days_tracked": int,
            "has_min_trades": bool  # 是否 >= MIN_TRADES_FOR_SCORING
        }
    """
    if db_path is None:
        db_path = DB_PATH

    # 在回溯期内查询此标的的已关闭交易
    start_date = (datetime.now() - timedelta(days=lookback_days)).isoformat()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT pnl, status, timestamp
        FROM trades
        WHERE symbol = ?
          AND timestamp >= ?
          AND status IN ('FILLED', 'CLOSED')
          AND pnl IS NOT NULL
        ORDER BY timestamp ASC
    """, (symbol, start_date))

    trades = cursor.fetchall()
    conn.close()

    # 没有交易的标的的默认结果
    if len(trades) == 0:
        return {
            "symbol": symbol,
            "score": 0.0,
            "sharpe_ratio": 0.0,
            "win_rate": 0.0,
            "avg_pnl": 0.0,
            "trade_count": 0,
            "sector": get_symbol_sector(symbol),
            "days_tracked": lookback_days,
            "has_min_trades": False
        }

    # 提取盈亏值
    pnls = [trade["pnl"] for trade in trades]
    trade_count = len(pnls)

    # 计算组成部分
    sharpe = calculate_sharpe_ratio(pnls)
    win_count = sum(1 for pnl in pnls if pnl > 0)
    win_rate = win_count / trade_count if trade_count > 0 else 0.0
    avg_pnl = np.mean(pnls)

    # 将组成部分归一化到 0-100 范围
    # Sharpe：-3 到 +3 → 0 到 100
    sharpe_normalized = np.clip((sharpe + 3) / 6 * 100, 0, 100)

    # 胜率：0% 到 100% → 0 到 100
    win_rate_normalized = win_rate * 100

    # 平均盈亏：-500 到 +500 → 0 到 100
    avg_pnl_normalized = np.clip((avg_pnl + 500) / 1000 * 100, 0, 100)

    # 交易频率：0 到 20 笔交易 → 0 到 100
    freq_normalized = np.clip(trade_count / 20 * 100, 0, 100)

    # 综合评分（加权平均）
    composite_score = (
        sharpe_normalized * SHARPE_WEIGHT +
        win_rate_normalized * WIN_RATE_WEIGHT +
        avg_pnl_normalized * AVG_PNL_WEIGHT +
        freq_normalized * FREQ_WEIGHT
    )

    return {
        "symbol": symbol,
        "score": round(composite_score, 2),
        "sharpe_ratio": round(sharpe, 3),
        "win_rate": round(win_rate, 3),
        "avg_pnl": round(avg_pnl, 2),
        "trade_count": trade_count,
        "sector": get_symbol_sector(symbol),
        "days_tracked": lookback_days,
        "has_min_trades": trade_count >= MIN_TRADES_FOR_SCORING
    }


def get_current_watchlist(db_path: Optional[Path] = None) -> List[str]:
    """
    获取当前活跃的观察列表标的。

    Args:
        db_path: 数据库路径（默认：DB_PATH）

    Returns:
        活跃标的列表
    """
    if db_path is None:
        db_path = DB_PATH

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT symbol
        FROM watchlist
        WHERE active = 1
        ORDER BY priority DESC, symbol ASC
    """)

    symbols = [row["symbol"] for row in cursor.fetchall()]
    conn.close()

    return symbols


def get_recent_churn(days: int = 7, db_path: Optional[Path] = None) -> int:
    """
    统计最近 N 天内的观察列表变动次数。

    Args:
        days: 回溯天数
        db_path: 数据库路径（默认：DB_PATH）

    Returns:
        期间内添加/移除的标的数量
    """
    if db_path is None:
        db_path = DB_PATH

    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 统计添加
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM watchlist
        WHERE added_at >= ?
    """, (cutoff_date,))

    additions = cursor.fetchone()["count"]

    # 统计移除（active=0 且 last_updated 在期间内）
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM watchlist
        WHERE active = 0
          AND last_updated >= ?
    """, (cutoff_date,))

    removals = cursor.fetchone()["count"]
    conn.close()

    return additions + removals


def update_watchlist(
    candidate_pool: List[str],
    max_watchlist_size: int = 20,
    lookback_days: int = 30,
    enforce_sector_limits: bool = True,
    db_path: Optional[Path] = None
) -> Dict:
    """
    通过轮换表现不佳者来更新观察列表。

    算法：
    1. 评分所有当前观察列表标的
    2. 识别底部 20% 的表现者（具有最小交易数）
    3. 评分候选池
    4. 用顶级候选者替换表现不佳者
    5. 强制执行板块多样化（每个板块最多 30%）
    6. 强制执行变动限制（每周最多 3 次更改）

    Args:
        candidate_pool: 要考虑的候选标的列表
        max_watchlist_size: 最大观察列表大小（默认 20）
        lookback_days: 回溯性能的天数（默认 30）
        enforce_sector_limits: 是否强制执行板块多样化
        db_path: 数据库路径（默认：DB_PATH）

    Returns:
        包含更新结果的字典：
        {
            "added": List[str],
            "removed": List[str],
            "scores": Dict[str, Dict],  # symbol -> score 详情
            "churn_limit_reached": bool,
            "sector_distribution": Dict[str, int]
        }
    """
    if db_path is None:
        db_path = DB_PATH

    # 检查变动限制
    recent_churn = get_recent_churn(days=7, db_path=db_path)
    churn_available = MAX_CHURN_PER_WEEK - recent_churn

    if churn_available <= 0:
        warnings.warn(
            f"已达到变动限制（本周 {recent_churn}/{MAX_CHURN_PER_WEEK} 次更改）。"
            "未执行观察列表更新。"
        )
        return {
            "added": [],
            "removed": [],
            "scores": {},
            "churn_limit_reached": True,
            "sector_distribution": {}
        }

    # 获取当前观察列表
    current_symbols = get_current_watchlist(db_path)

    # 评分当前观察列表
    current_scores = {}
    for symbol in current_symbols:
        score_data = calculate_symbol_score(symbol, lookback_days, db_path)
        current_scores[symbol] = score_data

    # 识别表现不佳者（底部 20%，具有最小交易数）
    scored_symbols = [
        (sym, data) for sym, data in current_scores.items()
        if data["has_min_trades"]
    ]

    if len(scored_symbols) == 0:
        # 没有足够交易数的标的可以评分
        return {
            "added": [],
            "removed": [],
            "scores": current_scores,
            "churn_limit_reached": False,
            "sector_distribution": {}
        }

    scored_symbols.sort(key=lambda x: x[1]["score"])
    rotation_count = max(1, int(len(scored_symbols) * ROTATION_PCT))
    rotation_count = min(rotation_count, churn_available)  # 遵守变动限制

    underperformers = [sym for sym, _ in scored_symbols[:rotation_count]]

    # 评分候选池
    candidate_scores = {}
    for symbol in candidate_pool:
        if symbol not in current_symbols:  # 不重新添加当前标的
            score_data = calculate_symbol_score(symbol, lookback_days, db_path)
            candidate_scores[symbol] = score_data

    # 按评分排名候选者
    ranked_candidates = sorted(
        candidate_scores.items(),
        key=lambda x: x[1]["score"],
        reverse=True
    )

    # 选择替换者（如果启用，遵守板块限制）
    added = []
    removed = []

    # 计算当前板块分布
    remaining_symbols = [s for s in current_symbols if s not in underperformers]
    sector_counts = {}
    for symbol in remaining_symbols:
        sector = get_symbol_sector(symbol)
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

    # 添加候选者以填补空位
    max_total_symbols = min(max_watchlist_size, len(current_symbols))

    for candidate, score_data in ranked_candidates:
        if len(added) >= len(underperformers):
            break  # 已填满所有空位

        # 检查板块限制
        if enforce_sector_limits:
            sector = score_data["sector"]
            current_sector_count = sector_counts.get(sector, 0)
            projected_total = len(remaining_symbols) + len(added)

            if projected_total == 0:
                sector_pct = 0
            else:
                sector_pct = (current_sector_count + 1) / projected_total

            if sector_pct > MAX_SECTOR_PCT:
                continue  # 跳过，会违反板块限制

        # 添加候选者
        added.append(candidate)
        sector = score_data["sector"]
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

    # 只移除我们可以替换的表现不佳者
    removed = underperformers[:len(added)]

    # 更新数据库
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    try:
        # 移除表现不佳者
        for symbol in removed:
            cursor.execute("""
                UPDATE watchlist
                SET active = 0, last_updated = ?
                WHERE symbol = ?
            """, (now, symbol))

        # 添加新标的
        for symbol in added:
            # 检查标的是否已存在（之前被移除）
            cursor.execute("SELECT symbol FROM watchlist WHERE symbol = ?", (symbol,))
            exists = cursor.fetchone() is not None

            if exists:
                # 重新激活
                cursor.execute("""
                    UPDATE watchlist
                    SET active = 1, last_updated = ?, priority = 5
                    WHERE symbol = ?
                """, (now, symbol))
            else:
                # 插入新标的
                cursor.execute("""
                    INSERT INTO watchlist (symbol, added_at, active, priority, notes)
                    VALUES (?, ?, 1, 5, '由观察列表管理器自动添加')
                """, (symbol, now))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    # 合并评分
    all_scores = {**current_scores, **candidate_scores}

    return {
        "added": added,
        "removed": removed,
        "scores": all_scores,
        "churn_limit_reached": False,
        "sector_distribution": sector_counts
    }


def get_watchlist_performance_report(
    lookback_days: int = 30,
    db_path: Optional[Path] = None
) -> Dict:
    """
    生成当前观察列表的性能报告。

    Args:
        lookback_days: 回溯性能的天数
        db_path: 数据库路径（默认：DB_PATH）

    Returns:
        包含性能指标的字典：
        {
            "symbol_scores": List[Dict],  # 按评分排序（降序）
            "avg_score": float,
            "total_trades": int,
            "sector_distribution": Dict[str, int],
            "underperformers": List[str],  # 底部 20%
            "top_performers": List[str]  # 顶部 20%
        }
    """
    if db_path is None:
        db_path = DB_PATH

    current_symbols = get_current_watchlist(db_path)

    # 评分所有标的
    scores = []
    total_trades = 0
    sector_dist = {}

    for symbol in current_symbols:
        score_data = calculate_symbol_score(symbol, lookback_days, db_path)
        scores.append(score_data)
        total_trades += score_data["trade_count"]

        sector = score_data["sector"]
        sector_dist[sector] = sector_dist.get(sector, 0) + 1

    # 按评分排序
    scores.sort(key=lambda x: x["score"], reverse=True)

    # 计算平均评分
    avg_score = np.mean([s["score"] for s in scores]) if scores else 0.0

    # 识别顶部和底部表现者
    count = len(scores)
    top_20_count = max(1, int(count * 0.2))
    bottom_20_count = max(1, int(count * 0.2))

    top_performers = [s["symbol"] for s in scores[:top_20_count]]
    underperformers = [s["symbol"] for s in scores[-bottom_20_count:]]

    return {
        "symbol_scores": scores,
        "avg_score": round(avg_score, 2),
        "total_trades": total_trades,
        "sector_distribution": sector_dist,
        "underperformers": underperformers,
        "top_performers": top_performers
    }


def add_to_watchlist(
    symbol: str,
    priority: int = 5,
    notes: str = "",
    auto_backfill: bool = True,
    backfill_days: int = 60,
    db_path: Optional[Path] = None
) -> Dict:
    """
    将标的添加到观察列表并自动回填数据。

    Args:
        symbol: 要添加的交易标的
        priority: 优先级（1-10，越高越重要）
        notes: 关于标的的可选备注
        auto_backfill: 是否触发自动回填（默认：True）
        backfill_days: 要回填的历史天数（默认：60）
        db_path: 数据库路径（默认：DB_PATH）

    Returns:
        包含添加结果的字典：
        {
            "symbol": str,
            "status": str,  # "ADDED", "ALREADY_EXISTS", "REACTIVATED"
            "priority": int,
            "backfill_triggered": bool,
            "backfill_info": Dict  # 回填任务详情
        }
    """
    if db_path is None:
        db_path = DB_PATH

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    try:
        # 检查标的是否已存在
        cursor.execute("SELECT * FROM watchlist WHERE symbol = ?", (symbol,))
        existing = cursor.fetchone()

        if existing:
            if existing["active"] == 1:
                status = "ALREADY_EXISTS"
                print(f"标的 {symbol} 已在活跃观察列表中")
            else:
                # 重新激活
                cursor.execute("""
                    UPDATE watchlist
                    SET active = 1, last_updated = ?, priority = ?, notes = ?
                    WHERE symbol = ?
                """, (now, priority, notes or existing["notes"], symbol))
                conn.commit()
                status = "REACTIVATED"
                print(f"标的 {symbol} 已在观察列表中重新激活")
        else:
            # 插入新标的
            cursor.execute("""
                INSERT INTO watchlist (symbol, added_at, active, priority, notes)
                VALUES (?, ?, 1, ?, ?)
            """, (symbol, now, priority, notes or ""))
            conn.commit()
            status = "ADDED"
            print(f"标的 {symbol} 已添加到观察列表")

    except Exception as e:
        conn.rollback()
        conn.close()
        raise e
    finally:
        conn.close()

    # 如果启用，触发自动回填
    backfill_info = None
    backfill_triggered = False

    if auto_backfill and status in ["ADDED", "REACTIVATED"]:
        from skills.data_quality import auto_trigger_backfill

        backfill_info = auto_trigger_backfill(
            symbols=[symbol],
            missing_intervals=["5min", "1h", "daily"],
            days=backfill_days
        )
        backfill_triggered = True
        print(f"  → 回填已排队：{backfill_days} 天，{backfill_info['estimated_api_calls']} 次 API 调用")

    return {
        "symbol": symbol,
        "status": status,
        "priority": priority,
        "backfill_triggered": backfill_triggered,
        "backfill_info": backfill_info
    }


def remove_from_watchlist(
    symbol: str,
    db_path: Optional[Path] = None
) -> Dict:
    """
    从观察列表中移除（停用）标的。

    Args:
        symbol: 要移除的交易标的
        db_path: 数据库路径（默认：DB_PATH）

    Returns:
        包含移除结果的字典：
        {
            "symbol": str,
            "status": str,  # "REMOVED", "NOT_FOUND", "ALREADY_INACTIVE"
        }
    """
    if db_path is None:
        db_path = DB_PATH

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    try:
        # 检查标的是否存在
        cursor.execute("SELECT active FROM watchlist WHERE symbol = ?", (symbol,))
        result = cursor.fetchone()

        if not result:
            status = "NOT_FOUND"
        elif result[0] == 0:
            status = "ALREADY_INACTIVE"
        else:
            # 停用
            cursor.execute("""
                UPDATE watchlist
                SET active = 0, last_updated = ?
                WHERE symbol = ?
            """, (now, symbol))
            conn.commit()
            status = "REMOVED"

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    return {
        "symbol": symbol,
        "status": status
    }
