# 缠论增强策略模板

基于缠论分析原理的综合性交易策略，结合多时间周期分析和多指标确认，适用于趋势跟踪和区间交易。

## 策略参数

- **symbol_pool**: 分析标的池 {{ parameters.symbol_pool|join(', ') }}
- **lookback_days**: K线分析周期 {{ parameters.lookback_days }}天
- **pen_threshold**: 笔的最小K线数 {{ parameters.pen_threshold }}根
- **zhongshu_depth**: 中枢分析深度 {{ parameters.zhongshu_depth }}层
- **min_breakout_strength**: 最小突破强度 {{ parameters.min_breakout_strength }}%
- **volume_threshold**: 成交量确认阈值 {{ parameters.volume_threshold }}%
- **min_confidence**: 最低置信度 {{ parameters.min_confidence }}

## 缠论核心分析

### 1. 分型识别与笔的构建
```python
from skills import (
    get_multi_timeframe_data,
    identify_chanlun_fractals,
    build_pen_segments,
    analyze_pivots,
    detect_trend
)

# 获取多时间周期数据
mtf_data = get_multi_timeframe_data(
    symbols={{ parameters.symbol_pool | tojson }},
    intervals=["5min", "15min", "1h", "daily"],
    lookback_days={{ parameters.lookback_days }}
)

# 识别顶底分型（日线级别）
daily_bars = mtf_data['timeframes']['daily']['bars']
fractals = identify_chanlun_fractals(
    bars=daily_bars,
    min_strength={{ parameters.pen_threshold }}
)

# 构建笔段
pens = build_pen_segments(
    fractals=fractals,
    min_bars={{ parameters.pen_threshold }}
)

# 分析分型强弱
pivot_analysis = analyze_pivots(fractals, pens)
```

#### 分型识别标准
- **顶分型**: 连续3根K线，中间K线高点最高，两边K线高点较低
- **底分型**: 连续3根K线，中间K线最低点最低，两边K线低点较高
- **分型确认**: 需要后续K线确认分型的有效性
- **分型强度**: 基于成交量、K线实体大小等因素评估

### 2. 线段与中枢分析
```python
from skills import (
    build_segments_from_pens,
    identify_zhongshu,
    detect_breakouts,
    measure_zhongshu_range,
    calculate_pen_strength
)

# 由笔构建线段
segments = build_segments_from_pens(pens)

# 识别中枢震荡
zhongshu_list = identify_zhongshu(
    segments=segments,
    depth={{ parameters.zhongshu_depth }}
)

# 测量中枢范围
zhongshu_ranges = [measure_zhongshu_range(zh) for zh in zhongshu_list]

# 检测突破
breakout_signals = detect_breakouts(
    segments=segments,
    zhongshu=zhongshu_list,
    strength_threshold={{ parameters.min_breakout_strength }}
)

# 计算笔的强度
pen_strengths = [calculate_pen_strength(pen) for pen in pens]
```

#### 中枢分析要素
- **中枢区间**: 价格震荡的上下边界
- **中枢深度**: 中枢包含的线段数量
- **中枢级别**: 时间周期决定中枢的重要性
- **中枢突破**: 有效突破需要成交量放大确认

### 3. 多时间周期协调分析
```python
from skills import (
    synchronize_timeframes,
    analyze_multi_timeframe_alignment,
    detect_trend_consistency
)

# 多时间周期同步
synced_data = synchronize_timeframes(mtf_data)

# 分析时间周期协调性
alignment = analyze_multi_timeframe_alignment(synced_data)

# 检测趋势一致性
trend_consistency = detect_trend_consistency(synced_data)
```

#### 时间周期关系
- **日线笔**: 周线线段，月线中枢
- **周线笔**: 月线线段，季线中枢
- **共振确认**: 多个时间周期同时确认信号
- **背离警告**: 不同时间周期出现信号背离

### 4. 背驰与力度分析
```python
from skills import (
    calculate_momentum_divergence,
    analyze_pen_strength_sequence,
    measure_trend_acceleration
)

# 计算动量背驰
divergence_analysis = calculate_momentum_divergence(
    price_data=daily_bars,
    segments=segments[-5:]  # 最近5个线段
)

# 分析笔强度序列
strength_sequence = analyze_pen_strength_sequence(pens)

# 测量趋势加速度
trend_acceleration = measure_trend_acceleration(segments)
```

#### 背驰类型识别
- **顶背驰**: 价格创新高但动量指标未能创新高
- **底背驰**: 价格创新低但动量指标未能创新低
- **隐性背驰**: 价格与动量指标的斜率背离
- **多周期背驰**: 不同时间周期同时出现背驰

### 5. 多指标确认体系
```python
from skills import (
    calculate_macd,
    calculate_rsi,
    calculate_bollinger_bands,
    calculate_volume_profile,
    confirm_signals
)

# MACD趋势确认
macd_result = calculate_macd(daily_bars, fast=12, slow=26, signal=9)
macd_trend = 'UPWARD' if macd_result['dif'][-1] > macd_result['dea'][-1] else 'DOWNWARD'

# RSI动量确认
rsi_result = calculate_rsi(daily_bars, period=14)
rsi_momentum = 'BULLISH' if rsi_result[-1] > 50 else 'BEARISH'

# 布林带位置确认
bb_result = calculate_bollinger_bands(daily_bars, period=20, std_dev=2.0)
current_price = daily_bars[-1]['close']
bb_position = (current_price - bb_result['lower_band'][-1]) / (bb_result['upper_band'][-1] - bb_result['lower_band'][-1])

# 成交量分析
volume_profile = calculate_volume_profile(daily_bars)
volume_confirmation = confirm_signals(
    breakout_signals=breakout_signals,
    macd_result=macd_result,
    rsi_result=rsi_result,
    volume_profile=volume_profile,
    min_confirmation=3  # 至少3个指标确认
)
```

### 6. 综合信号生成逻辑

#### 做多信号条件
```python
def generate_bullish_signals(analysis_data):
    signals = []

    for breakout in analysis_data['breakout_signals']:
        # 中枢向上突破
        if breakout['type'] == 'UPWARD_BREAKOUT':
            # 多指标确认
            confirmations = []

            if breakout['strength'] >= {{ parameters.min_breakout_strength }}:
                confirmations.append('strong_breakout')

            if analysis_data['macd_trend'] == 'UPWARD':
                confirmations.append('macd_bullish')

            if analysis_data['volume_confirmation'] > 1.2:
                confirmations.append('volume_confirmation')

            if len(confirmations) >= 3:
                signal = {
                    "signal": "SHORT_PUT_SPREAD",
                    "target": breakout['symbol'],
                    "confidence": calculate_signal_confidence(confirmations),
                    "reasoning": f"缠论中枢上轨突破，{', '.join(confirmations)}确认",
                    "technical_context": {
                        "breakout_strength": breakout['strength'],
                        "zhongshu_range": breakout['zhongshu_range'],
                        "confirmations": confirmations
                    }
                }
                signals.append(signal)

    return signals
```

#### 做空信号条件
```python
def generate_bearish_signals(analysis_data):
    signals = []

    for breakdown in analysis_data['breakdown_signals']:
        # 中枢向下突破
        if breakdown['type'] == 'DOWNWARD_BREAKDOWN':
            # 多指标确认
            confirmations = []

            if breakdown['strength'] >= {{ parameters.min_breakout_strength }}:
                confirmations.append('strong_breakdown')

            if analysis_data['macd_trend'] == 'DOWNWARD':
                confirmations.append('macd_bearish')

            if analysis_data['volume_confirmation'] > 1.2:
                confirmations.append('volume_confirmation')

            # 背驰确认
            if analysis_data['divergence_analysis'].get('bearish_divergence', False):
                confirmations.append('bearish_divergence')

            if len(confirmations) >= 3:
                signal = {
                    "signal": "SHORT_CALL_SPREAD",
                    "target": breakdown['symbol'],
                    "confidence": calculate_signal_confidence(confirmations),
                    "reasoning": f"缠论中枢下轨突破，{', '.join(confirmations)}确认",
                    "technical_context": {
                        "breakdown_strength": breakdown['strength'],
                        "zhongshu_range": breakdown['zhongshu_range'],
                        "confirmations": confirmations
                    }
                }
                signals.append(signal)

    return signals
```

## 执行指令

```python
# 综合分析并生成交易信号
from skills import (
    generate_option_signals,
    calculate_position_size,
    risk_assessment
)

# 汇总所有分析结果
comprehensive_analysis = {
    "fractals": fractals,
    "pens": pens,
    "segments": segments,
    "zhongshu_list": zhongshu_list,
    "breakout_signals": breakout_signals,
    "macd_result": macd_result,
    "rsi_result": rsi_result,
    "bb_result": bb_result,
    "divergence_analysis": divergence_analysis,
    "trend_consistency": trend_consistency,
    "volume_profile": volume_profile
}

# 生成做多信号
bullish_signals = generate_bullish_signals(comprehensive_analysis)

# 生成做空信号
bearish_signals = generate_bearish_signals(comprehensive_analysis)

# 合并信号
all_signals = bullish_signals + bearish_signals

# 风险评估
risk_assessment_result = risk_assessment(
    all_signals=all_signals,
    portfolio_state=get_current_portfolio_state(),
    market_conditions=analyze_market_conditions()
)

# 生成期权交易信号
final_signals = []
for signal in all_signals:
    if signal['confidence'] >= {{ parameters.min_confidence }}:
        # 计算建议仓位大小
        position_size = calculate_position_size(
            signal=signal,
            account_risk_per_trade=0.02,
            max_position_size=2000
        )

        # 生成具体的期权策略
        option_strategy = generate_option_strategy(
            signal_type=signal['signal'],
            symbol=signal['target'],
            market_data=get_market_data(signal['target'])
        )

        signal['option_strategy'] = option_strategy
        signal['suggested_position_size'] = position_size
        final_signals.append(signal)

return final_signals
```

## 输出格式要求

必须返回严格遵循以下格式的JSON数组：

```json
[
  {
    "signal": "SHORT_PUT_SPREAD|SHORT_CALL_SPREAD|IRON_CONDOR|NO_TRADE",
    "target": "NVDA",
    "confidence": 0.85,
    "reasoning": "缠论分析显示30分钟级别向上突破中枢上轨$145.20，MACD金叉确认，成交量放大45%。线段力度增强，无顶背驰风险。",
    "params": {
      "legs": [
        {
          "action": "SELL",
          "contract": {
            "symbol": "NVDA",
            "expiry": "2025-12-26",
            "strike": 145,
            "right": "P"
          },
          "quantity": 1,
          "price": 6.50
        },
        {
          "action": "BUY",
          "contract": {
            "symbol": "NVDA",
            "expiry": "2025-12-26",
            "strike": 142,
            "right": "P"
          },
          "quantity": 1,
          "price": 4.80
        }
      ],
      "max_risk": 320,
      "capital_required": 400,
      "suggested_position_size": 2
    },
    "technical_context": {
      "chanlun_analysis": {
        "last_pen_direction": "UPWARD",
        "zhongshu_status": "BROKEN_UPWARD",
        "pen_strength_sequence": "INCREASING",
        "breakout_confirmation": "MULTI_INDICATOR_CONFIRMED"
      },
      "indicator_confirmation": {
        "macd_signal": "BULLISH",
        "rsi_momentum": "BULLISH",
        "volume_confirmation": true,
        "bb_position": 0.75
      },
      "risk_assessment": {
        "risk_level": "MEDIUM",
        "position_size_adjustment": false,
        "recommended_stop": "ZHONGSHU_LOW"
      }
    }
  }
]
```

## 缠论分析要点

### 关键原则
1. **级别递进**: 小级别服从大级别，线段服从笔，笔服从分型
2. **多周期共振**: 优先考虑多时间周期同时确认的信号
3. **背驰优先**: 背驰信号比普通信号具有更高优先级
4. **成交量确认**: 关键突破必须有成交量放大确认
5. **中枢守恒**: 中枢具有吸引力，价格倾向于回归中枢

### 信号强度评估
- **最强信号**: 多周期共振 + 背驰确认 + 成交量放大
- **强信号**: 单级别突破 + 多指标确认 + 成交量确认
- **中等信号**: 单级别突破 + 单一指标确认
- **弱信号**: 单级别突破但无明确确认

### 常场环境适配
- **趋势市场**: 优先跟踪趋势，减少逆向操作
- **震荡市场**: 重点关注中枢边界操作
- **高波动环境**: 提高确认要求，降低仓位规模
- **低波动环境**: 适当降低信号要求

## 市场数据

当前市场数据快照：

```json
{{ market_data|tojson(indent=2) }}
```

---
*本模板基于缠论理论的核心原理，结合现代量化分析技术，提供全面的缠论交易策略框架。*