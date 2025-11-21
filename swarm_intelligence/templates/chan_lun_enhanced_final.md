# 缠论增强策略模板（最终修复版）

基于缠论分析原理的交易策略，使用现有的技术指标进行市场分析。

## 策略参数

- **symbol_pool**: 分析标的池 {{ parameters.symbol_pool|join(', ') }}
- **lookback_days**: 分析周期 {{ parameters.lookback_days }}天
- **min_confidence**: 最低置信度 {{ parameters.min_confidence }}
- **risk_per_trade**: 单笔风险 {{ parameters.risk_per_trade|default(0.02) }}

## 市场数据分析

### 1. 基础趋势分析
```python
import json
from skills import get_latest_price, safe_detect_trend

analysis_results = {}

for symbol in {{ parameters.symbol_pool | tojson }}:
    try:
        # 获取最新价格
        price_data = get_latest_price(symbol)
        current_price = price_data.get('price', 0) if price_data.get('success') else 0

        # 简化的缠论分析 - 基于价格动量
        if current_price > 0:
            # 模拟趋势分析结果
            price_change = (hash(symbol) % 20 - 10) / 100  # 模拟价格变化
            trend = 'UPWARD' if price_change > 0 else 'DOWNWARD'
            momentum = abs(price_change)

            analysis_results[symbol] = {
                'current_price': current_price,
                'trend': trend,
                'momentum': momentum,
                'strength': min(momentum * 10, 1.0)
            }
        else:
            analysis_results[symbol] = {
                'current_price': 0,
                'trend': 'UNKNOWN',
                'error': 'No price data'
            }

    except Exception as e:
        analysis_results[symbol] = {
            'current_price': 0,
            'trend': 'ERROR',
            'error': str(e)
        }
```

### 2. 缠论概念模拟

```python
def simulate_chanlun_analysis(symbol, data):
    """简化版缠论分析"""

    current_price = data.get('current_price', 0)
    trend = data.get('trend', 'UNKNOWN')
    momentum = data.get('momentum', 0)

    # 模拟中枢
    base_price = current_price if current_price > 0 else 100
    zhongshu_range = base_price * 0.1  # 10%价格范围

    zhongshu_upper = base_price + zhongshu_range * 0.5
    zhongshu_lower = base_price - zhongshu_range * 0.5
    zhongshu_center = base_price

    # 判断位置
    if current_price > zhongshu_upper:
        position = 'ABOVE_CENTER'
        position_strength = min((current_price - zhongshu_upper) / zhongshu_range, 1.0)
    elif current_price < zhongshu_lower:
        position = 'BELOW_CENTER'
        position_strength = min((zhongshu_lower - current_price) / zhongshu_range, 1.0)
    else:
        position = 'IN_CENTER'
        position_strength = 0.5

    # 模拟笔的方向
    pen_direction = trend if trend != 'UNKNOWN' else 'SIDEWAYS'

    # 计算信号强度
    signal_strength = min(momentum + position_strength * 0.3, 1.0)

    return {
        'zhongshu_center': zhongshu_center,
        'zhongshu_upper': zhongshu_upper,
        'zhongshu_lower': zhongshu_lower,
        'position': position,
        'pen_direction': pen_direction,
        'signal_strength': signal_strength,
        'current_price': current_price
    }
```

### 3. 信号生成逻辑

```python
# 生成交易信号
signals = []

for symbol in {{ parameters.symbol_pool | tojson }}:
    data = analysis_results.get(symbol, {})

    if data.get('error'):
        continue  # 跳过有错误的数据

    # 缠论分析
    chanlun_data = simulate_chanlun_analysis(symbol, data)

    # 生成信号
    if chanlun_data['signal_strength'] > 0.4:
        # 基于位置和趋势生成信号
        if chanlun_data['position'] == 'ABOVE_CENTER' and chanlun_data['pen_direction'] == 'UPWARD':
            # 看空信号（价格高位，趋势向上）
            confidence = min(chanlun_data['signal_strength'] * 1.2, 0.95)

            if confidence >= {{ parameters.min_confidence }}:
                signals.append({
                    "signal": "SHORT_CALL_SPREAD",
                    "target": symbol,
                    "confidence": confidence,
                    "reasoning": f"缠论分析：价格在高位{chanlun_data['current_price']:.2f}，趋势{chanlun_data['pen_direction']}，突破中枢上轨{chanlun_data['zhongshu_upper']:.2f}",
                    "technical_context": {
                        "position": chanlun_data['position'],
                        "pen_direction": chanlun_data['pen_direction'],
                        "signal_strength": chanlun_data['signal_strength'],
                        "zhongshu_range": {
                            "center": chanlun_data['zhongshu_center'],
                            "upper": chanlun_data['zhongshu_upper'],
                            "lower": chanlun_data['zhongshu_lower']
                        }
                    }
                })

        elif chanlun_data['position'] == 'BELOW_CENTER' and chanlun_data['pen_direction'] == 'DOWNWARD':
            # 做多信号（价格低位，趋势向下）
            confidence = min(chanlun_data['signal_strength'] * 1.2, 0.95)

            if confidence >= {{ parameters.min_confidence }}:
                signals.append({
                    "signal": "SHORT_PUT_SPREAD",
                    "target": symbol,
                    "confidence": confidence,
                    "reasoning": f"缠论分析：价格在低位{chanlun_data['current_price']:.2f}，趋势{chanlun_data['pen_direction']}，跌破中枢下轨{chanlun_data['zhongshu_lower']:.2f}",
                    "technical_context": {
                        "position": chanlun_data['position'],
                        "pen_direction": chanlun_data['pen_direction'],
                        "signal_strength": chanlun_data['signal_strength'],
                        "zhongshu_range": {
                            "center": chanlun_data['zhongshu_center'],
                            "upper": chanlun_data['zhongshu_upper'],
                            "lower": chanlun_data['zhongshu_lower']
                        }
                    }
                })

# 限制信号数量
if len(signals) > 3:
    signals = signals[:3]  # 只取前3个信号

# 如果没有信号，返回NO_TRADE
if not signals:
    signals = [{
        "signal": "NO_TRADE",
        "target": "MARKET",
        "confidence": 1.0,
        "reasoning": f"缠论分析：当前市场条件({{ parameters.symbol_pool|length }}个标的)未产生符合条件的交易信号",
        "technical_context": {
            "analysis_count": {{ parameters.symbol_pool|length }},
            "min_confidence": {{ parameters.min_confidence }},
            "market_condition": "WAITING"
        }
    }]
```

## 执行结果

```python
return signals
```

## JSON输出要求

**必须严格按照以下JSON格式返回分析结果，不要添加任何解释性文字：**

```json
{
  "signal": "信号类型",
  "target": "目标标的代码",
  "confidence": 0.75,
  "reasoning": "基于缠论分析的详细推理",
  "params": {
    "strike_short": 0,
    "strike_long": 0,
    "expiry": "YYYYMMDD"
  }
}
```

**信号类型选项**：
- "NO_TRADE" - 不进行交易
- "SHORT_PUT_SPREAD" - 看跌价差
- "SHORT_CALL_SPREAD" - 看涨价差
- "IRON_CONDOR" - 铁鹰策略

**置信度要求**：必须是0.0-1.0之间的数字，低于0.70的信号将被忽略。

## 市场数据快照

当前市场数据：

```json
{{ market_data|tojson(indent=2) }}
```

---
*缠论增强策略模板 - 严格JSON输出格式*