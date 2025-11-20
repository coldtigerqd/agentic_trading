# 蜂群智能增强指南

本文档提供蜂群智能系统增强功能的全面指导，包括新策略模板、技术指标库和自动化监控列表管理。

## 目录

1. [概述](#概述)
2. [技术指标库](#技术指标库)
3. [新策略模板](#新策略模板)
4. [监控列表管理器](#监控列表管理器)
5. [集成示例](#集成示例)
6. [情绪分析（可选）](#情绪分析可选)

---

## 概述

蜂群智能系统已增强以下功能：

- **15 个技术指标**：向量化 NumPy 实现，性能提升 10 倍以上
- **3 个新策略模板**：均值回归、突破侦察、相关套利
- **自动化监控列表管理器**：基于表现的标的轮换，带板块分散化
- **情绪 MCP 集成**：新闻和 Twitter 情绪分析（可选）

### 系统架构

```
指挥官代理 (Commander Agent)
    ↓
蜂群智能 (5 个并发策略)
    ├── Vol Sniper (earnings volatility)
    ├── Trend Scout (momentum breakouts)
    ├── Mean Reversion (range-bound markets)
    ├── Breakout Scout (volatility squeezes)
    └── Correlation Arbitrage (pairs trading)
         ↓
技术指标库 (15 个函数)
         ↓
市场数据 (3年缓存, 5分钟K线)
         ↓
监控列表管理器 (自动轮换)
```

---

## 技术指标库

### 位置
`skills/technical_indicators.py`

### 性能
- **18.7 倍加速** SMA（超过 10 倍要求）
- 所有函数使用 NumPy 向量化
- 处理边缘情况（NaN、空数组、数据不足）

### 可用函数

#### 移动平均线
```python
from skills import calculate_sma, calculate_ema, calculate_wma

# 简单移动平均 (Simple Moving Average)
sma = calculate_sma(bars, period=20, field='close')
# 结果: np.ndarray，前 (period-1) 个值为 NaN

# 指数移动平均 (Exponential Moving Average，带 NaN 感知初始化)
ema = calculate_ema(bars, period=12, field='close')

# 加权移动平均 (Weighted Moving Average)
wma = calculate_wma(bars, period=10, field='close')
```

#### 动量指标
```python
from skills import calculate_rsi, calculate_macd, calculate_stochastic

# RSI (Wilder's smoothing)
rsi = calculate_rsi(bars, period=14)
# 返回: np.ndarray (0-100 刻度)
# 边缘情况: 恒定价格返回 50.0（中性）

# MACD
macd = calculate_macd(bars, fast=12, slow=26, signal=9)
# 返回: {'macd_line': ndarray, 'signal_line': ndarray, 'histogram': ndarray}

# 随机振荡器 (Stochastic Oscillator)
stoch = calculate_stochastic(bars, k_period=14, d_period=3)
# 返回: {'k_line': ndarray, 'd_line': ndarray}
```

#### 波动率指标
```python
from skills import (
    calculate_bollinger_bands,
    calculate_atr,
    calculate_historical_volatility
)

# Bollinger Bands
bb = calculate_bollinger_bands(bars, period=20, std_dev=2.0)
# 返回: {
#     'upper_band': ndarray,
#     'middle_band': ndarray (SMA),
#     'lower_band': ndarray,
#     'bandwidth': ndarray  # 归一化 (upper-lower)/middle
# }

# ATR (Wilder's smoothing)
atr = calculate_atr(bars, period=14)
# 返回: np.ndarray

# 历史波动率（年化）
hv = calculate_historical_volatility(bars, period=20)
# 返回: np.ndarray (年化收益率标准差)
```

#### 趋势检测
```python
from skills import calculate_adx, detect_trend

# ADX (Average Directional Index)
adx = calculate_adx(bars, period=14)
# 返回: np.ndarray
# ADX > 25: 强趋势
# ADX < 20: 弱趋势 / 震荡

# 趋势分类
trend = detect_trend(bars, sma_short=20, sma_long=50)
# 返回: str
# 选项: "STRONG_UPTREND", "WEAK_UPTREND", "SIDEWAYS",
#       "WEAK_DOWNTREND", "STRONG_DOWNTREND"
```

#### 支撑/阻力
```python
from skills import find_swing_highs, find_swing_lows, calculate_pivot_points

# 摆动点
highs = find_swing_highs(bars, window=5, min_bars=10)
# 返回: List[float]（降序排列）

lows = find_swing_lows(bars, window=5, min_bars=10)
# 返回: List[float]（升序排列）

# 枢轴点（用于单根K线或最新K线）
pivots = calculate_pivot_points(bars)
# 返回: {
#     'pivot': float,
#     'r1': float, 'r2': float, 'r3': float,
#     's1': float, 's2': float, 's3': float
# }
```

#### 成交量指标
```python
from skills import calculate_obv, calculate_vwap

# 能量潮 (On-Balance Volume)
obv = calculate_obv(bars)
# 返回: np.ndarray（基于价格方向的累积成交量）

# VWAP
vwap = calculate_vwap(bars)
# 返回: np.ndarray（成交量加权平均价）
```

### 输入格式

所有技术指标函数期望 bars 为以下格式：

```python
bars = [
    {
        'timestamp': '2025-11-20T09:30:00',
        'open': 150.5,
        'high': 151.2,
        'low': 150.1,
        'close': 150.8,
        'volume': 1000000
    },
    # ... 更多K线
]
```

### 错误处理

- **空数组**: 返回空 np.ndarray 或默认字典
- **数据不足**: 返回 NaN 数组并发出警告
- **无效周期**: 验证 period > 0
- **NaN 值**: 适用时使用 `np.nanmean`、`np.nanstd`

---

## 新策略模板

### 1. 均值回归 (Mean Reversion)

**位置**: `swarm_intelligence/templates/mean_reversion.md`
**实例**: `swarm_intelligence/active_instances/mean_reversion_spx.json`

**目标市场**: 区间震荡、低波动率环境（ADX < 25）

**策略逻辑**:
1. 使用 ADX < max_adx 检测震荡区间（通常 20-25）
2. 测量 BB 位置和 RSI 极值
3. 验证区间稳定性（超过 min_range_days）
4. 推荐 Iron Condor（中性）或信用价差（极值）

**配置示例**:
```json
{
  "template": "mean_reversion",
  "name": "mean_reversion_spx",
  "priority": 6,
  "enabled": true,
  "parameters": {
    "symbol_pool": ["SPY", "QQQ", "IWM", "DIA", "XLF", "XLE", "XLK", "XLV"],
    "max_adx": 25,
    "bb_period": 20,
    "bb_std_dev": 2.0,
    "rsi_period": 14,
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "min_range_days": 10
  }
}
```

**信号**:
- **IRON_CONDOR**: 中性震荡（ADX < 20, BB 位置 0.4-0.6, RSI 40-60）
- **SHORT_CALL_SPREAD**: 超买极值（BB > 0.9, RSI > 70）
- **SHORT_PUT_SPREAD**: 超卖极值（BB < 0.1, RSI < 30）
- **NO_TRADE**: 趋势市场或震荡区间不足

---

### 2. 突破侦察 (Breakout Scout)

**位置**: `swarm_intelligence/templates/breakout_scout.md`
**实例**: `swarm_intelligence/active_instances/breakout_scout_tech.json`

**目标市场**: 波动率压缩后的爆发性走势

**策略逻辑**:
1. 检测波动率收缩（ATR 下降 >= atr_contraction_pct, BB 挤压）
2. 识别盘整形态（min_consolidation_days）
3. 等待带成交量确认的突破（volume_multiplier）
4. 使用 breakout_confirm_bars 过滤假突破
5. 使用 RSI 和 OBV 动量确认
6. 使用 ATR 和区间投影计算目标
7. 要求风险回报比 >= 2:1

**配置示例**:
```json
{
  "template": "breakout_scout",
  "name": "breakout_scout_tech",
  "priority": 7,
  "enabled": true,
  "parameters": {
    "symbol_pool": ["NVDA", "TSLA", "AMD", "META", "GOOGL", "AMZN", "NFLX", "AAPL"],
    "atr_contraction_pct": 30,
    "bb_squeeze_threshold": 0.10,
    "volume_multiplier": 1.5,
    "min_consolidation_days": 5,
    "breakout_confirm_bars": 2
  }
}
```

**信号**:
- **LONG_CALL_SPREAD**: 看涨突破（价格 > 盘整高点, 成交量激增, RSI > 50）
- **LONG_PUT_SPREAD**: 看跌突破（价格 < 盘整低点, 成交量激增, RSI < 50）
- **NO_TRADE**: 无挤压、风险回报比不佳或确认不足

---

### 3. 相关套利 (Correlation Arbitrage)

**位置**: `swarm_intelligence/templates/correlation_arbitrage.md`
**实例**: `swarm_intelligence/active_instances/correlation_arb_tech_pairs.json`

**目标市场**: 相关对的统计套利

**策略逻辑**:
1. 计算 Pearson 相关性（要求 >= min_correlation）
2. 通过线性回归确定对冲比率（上限为 max_hedge_ratio）
3. 计算价差偏离的 z-score
4. 当 |z-score| >= zscore_threshold（通常 2.0）时入场
5. 使用 RSI 和 Bollinger Band 背离确认
6. 验证相关性稳定性（std < 0.15，超过 min_stability_days）
7. 检查相反趋势（避免相关性崩溃）
8. 测量历史回归率（要求 > 70%）

**配置示例**:
```json
{
  "template": "correlation_arbitrage",
  "name": "correlation_arb_tech_pairs",
  "priority": 8,
  "enabled": true,
  "parameters": {
    "symbol_pairs": [
      ["AAPL", "MSFT"],
      ["NVDA", "AMD"],
      ["GOOGL", "META"],
      ["AMZN", "SHOP"],
      ["TSM", "INTC"]
    ],
    "min_correlation": 0.7,
    "zscore_threshold": 2.0,
    "lookback_days": 90,
    "min_stability_days": 30,
    "max_hedge_ratio": 2.0
  }
}
```

**信号**:
- **LONG_SHORT_COMBO**: 标的 A 被高估（z-score > 2.0, 做多 B, 做空 A）
- **SHORT_LONG_COMBO**: 标的 A 被低估（z-score < -2.0, 做多 A, 做空 B）
- **NO_TRADE**: 相关性弱、不稳定或回归历史不佳

---

## 监控列表管理器

### 位置
`skills/watchlist_manager.py`

### 目的
根据交易表现自动轮换监控列表标的，同时强制执行板块分散化和稳定性约束。

### 核心函数

#### 1. 计算标的分数
```python
from skills import calculate_symbol_score

# 根据 30 天表现评分标的
score_data = calculate_symbol_score(
    symbol="AAPL",
    lookback_days=30  # 默认: 30
)

# 返回:
{
    "symbol": "AAPL",
    "score": 72.5,  # 综合分数 0-100
    "sharpe_ratio": 1.8,
    "win_rate": 0.65,  # 65% 胜率
    "avg_pnl": 120.50,  # 每笔交易平均 P&L
    "trade_count": 15,
    "sector": "Technology",
    "days_tracked": 30,
    "has_min_trades": True  # >= 5 笔交易
}
```

**评分公式**（0-100 刻度）:
- Sharpe 比率: 40% 权重（归一化: -3 到 +3 → 0 到 100）
- 胜率: 30% 权重（0% 到 100% → 0 到 100）
- 平均 P&L: 20% 权重（-$500 到 +$500 → 0 到 100）
- 交易频率: 10% 权重（0 到 20 笔交易 → 0 到 100）

#### 2. 更新监控列表
```python
from skills import update_watchlist

# 用顶级候选者轮换表现不佳者
result = update_watchlist(
    candidate_pool=["SPY", "QQQ", "AAPL", "NVDA", "AMD", "TSLA"],
    max_watchlist_size=20,  # 默认: 20
    lookback_days=30,  # 默认: 30
    enforce_sector_limits=True  # 默认: True
)

# 返回:
{
    "added": ["NVDA", "AMD"],  # 新增标的
    "removed": ["LOSER1", "LOSER2"],  # 移除的表现不佳者
    "scores": {...},  # 所有标的分数
    "churn_limit_reached": False,
    "sector_distribution": {
        "Technology": 6,
        "Financial": 3,
        "Energy": 2,
        "Broad Market": 4,
        ...
    }
}
```

**轮换逻辑**:
1. 评估所有当前监控列表标的
2. 识别底部 20% 表现者（>= 5 笔交易）
3. 评估候选池
4. 用顶级候选者替换表现不佳者
5. 强制执行板块限制（每个板块最多 30%）
6. 强制执行变动限制（每周最多 3 次变化）

#### 3. 获取表现报告
```python
from skills import get_watchlist_performance_report

report = get_watchlist_performance_report(lookback_days=30)

# 返回:
{
    "symbol_scores": [  # 按分数排序（降序）
        {"symbol": "AAPL", "score": 85.2, ...},
        {"symbol": "NVDA", "score": 78.5, ...},
        ...
    ],
    "avg_score": 68.5,
    "total_trades": 250,
    "sector_distribution": {"Technology": 8, ...},
    "underperformers": ["SYM1", "SYM2"],  # 底部 20%
    "top_performers": ["AAPL", "NVDA"]  # 顶部 20%
}
```

### 配置常量

位于 `skills/watchlist_manager.py`:

```python
MIN_TRADES_FOR_SCORING = 5  # 有效分数的最少交易数
ROTATION_PCT = 0.20  # 底部 20% 有资格轮换
MAX_CHURN_PER_WEEK = 3  # 每周最多标的变化数
MAX_SECTOR_PCT = 0.30  # 每个板块最多 30% 集中度

# 综合分数权重
SHARPE_WEIGHT = 0.40  # 40%
WIN_RATE_WEIGHT = 0.30  # 30%
AVG_PNL_WEIGHT = 0.20  # 20%
FREQ_WEIGHT = 0.10  # 10%
```

### 板块映射

监控列表管理器包含 40+ 标的的板块映射：

```python
SECTOR_MAP = {
    # 大盘市场
    "SPY": "Broad Market",
    "QQQ": "Technology",
    "IWM": "Broad Market",

    # 板块 ETF
    "XLF": "Financial",
    "XLE": "Energy",
    "XLK": "Technology",
    "XLV": "Healthcare",
    # ... 更多板块

    # 科技股
    "AAPL": "Technology",
    "NVDA": "Technology",
    "TSLA": "Consumer Discretionary",
    # ... 更多股票
}
```

**未知标的**默认板块为 "Other"。

### 每周轮换工作流

**推荐时间表**: 每周五市场收盘

```python
from skills import update_watchlist, get_watchlist_performance_report

# 1. 获取当前表现
report = get_watchlist_performance_report(lookback_days=7)

print(f"平均分数: {report['avg_score']}")
print(f"表现不佳者: {report['underperformers']}")

# 2. 定义候选池（从蜂群推荐或预定义列表）
candidates = [
    "AAPL", "MSFT", "NVDA", "AMD", "TSLA",
    "GOOGL", "META", "AMZN", "SPY", "QQQ",
    "IWM", "DIA", "XLF", "XLE", "XLK"
]

# 3. 更新监控列表
result = update_watchlist(
    candidate_pool=candidates,
    max_watchlist_size=20,
    lookback_days=7,  # 每周表现
    enforce_sector_limits=True
)

# 4. 记录结果
print(f"新增: {result['added']}")
print(f"移除: {result['removed']}")
print(f"板块分布: {result['sector_distribution']}")
```

---

## 集成示例

### 示例 1: 在蜂群模板中使用技术指标

```python
# 在 swarm_intelligence/templates/custom_strategy.md 中

from skills import (
    get_historical_bars,
    calculate_sma,
    calculate_rsi,
    calculate_bollinger_bands,
    detect_trend
)

# 获取数据
bars = get_historical_bars(symbol="{{ symbol }}", interval="daily", lookback_days=60)

# 计算指标
sma_20 = calculate_sma(bars, period=20)
sma_50 = calculate_sma(bars, period=50)
rsi = calculate_rsi(bars, period=14)
bb = calculate_bollinger_bands(bars, period=20, std_dev=2.0)

# 自动趋势检测
trend = detect_trend(bars, sma_short=20, sma_long=50)
# 返回: "STRONG_UPTREND", "WEAK_UPTREND", "SIDEWAYS" 等

# 生成信号
if trend == "STRONG_UPTREND" and rsi[-1] < 70:
    signal = "LONG_CALL_SPREAD"
elif trend == "STRONG_DOWNTREND" and rsi[-1] > 30:
    signal = "LONG_PUT_SPREAD"
else:
    signal = "NO_TRADE"
```

### 示例 2: 带监控列表管理器的 Commander 工作流

```python
# 在 prompts/commander_system_prompt.md 中

from skills import (
    get_watchlist_performance_report,
    update_watchlist,
    consult_swarm
)

# 步骤 1: 获取监控列表表现
report = get_watchlist_performance_report(lookback_days=7)

# 步骤 2: 检查是否需要每周轮换（周五）
if today_is_friday():
    # 从蜂群获取新候选者推荐
    swarm_results = consult_swarm()

    # 提取高置信度标的
    high_confidence_symbols = [
        r["target"] for r in swarm_results
        if r["confidence"] > 0.75 and r["signal"] != "NO_TRADE"
    ]

    # 添加到候选池
    candidates = high_confidence_symbols + [
        "SPY", "QQQ", "IWM", "DIA"  # 核心持仓
    ]

    # 轮换监控列表
    rotation_result = update_watchlist(
        candidate_pool=candidates,
        max_watchlist_size=20,
        lookback_days=7,
        enforce_sector_limits=True
    )

    # 记录轮换
    if rotation_result["added"]:
        log(f"监控列表轮换: 新增 {rotation_result['added']}, "
            f"移除 {rotation_result['removed']}")
```

### 示例 3: 情绪增强策略

```python
# 使用 news-sentiment MCP（如果可用）

from skills import get_historical_bars, calculate_rsi

# 获取技术分析
bars = get_historical_bars("AAPL", interval="daily", lookback_days=30)
rsi = calculate_rsi(bars, period=14)

# 获取情绪（通过 MCP）
# 假设 MCP 工具: get_news_sentiment(symbol)
sentiment = get_news_sentiment("AAPL")

# 结合技术 + 情绪
if rsi[-1] < 30 and sentiment["score"] > 0.5:
    # 超卖 + 积极情绪 = 强烈买入信号
    signal = "LONG_CALL_SPREAD"
    confidence = 0.85
elif rsi[-1] > 70 and sentiment["score"] < -0.5:
    # 超买 + 消极情绪 = 强烈卖出信号
    signal = "LONG_PUT_SPREAD"
    confidence = 0.85
else:
    # 技术面和情绪面冲突
    signal = "NO_TRADE"
    confidence = 0.0
```

---

## 情绪分析（可选）

### MCP 服务器位置
`mcp-servers/news-sentiment/`

### 功能
1. **新闻情绪**: 基于 LLM 的情绪评分（-1 到 +1）
2. **Twitter/X 情绪**: 实时社交情绪跟踪
3. **事件日历**: 财报日期、经济事件（FOMC、CPI、GDP）

### 配置

#### 1. 安装依赖
```bash
cd mcp-servers/news-sentiment
pip install requests anthropic
```

#### 2. 设置 API 密钥
```bash
export SERPER_API_KEY="your-serper-key"  # 用于新闻
export ANTHROPIC_API_KEY="your-anthropic-key"  # 用于情绪评分
export TWITTER_BEARER_TOKEN="your-twitter-token"  # 可选
```

#### 3. 配置 MCP 客户端
添加到 Claude Code MCP 配置：

```json
{
  "mcpServers": {
    "news-sentiment": {
      "command": "python",
      "args": ["/path/to/mcp-servers/news-sentiment/server.py"],
      "env": {
        "SERPER_API_KEY": "your-key",
        "ANTHROPIC_API_KEY": "your-key"
      }
    }
  }
}
```

### 使用

#### 获取新闻情绪
```python
# MCP 工具调用
result = get_news_sentiment(symbol="AAPL", max_articles=10)

# 返回:
{
    "symbol": "AAPL",
    "overall_sentiment": 0.65,  # -1 到 +1 刻度
    "sentiment_trend": "improving",  # improving/stable/deteriorating
    "article_count": 10,
    "top_headlines": [
        {
            "title": "Apple announces new iPhone...",
            "source": "TechCrunch",
            "sentiment": 0.8,
            "date": "2025-11-19"
        },
        ...
    ]
}
```

#### 获取 Twitter 情绪
```python
result = get_twitter_sentiment(symbol="TSLA")

# 返回:
{
    "symbol": "TSLA",
    "overall_sentiment": -0.3,
    "influencer_sentiment": 0.1,  # 账户 > 10K 粉丝
    "sentiment_spike": False,
    "tweet_count": 5000
}
```

#### 获取事件日历
```python
result = get_event_calendar(symbol="AAPL")

# 返回:
{
    "symbol": "AAPL",
    "earnings_date": "2025-12-15",
    "days_until_earnings": 25,
    "upcoming_economic_events": [
        {
            "event": "FOMC Meeting",
            "date": "2025-12-01",
            "impact": "high",
            "days_until": 11
        },
        ...
    ]
}
```

---

## 测试

### 运行所有测试
```bash
# 技术指标（40 个测试）
python -m pytest tests/test_technical_indicators.py -v

# 监控列表管理器（27 个测试）
python -m pytest tests/test_watchlist_manager.py -v

# 所有测试
python -m pytest tests/ -v
```

### 性能基准

来自 `tests/test_technical_indicators.py`:

```
SMA 性能: 18.7 倍加速（朴素: 1.2ms, 向量化: 0.064ms）
目标: 10 倍最小值 ✓ 通过
```

---

## 故障排除

### 问题: "指标计算数据不足"

**解决方案**: 确保 bars 数组有足够的数据点
```python
# 对于 SMA(20)，至少需要 20 根K线
bars = get_historical_bars(symbol, interval="daily", lookback_days=30)
```

### 问题: "达到变动限制"

**解决方案**: 等到下周或调整 MAX_CHURN_PER_WEEK
```python
# 检查最近变动
from skills.watchlist_manager import get_recent_churn

churn = get_recent_churn(days=7)
print(f"最近变化: {churn}/3")
```

### 问题: "超过板块限制"

**解决方案**: 跨板块分散候选池
```python
# 确保候选者跨越多个板块
candidates = [
    "AAPL",  # Technology
    "XLE",   # Energy
    "JPM",   # Financial
    "SPY"    # Broad Market
]
```

---

## 性能指标

### 技术指标
- **向量化加速**: SMA 18.7 倍（目标: 10 倍）
- **测试覆盖率**: 40 个测试，100% 通过率
- **边缘情况处理**: 空数组、NaN 值、数据不足

### 监控列表管理器
- **综合评分**: 4 因子加权平均
- **轮换效率**: 底部 20% 识别 O(n log n)
- **测试覆盖率**: 27 个测试，100% 通过率
- **板块强制**: 每个板块最多 30% 集中度

### 蜂群模板
- **策略总数**: 5（Vol Sniper、Trend Scout、Mean Reversion、Breakout Scout、Correlation Arbitrage）
- **并发执行**: 所有 5 个策略并行运行
- **优先级评分**: 6-10（更高优先级先评估）

---

## 总结

增强的蜂群智能系统提供：

1. **全面的技术分析**: 15 个向量化指标，性能提升 10 倍以上
2. **多样化策略覆盖**: 5 个并发策略，涵盖波动率、趋势、震荡、突破和统计套利
3. **智能投资组合管理**: 带板块分散化的自动监控列表轮换
4. **可选情绪集成**: 通过 MCP 进行新闻和 Twitter 情绪分析

所有增强功能均已完全测试、文档化并集成到现有的 Commander 工作流中。
