"""
Mathematical calculation functions for trading decisions.

Provides deterministic financial calculations including Kelly criterion,
Black-Scholes implied volatility, and option Greeks.
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
    Calculate position size using Kelly Criterion.

    Uses fractional Kelly (default 0.25) for safety to avoid over-betting.

    Args:
        win_prob: Probability of winning (0.0-1.0)
        win_amount: Expected profit on win ($)
        loss_amount: Expected loss on loss ($)
        bankroll: Total available capital ($)
        fraction: Kelly fraction to use (default 0.25 for quarter-Kelly)

    Returns:
        Position size in dollars (non-negative)

    Example:
        >>> kelly_criterion(0.6, 500, 200, 10000, 0.25)
        750.0  # Invest $750
    """
    if win_prob <= 0 or win_prob >= 1:
        return 0.0

    if win_amount <= 0 or loss_amount <= 0:
        return 0.0

    if bankroll <= 0:
        return 0.0

    # Kelly formula: (p * W - (1-p) * L) / W
    # where p=win_prob, W=win_amount, L=loss_amount
    kelly = (win_prob * win_amount - (1 - win_prob) * loss_amount) / win_amount

    # Apply fractional Kelly
    kelly_fraction = kelly * fraction

    # Calculate position size
    position_size = bankroll * kelly_fraction

    # Never return negative position
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
    Calculate Black-Scholes option price.

    Args:
        spot: Current stock price
        strike: Strike price
        time_to_expiry: Time to expiration in years
        rate: Risk-free interest rate (annual)
        volatility: Volatility (annual, as decimal e.g., 0.25 for 25%)
        is_call: True for call option, False for put

    Returns:
        Option price
    """
    if time_to_expiry <= 0:
        # At expiration, option worth intrinsic value
        if is_call:
            return max(0, spot - strike)
        else:
            return max(0, strike - spot)

    # Calculate d1 and d2
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
    Calculate implied volatility using Newton-Raphson method.

    Args:
        option_price: Observed option price
        spot: Current stock price
        strike: Strike price
        time_to_expiry: Time to expiration in years
        rate: Risk-free interest rate (annual)
        is_call: True for call option, False for put
        initial_guess: Starting volatility guess (default 0.3 = 30%)
        max_iterations: Maximum Newton-Raphson iterations
        tolerance: Convergence tolerance

    Returns:
        Implied volatility (as decimal, e.g., 0.35 for 35%), or None if failed to converge

    Example:
        >>> black_scholes_iv(5.50, 100, 105, 0.25, 0.05, True)
        0.35  # 35% implied volatility
    """
    if option_price <= 0 or spot <= 0 or strike <= 0 or time_to_expiry <= 0:
        return None

    def objective(vol):
        """Difference between theoretical and market price."""
        if vol <= 0:
            return float('inf')
        return black_scholes_price(spot, strike, time_to_expiry, rate, vol, is_call) - option_price

    def vega(vol):
        """Vega: derivative of price with respect to volatility."""
        if vol <= 0:
            return 1e-10  # Avoid division by zero
        d1 = (math.log(spot / strike) + (rate + 0.5 * vol ** 2) * time_to_expiry) / \
             (vol * math.sqrt(time_to_expiry))
        return spot * stats.norm.pdf(d1) * math.sqrt(time_to_expiry)

    try:
        # Use Newton-Raphson to find volatility
        iv = newton(
            objective,
            x0=initial_guess,
            fprime=vega,
            maxiter=max_iterations,
            tol=tolerance
        )

        # Sanity check: IV should be between 0 and 5 (500%)
        if 0 < iv < 5:
            return iv
        else:
            return None

    except (RuntimeError, ValueError):
        # Newton-Raphson failed to converge
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
    Calculate option delta.

    Args:
        spot: Current stock price
        strike: Strike price
        time_to_expiry: Time to expiration in years
        rate: Risk-free interest rate
        volatility: Volatility (annual)
        is_call: True for call, False for put

    Returns:
        Delta value
    """
    if time_to_expiry <= 0:
        # At expiration
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
    Calculate option gamma (same for call and put).

    Args:
        spot: Current stock price
        strike: Strike price
        time_to_expiry: Time to expiration in years
        rate: Risk-free interest rate
        volatility: Volatility (annual)

    Returns:
        Gamma value
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
    Calculate option theta (time decay per day).

    Args:
        spot: Current stock price
        strike: Strike price
        time_to_expiry: Time to expiration in years
        rate: Risk-free interest rate
        volatility: Volatility (annual)
        is_call: True for call, False for put

    Returns:
        Theta value (per day)
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

    # Convert to per-day theta (divide by 365)
    return theta / 365.0


def calculate_vega(
    spot: float,
    strike: float,
    time_to_expiry: float,
    rate: float,
    volatility: float
) -> float:
    """
    Calculate option vega (sensitivity to volatility change).

    Args:
        spot: Current stock price
        strike: Strike price
        time_to_expiry: Time to expiration in years
        rate: Risk-free interest rate
        volatility: Volatility (annual)

    Returns:
        Vega value (per 1% change in volatility)
    """
    if time_to_expiry <= 0:
        return 0.0

    d1 = (math.log(spot / strike) + (rate + 0.5 * volatility ** 2) * time_to_expiry) / \
         (volatility * math.sqrt(time_to_expiry))

    # Vega per 1% change in volatility
    return spot * stats.norm.pdf(d1) * math.sqrt(time_to_expiry) / 100.0
