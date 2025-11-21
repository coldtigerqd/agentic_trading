# JSON输出格式要求

## 必须返回的JSON格式

您必须严格按照以下JSON格式返回分析结果，不要添加任何解释性文字：

```json
{
  "signal": "信号类型",
  "target": "目标标的代码",
  "confidence": 0.75,
  "reasoning": "详细的推理说明",
  "params": {
    "参数名": "参数值"
  }
}
```

## 信号类型选项

必须使用以下标准信号类型之一：
- "NO_TRADE" - 不进行交易
- "SHORT_PUT_SPREAD" - 看跌价差（卖出看跌期权价差）
- "SHORT_CALL_SPREAD" - 看涨价差（卖出看涨期权价差）
- "IRON_CONDOR" - 铁鹰策略
- "CREDIT_SPREAD" - 信用价差
- "LONG_CALL" - 买入看涨期权
- "LONG_PUT" - 买入看跌期权

## 置信度要求

- 必须是0.0到1.0之间的数字
- 推荐使用最低0.70的置信度阈值
- 低于0.70的信号将被系统忽略

## 示例输出

### 示例1：有交易信号
```json
{
  "signal": "SHORT_PUT_SPREAD",
  "target": "AAPL",
  "confidence": 0.82,
  "reasoning": "IV rank达到85%，股价接近支撑位，技术指标显示超卖状态",
  "params": {
    "strike_short": 175,
    "strike_long": 170,
    "expiry": "20241220"
  }
}
```

### 示例2：无交易信号
```json
{
  "signal": "NO_TRADE",
  "target": "",
  "confidence": 0.0,
  "reasoning": "市场趋势不明，缺乏明确的交易机会",
  "params": {}
}
```

**重要提醒**：只返回JSON格式的数据，不要包含任何其他文字、解释或Markdown格式！