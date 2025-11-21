"""
交易决策的数学计算函数。

提供确定性金融计算，包括 Kelly Criterion、
Black-Scholes 隐含波动率和期权 Greeks。
"""

import math
from typing import Optional
from scipy import stats
from scipy.optimize import newton


def kelly_criterion(
    win_prob: float,
    win_amount: float,
    loss_amount: float,
    bankroll: float,
    fraction: float = 0.25
) -> float:
    """
    使用 Kelly Criterion 计算仓位大小。

    为安全起见使用分数 Kelly (默认 0.25) 以避免过度下注。

    参数:
        win_prob: 获胜概率 (0.0-1.0)
        win_amount: 获胜时的预期利润 ($)
        loss_amount: 失败时的预期损失 ($)
        bankroll: 可用资金总额 ($)
        fraction: 使用的 Kelly 分数 (默认 0.25 为四分之一 Kelly)

    返回:
        以美元计的仓位大小（非负值）

    示例:
        >>> kelly_criterion(0.6, 500, 200, 10000, 0.25)
        750.0  # 投资 $750
    """
    if win_prob <= 0 or win_prob >= 1:
        return 0.0

    if win_amount <= 0 or loss_amount <= 0:
        return 0.0

    if bankroll <= 0:
        return 0.0

    # Kelly 公式: (p * W - (1-p) * L) / W
    # 其中 p=win_prob, W=win_amount, L=loss_amount
    kelly = (win_prob * win_amount - (1 - win_prob) * loss_amount) / win_amount

    # 应用分数 Kelly
    kelly_fraction = kelly * fraction

    # 计算仓位大小
    position_size = bankroll * kelly_fraction

    # 永不返回负值仓位
    return max(0.0, position_size)


def black_scholes_price(
    spot: float,
    strike: float,
    time_to_expiry: float,
    rate: float,
    volatility: float,
    is_call: bool
) -> float:
    """
    计算 Black-Scholes 期权价格。

    参数:
        spot: 当前股价
        strike: 行权价
        time_to_expiry: 距到期时间（年）
        rate: 无风险利率（年化）
        volatility: 波动率（年化，小数形式，例如 0.25 表示 25%）
        is_call: True 表示看涨期权，False 表示看跌期权

    返回:
        期权价格
    """
    if time_to_expiry <= 0:
        # 到期时，期权价值为内在价值
        if is_call:
            return max(0, spot - strike)
        else:
            return max(0, strike - spot)

    # 计算 d1 和 d2
    d1 = (math.log(spot / strike) + (rate + 0.5 * volatility ** 2) * time_to_expiry) / \
         (volatility * math.sqrt(time_to_expiry))
    d2 = d1 - volatility * math.sqrt(time_to_expiry)

    if is_call:
        price = spot * stats.norm.cdf(d1) - strike * math.exp(-rate * time_to_expiry) * stats.norm.cdf(d2)
    else:
        price = strike * math.exp(-rate * time_to_expiry) * stats.norm.cdf(-d2) - spot * stats.norm.cdf(-d1)

    return price


def black_scholes_iv(
    option_price: float,
    spot: float,
    strike: float,
    time_to_expiry: float,
    rate: float,
    is_call: bool,
    initial_guess: float = 0.3,
    max_iterations: int = 100,
    tolerance: float = 1e-6
) -> Optional[float]:
    """
    使用 Newton-Raphson 方法计算隐含波动率。

    参数:
        option_price: 观察到的期权价格
        spot: 当前股价
        strike: 行权价
        time_to_expiry: 距到期时间（年）
        rate: 无风险利率（年化）
        is_call: True 表示看涨期权，False 表示看跌期权
        initial_guess: 波动率初始猜测值（默认 0.3 = 30%）
        max_iterations: Newton-Raphson 最大迭代次数
        tolerance: 收敛容差

    返回:
        隐含波动率（小数形式，例如 0.35 表示 35%），如果未收敛则返回 None

    示例:
        >>> black_scholes_iv(5.50, 100, 105, 0.25, 0.05, True)
        0.35  # 35% 隐含波动率
    """
    if option_price <= 0 or spot <= 0 or strike <= 0 or time_to_expiry <= 0:
        return None

    def objective(vol):
        """理论价格与市场价格之差。"""
        if vol <= 0:
            return float('inf')
        return black_scholes_price(spot, strike, time_to_expiry, rate, vol, is_call) - option_price

    def vega(vol):
        """Vega: 价格对波动率的导数。"""
        if vol <= 0:
            return 1e-10  # 避免除以零
        d1 = (math.log(spot / strike) + (rate + 0.5 * vol ** 2) * time_to_expiry) / \
             (vol * math.sqrt(time_to_expiry))
        return spot * stats.norm.pdf(d1) * math.sqrt(time_to_expiry)

    try:
        # 使用 Newton-Raphson 方法求解波动率
        iv = newton(
            objective,
            x0=initial_guess,
            fprime=vega,
            maxiter=max_iterations,
            tol=tolerance
        )

        # 合理性检查：隐含波动率应在 0 到 5 (500%) 之间
        if 0 < iv < 5:
            return iv
        else:
            return None

    except (RuntimeError, ValueError):
        # Newton-Raphson 未能收敛
        return None


def calculate_delta(
    spot: float,
    strike: float,
    time_to_expiry: float,
    rate: float,
    volatility: float,
    is_call: bool
) -> float:
    """
    计算期权 delta。

    参数:
        spot: 当前股价
        strike: 行权价
        time_to_expiry: 距到期时间（年）
        rate: 无风险利率
        volatility: 波动率（年化）
        is_call: True 表示看涨期权，False 表示看跌期权

    返回:
        Delta 值
    """
    if time_to_expiry <= 0:
        # 到期时
        if is_call:
            return 1.0 if spot > strike else 0.0
        else:
            return -1.0 if spot < strike else 0.0

    d1 = (math.log(spot / strike) + (rate + 0.5 * volatility ** 2) * time_to_expiry) / \
         (volatility * math.sqrt(time_to_expiry))

    if is_call:
        return stats.norm.cdf(d1)
    else:
        return stats.norm.cdf(d1) - 1.0


def calculate_gamma(
    spot: float,
    strike: float,
    time_to_expiry: float,
    rate: float,
    volatility: float
) -> float:
    """
    计算期权 gamma（看涨和看跌期权相同）。

    参数:
        spot: 当前股价
        strike: 行权价
        time_to_expiry: 距到期时间（年）
        rate: 无风险利率
        volatility: 波动率（年化）

    返回:
        Gamma 值
    """
    if time_to_expiry <= 0:
        return 0.0

    d1 = (math.log(spot / strike) + (rate + 0.5 * volatility ** 2) * time_to_expiry) / \
         (volatility * math.sqrt(time_to_expiry))

    return stats.norm.pdf(d1) / (spot * volatility * math.sqrt(time_to_expiry))


def calculate_theta(
    spot: float,
    strike: float,
    time_to_expiry: float,
    rate: float,
    volatility: float,
    is_call: bool
) -> float:
    """
    计算期权 theta（每日时间衰减）。

    参数:
        spot: 当前股价
        strike: 行权价
        time_to_expiry: 距到期时间（年）
        rate: 无风险利率
        volatility: 波动率（年化）
        is_call: True 表示看涨期权，False 表示看跌期权

    返回:
        Theta 值（每日）
    """
    if time_to_expiry <= 0:
        return 0.0

    d1 = (math.log(spot / strike) + (rate + 0.5 * volatility ** 2) * time_to_expiry) / \
         (volatility * math.sqrt(time_to_expiry))
    d2 = d1 - volatility * math.sqrt(time_to_expiry)

    if is_call:
        theta = (-spot * stats.norm.pdf(d1) * volatility / (2 * math.sqrt(time_to_expiry)) -
                 rate * strike * math.exp(-rate * time_to_expiry) * stats.norm.cdf(d2))
    else:
        theta = (-spot * stats.norm.pdf(d1) * volatility / (2 * math.sqrt(time_to_expiry)) +
                 rate * strike * math.exp(-rate * time_to_expiry) * stats.norm.cdf(-d2))

    # 转换为每日 theta（除以 365）
    return theta / 365.0


def calculate_vega(
    spot: float,
    strike: float,
    time_to_expiry: float,
    rate: float,
    volatility: float
) -> float:
    """
    计算期权 vega（对波动率变化的敏感度）。

    参数:
        spot: 当前股价
        strike: 行权价
        time_to_expiry: 距到期时间（年）
        rate: 无风险利率
        volatility: 波动率（年化）

    返回:
        Vega 值（波动率变化 1% 时的变化）
    """
    if time_to_expiry <= 0:
        return 0.0

    d1 = (math.log(spot / strike) + (rate + 0.5 * volatility ** 2) * time_to_expiry) / \
         (volatility * math.sqrt(time_to_expiry))

    # 波动率变化 1% 时的 vega
    return spot * stats.norm.pdf(d1) * math.sqrt(time_to_expiry) / 100.0
