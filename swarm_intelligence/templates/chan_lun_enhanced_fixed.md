# 缠论增强策略模板（简化版）

基于缠论分析原理的综合交易策略，使用现有的技术指标进行市场分析。

## 策略参数

- **symbol_pool**: 分析标的池 {{ parameters.symbol_pool|join(', ') }}
- **lookback_days**: K线分析周期 {{ parameters.lookback_days }}天
- **min_confidence**: 最低置信度 {{ parameters.min_confidence }}
- **risk_per_trade**: 单笔交易风险 {{ parameters.risk_per_trade|default(0.02) }}

## 技术分析

### 1. 趋势分析
```python
from skills import (
    get_multi_timeframe_data,
    safe_detect_trend,
    safe_calculate_sma,
    safe_calculate_historical_volatility
)

# 获取多时间周期数据
try:
    mtf_data = get_multi_timeframe_data(
        symbols={{ parameters.symbol_pool }},
        intervals=["daily"],
        lookback_days={{ parameters.lookback_days }}
    )

    # 趋势分析
    trend_analysis = {}
    for symbol in {{ parameters.symbol_pool | tojson }}:
        try:
            daily_bars = mtf_data.get('symbols', {}).get(symbol, {}).get('daily', {}).get('bars', [])
            if len(daily_bars) > 0:
                # 检测趋势
                trend_result = safe_detect_trend(daily_bars)

                # 计算移动平均线
                sma_short = safe_calculate_sma(daily_bars[-20:], period=10)
                sma_long = safe_calculate_sma(daily_bars[-50:], period=20)

                # 计算波动率
                volatility = safe_calculate_historical_volatility(
                    [bar['close'] for bar in daily_bars[-21:]]
                )

                trend_analysis[symbol] = {
                    'trend': trend_result.get('trend', 'UNKNOWN'),
                    'sma_short': sma_short[-1] if sma_short else None,
                    'sma_long': sma_long[-1] if sma_long else None,
                    'volatility': volatility,
                    'price': daily_bars[-1]['close']
                }
        except Exception as e:
            trend_analysis[symbol] = {'error': str(e)}

except Exception as e:
    trend_analysis = {'error': f'数据获取失败: {str(e)}'}
```

### 2. 技术指标确认
```python
from skills import (
    safe_calculate_rsi,
    safe_calculate_macd
)

# 技术指标分析
indicator_analysis = {}

for symbol in {{ parameters.symbol_pool | tojson }}:
    try:
        daily_bars = mtf_data.get('symbols', {}).get(symbol, {}).get('daily', {}).get('bars', [])
        if len(daily_bars) > 0:
            closes = [bar['close'] for bar in daily_bars]

            # RSI分析
            rsi_result = safe_calculate_rsi(closes, period=14)

            # MACD分析
            macd_result = safe_calculate_macd(closes, fast=12, slow=26, signal=9)

            indicator_analysis[symbol] = {
                'rsi': rsi_result[-1] if rsi_result else 50,
                'rsi_trend': 'OVERBOUGHT' if (rsi_result[-1] if rsi_result else 50) > 70 else 'OVERSOLD' if (rsi_result[-1] if rsi_result else 50) < 30 else 'NEUTRAL',
                'macd_signal': 'BULLISH' if macd_result.get('dif', []) and macd_result.get('dea', []) and macd_result['dif'][-1] > macd_result['dea'][-1] else 'BEARISH',
                'current_price': closes[-1]
            }
    except Exception as e:
        indicator_analysis[symbol] = {'error': str(e)}
```

### 3. 缠论简化分析
```python
# 简化的缠论概念分析
def simplified_chanlun_analysis(price_data, trend_data):
    """使用现有指标模拟缠论分析"""

    current_price = price_data[-1]['close'] if price_data else 0
    trend = trend_data.get('trend', 'UNKNOWN')

    # 模拟中枢区间（使用布林带概念）
    if len(price_data) >= 20:
        prices = [bar['close'] for bar in price_data[-20:]]
        sma = sum(prices) / len(prices)

        # 简化波动范围计算
        high = max(prices)
        low = min(prices)

        zhongshu_center = sma
        zhongshu_range = high - low
        zhongshu_upper = zhongshu_center + zhongshu_range * 0.3
        zhongshu_lower = zhongshu_center - zhongshu_range * 0.3

        # 判断价格位置
        if current_price > zhongshu_upper:
            position = 'ABOVE_ZHONGSHU'
            signal_strength = min((current_price - zhongshu_upper) / zhongshu_range, 1.0)
        elif current_price < zhongshu_lower:
            position = 'BELOW_ZHONGSHU'
            signal_strength = min((zhongshu_lower - current_price) / zhongshu_range, 1.0)
        else:
            position = 'IN_ZHONGSHU'
            signal_strength = 0.5

        return {
            'zhongshu_center': zhongshu_center,
            'zhongshu_upper': zhongshu_upper,
            'zhongshu_lower': zhongshu_lower,
            'position': position,
            'signal_strength': signal_strength,
            'trend': trend
        }

    return {'error': '数据不足'}

# 对每个标的进行简化缠论分析
chanlun_analysis = {}
for symbol in {{ parameters.symbol_pool | tojson }}:
    try:
        bars = mtf_data.get('symbols', {}).get(symbol, {}).get('daily', {}).get('bars', [])
        if len(bars) > 0:
            trend_data = trend_analysis.get(symbol, {})
            chanlun_result = simplified_chanlun_analysis(bars, trend_data)
            chanlun_analysis[symbol] = chanlun_result
    except Exception as e:
        chanlun_analysis[symbol] = {'error': str(e)}
```

### 4. 信号生成逻辑

#### 做多信号条件
```python
def generate_bullish_signals():
    signals = []

    for symbol in {{ parameters.symbol_pool | tojson }}:
        try:
            # 获取分析结果
            trend_data = trend_analysis.get(symbol, {})
            indicator_data = indicator_analysis.get(symbol, {})
            chanlun_data = chanlun_analysis.get(symbol, {})

            # 做多条件检查
            confirmations = []
            confidence_factors = []

            # 1. 趋势确认
            if trend_data.get('trend') == 'UPWARD':
                confirmations.append('uptrend')
                confidence_factors.append(0.3)

            # 2. 中枢突破确认
            if chanlun_data.get('position') == 'ABOVE_ZHONGSHU':
                confirmations.append('zhongshu_breakout')
                confidence_factors.append(0.25)

            # 3. 技术指标确认
            if indicator_data.get('macd_signal') == 'BULLISH':
                confirmations.append('macd_bullish')
                confidence_factors.append(0.2)

            if indicator_data.get('rsi_trend') in ['NEUTRAL', 'OVERSOLD']:
                confirmations.append('rsi_favorable')
                confidence_factors.append(0.15)

            # 4. 强度评估
            signal_strength = chanlun_data.get('signal_strength', 0)
            if signal_strength > 0.3:
                confirmations.append('strong_momentum')
                confidence_factors.append(0.1)

            # 计算置信度
            if confirmations:
                base_confidence = min(confidence_factors + [0.3])  # 基础置信度
                confidence = min(base_confidence * (len(confirmations) / 3.0), 0.95)

                if confidence >= {{ parameters.min_confidence }}:
                    signal = {
                        "signal": "SHORT_PUT_SPREAD",
                        "target": symbol,
                        "confidence": confidence,
                        "reasoning": f"缠论增强分析显示{', '.join(confirmations)}确认，当前价格{indicator_data.get('current_price', 'N/A')}",
                        "technical_context": {
                            "trend": trend_data.get('trend'),
                            "zhongshu_position": chanlun_data.get('position'),
                            "signal_strength": signal_strength,
                            "confirmations": confirmations
                        }
                    }
                    signals.append(signal)

        except Exception as e:
            continue

    return signals
```

#### 做空信号条件
```python
def generate_bearish_signals():
    signals = []

    for symbol in {{ parameters.symbol_pool | tojson }}:
        try:
            trend_data = trend_analysis.get(symbol, {})
            indicator_data = indicator_analysis.get(symbol, {})
            chanlun_data = chanlun_analysis.get(symbol, {})

            # 做空条件检查
            confirmations = []
            confidence_factors = []

            # 1. 趋势确认
            if trend_data.get('trend') == 'DOWNWARD':
                confirmations.append('downtrend')
                confidence_factors.append(0.3)

            # 2. 中枢下破确认
            if chanlun_data.get('position') == 'BELOW_ZHONGSHU':
                confirmations.append('zhongshu_breakdown')
                confidence_factors.append(0.25)

            # 3. 技术指标确认
            if indicator_data.get('macd_signal') == 'BEARISH':
                confirmations.append('macd_bearish')
                confidence_factors.append(0.2)

            if indicator_data.get('rsi_trend') == 'OVERBOUGHT':
                confirmations.append('rsi_overbought')
                confidence_factors.append(0.15)

            # 4. 强度评估
            signal_strength = chanlun_data.get('signal_strength', 0)
            if signal_strength > 0.3:
                confirmations.append('strong_momentum')
                confidence_factors.append(0.1)

            # 计算置信度
            if confirmations:
                base_confidence = min(confidence_factors + [0.3])
                confidence = min(base_confidence * (len(confirmations) / 3.0), 0.95)

                if confidence >= {{ parameters.min_confidence }}:
                    signal = {
                        "signal": "SHORT_CALL_SPREAD",
                        "target": symbol,
                        "confidence": confidence,
                        "reasoning": f"缠论增强分析显示{', '.join(confirmations)}确认，当前价格{indicator_data.get('current_price', 'N/A')}",
                        "technical_context": {
                            "trend": trend_data.get('trend'),
                            "zhongshu_position": chanlun_data.get('position'),
                            "signal_strength": signal_strength,
                            "confirmations": confirmations
                        }
                    }
                    signals.append(signal)

        except Exception as e:
            continue

    return signals
```

## 执行指令

```python
# 生成交易信号
try:
    bullish_signals = generate_bullish_signals()
    bearish_signals = generate_bearish_signals()

    # 合并信号
    all_signals = bullish_signals + bearish_signals

    # 限制信号数量
    if len(all_signals) > 3:
        # 按置信度排序，取前3个
        all_signals.sort(key=lambda x: x['confidence'], reverse=True)
        all_signals = all_signals[:3]

    return all_signals

except Exception as e:
    return [{"signal": "NO_TRADE", "target": "ERROR", "confidence": 0.0, "reasoning": f"策略执行出错: {str(e)}"}]
```

## 输出格式要求

必须返回严格遵循以下格式的JSON数组：

```json
[
  {
    "signal": "SHORT_PUT_SPREAD|SHORT_CALL_SPREAD|IRON_CONDOR|NO_TRADE",
    "target": "NVDA",
    "confidence": 0.85,
    "reasoning": "缠论增强分析显示中枢上轨突破，MACD金叉确认，当前价格$145.20",
    "technical_context": {
      "trend": "UPWARD",
      "zhongshu_position": "ABOVE_ZHONGSHU",
      "signal_strength": 0.65,
      "confirmations": ["uptrend", "zhongshu_breakout", "macd_bullish"]
    }
  }
]
```

## 市场数据

当前市场数据快照：

```json
{{ market_data|tojson(indent=2) }}
```

---
*本模板为缠论策略的简化实现版本，使用现有技术指标函数进行市场分析。*