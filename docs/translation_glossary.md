# Translation Glossary (翻译术语表)

**Version**: 1.0
**Last Updated**: 2025-11-21
**Purpose**: Standardized Chinese translations for Agentic AlphaHive Runtime localization

---

## Usage Guidelines (使用指南)

### Translation Categories (翻译分类)

1. **Domain Terms** (领域术语) - **Keep English**
   - Financial/trading terminology without standard Chinese equivalents
   - Technical indicators and data formats
   - Examples: PUT_SPREAD, OHLC, MACD, RSI, VIX, IBKR

2. **System Concepts** (系统概念) - **Translate to Chinese**
   - Core system components and architecture terms
   - Workflow states and processes
   - Examples: Commander → 指挥官, Swarm → 蜂群

3. **User Messages** (用户消息) - **Full Chinese**
   - Error messages, status updates, log output
   - Instructions and guidance text
   - Examples: "Data sync complete" → "数据同步完成"

### Formatting Rules (格式规则)

- **Code Elements**: Keep in English (variable names, function names, class names)
- **Jinja2 Variables**: Never translate (e.g., `{{ symbol_pool }}` stays as-is)
- **Error Codes**: Always include English code in parentheses (e.g., `交易风险超限 (RISK_EXCEEDED)`)
- **Technical Terms in Context**: "PUT_SPREAD 策略" (English term + Chinese context)

---

## Core System Components (核心系统组件)

| English | Chinese | Notes |
|---------|---------|-------|
| Commander | 指挥官 | Central orchestrator agent |
| Alpha Swarm | Alpha蜂群 | Keep "Alpha" in English |
| Swarm Intelligence | 蜂群智能 | |
| Agent | 智能体 | Can also use "Agent" in technical contexts |
| Sub-agent | 子智能体 | |
| Skill | 技能 | Python functions registered to Claude |
| MCP Server | MCP服务器 | Keep "MCP" acronym |
| Runtime | 运行时 | Or "运行时环境" for clarity |
| Watchdog | 看门狗 | Safety monitoring process |
| Safety Layer | 安全层 | Hard-coded validation layer |
| Execution Gate | 执行门 | Order validation module |

---

## Trading Concepts (交易概念)

| English | Chinese | Notes |
|---------|---------|-------|
| Signal | 信号 | Trading signal from swarm |
| Strategy | 策略 | Trading strategy |
| Trade | 交易 | Individual trade operation |
| Order | 订单 | Order submitted to broker |
| Position | 持仓 | Open position in portfolio |
| Portfolio | 投资组合 | |
| Risk | 风险 | |
| Capital | 资金 | Or "资本" |
| Concentration | 集中度 | Position concentration limit |
| Drawdown | 回撤 | Portfolio drawdown |
| Circuit Breaker | 熔断机制 | Safety mechanism |
| Profit | 利润 / 盈利 | |
| Loss | 亏损 | |
| Volatility | 波动率 | Market volatility |
| Liquidity | 流动性 | |

---

## Workflow States (工作流状态)

| English | Chinese | Notes |
|---------|---------|-------|
| SENSE | 感知 | Market sensing phase |
| THINK | 思考 | Analysis phase |
| DECIDE | 决策 | Decision making phase |
| ACT | 行动 | Execution phase |
| Initialize | 初始化 | |
| Execute | 执行 | |
| Validate | 验证 | |
| Submit | 提交 | |
| Approve | 批准 | |
| Reject | 拒绝 | |
| Abort | 中止 | |
| Complete | 完成 | |
| Fail | 失败 | |

---

## Data & Market Terms (数据与市场术语)

| English | Chinese | Notes |
|---------|---------|-------|
| Market Data | 市场数据 | |
| Fresh Data | 新鲜数据 | Recently fetched data |
| Stale Data | 过期数据 | Outdated data |
| Snapshot | 快照 | Point-in-time data capture |
| Historical Data | 历史数据 | |
| Real-time Data | 实时数据 | |
| Bar | K线 / 数据条 | OHLC bar |
| Quote | 报价 | Bid/ask quote |
| Trade (market event) | 成交 | Executed trade on exchange |
| Price | 价格 | |
| Volume | 成交量 | |
| Bid | 买价 / 出价 | |
| Ask | 卖价 / 要价 | |
| Spread | 价差 | Bid-ask spread |
| Tick | 跳动 / Tick数据 | Market tick data |
| Timeframe | 时间周期 | e.g., 5min, 1h, daily |
| Interval | 间隔 / 周期 | Data interval |
| Watchlist | 监控列表 / 自选股 | |
| Symbol | 标的 / 代码 | Ticker symbol |
| Underlying | 标的资产 | Underlying asset |
| Expiration / Expiry | 到期日 | Options expiration |
| Strike | 行权价 | Options strike price |
| Market Open | 开盘 / 市场开放 | |
| Market Close | 收盘 / 市场关闭 | |
| Session | 交易时段 | Trading session |

---

## Technical Indicators (技术指标)

**Note**: Keep all indicator abbreviations in English

| English | Chinese | Notes |
|---------|---------|-------|
| MACD | MACD | Keep abbreviation |
| RSI | RSI | Relative Strength Index |
| SMA | SMA | Simple Moving Average, or "简单移动平均线" |
| EMA | EMA | Exponential Moving Average, or "指数移动平均线" |
| Bollinger Bands | 布林带 | |
| ATR | ATR | Average True Range |
| ADX | ADX | Average Directional Index |
| VWAP | VWAP | Volume Weighted Average Price |
| Trend | 趋势 | |
| Momentum | 动量 | |
| Breakout | 突破 | |
| Pullback | 回调 | |
| Reversal | 反转 | |

---

## Options Terminology (期权术语)

**Note**: Keep strategy names in English

| English | Chinese | Notes |
|---------|---------|-------|
| Option | 期权 | |
| Call Option | 看涨期权 / Call | |
| Put Option | 看跌期权 / Put | |
| Strike Price | 行权价 | |
| Premium | 权利金 | Option premium |
| PUT_SPREAD | PUT_SPREAD | Keep English |
| CALL_SPREAD | CALL_SPREAD | Keep English |
| IRON_CONDOR | IRON_CONDOR | Keep English |
| Long | 做多 / 买入 | |
| Short | 做空 / 卖出 | |
| Buy | 买入 | |
| Sell | 卖出 | |
| Contract | 合约 | Options contract |

---

## Safety & Validation (安全与验证)

| English | Chinese | Notes |
|---------|---------|-------|
| Safety Validator | 安全验证器 | |
| Validation | 验证 | |
| Rejection | 拒绝 | Order rejection |
| Approval | 批准 | |
| Limit | 限额 / 限制 | |
| Threshold | 阈值 | |
| Max Trade Risk | 最大交易风险 | |
| Max Trade Capital | 最大交易资金 | |
| Daily Loss Limit | 每日亏损限额 | |
| Concentration Limit | 集中度限额 | |
| Error | 错误 | |
| Warning | 警告 | |
| Exception | 异常 | |
| Constraint | 约束 | |
| Check | 检查 | |

---

## Data Quality (数据质量)

| English | Chinese | Notes |
|---------|---------|-------|
| Data Quality | 数据质量 | |
| Validation | 验证 | |
| Completeness | 完整性 | |
| Accuracy | 准确性 | |
| Freshness | 新鲜度 | |
| Gap | 缺口 / 间隙 | Data gap |
| Missing Data | 数据缺失 | |
| Corrupted Data | 损坏数据 | |
| Duplicate | 重复 | |
| Inconsistent | 不一致 | |
| Issue | 问题 | |
| Critical | 严重 | Severity level |
| High | 高 | Severity level |
| Medium | 中 | Severity level |
| Low | 低 | Severity level |

---

## System Operations (系统操作)

| English | Chinese | Notes |
|---------|---------|-------|
| Sync | 同步 | Data synchronization |
| Fetch | 获取 / 拉取 | Fetch data |
| Query | 查询 | |
| Cache | 缓存 | |
| Log | 日志 | |
| Snapshot | 快照 | |
| Backfill | 回填 | Historical data backfill |
| Update | 更新 | |
| Refresh | 刷新 | |
| Load | 加载 | |
| Process | 处理 | |
| Parse | 解析 | |
| Render | 渲染 | Template rendering |
| Invoke | 调用 | Function invocation |
| Trigger | 触发 | |
| Monitor | 监控 | |
| Track | 跟踪 | |

---

## Status & States (状态)

| English | Chinese | Notes |
|---------|---------|-------|
| Success | 成功 | |
| Failed | 失败 | |
| Pending | 待处理 / 等待中 | |
| In Progress | 进行中 | |
| Completed | 已完成 | |
| Cancelled | 已取消 | |
| Rejected | 已拒绝 | |
| Approved | 已批准 | |
| Active | 活跃 / 激活 | |
| Inactive | 非活跃 / 停用 | |
| Available | 可用 | |
| Unavailable | 不可用 | |
| Ready | 就绪 | |
| Busy | 繁忙 | |
| Idle | 空闲 | |

---

## Error Codes (错误代码)

**Note**: Always include English error code in parentheses

| Error Code | Chinese Message |
|------------|-----------------|
| RISK_EXCEEDED | 交易风险超限 |
| CAPITAL_EXCEEDED | 资金需求超限 |
| CONCENTRATION_EXCEEDED | 仓位集中度超限 |
| DRAWDOWN_TRIGGERED | 触发回撤熔断 |
| DAILY_LOSS_LIMIT | 触发每日亏损限额 |
| MARKET_CLOSED | 市场已关闭 |
| STALE_DATA | 数据过期 |
| MISSING_DATA | 数据缺失 |
| INVALID_STRIKE | 无效行权价 |
| INVALID_EXPIRY | 无效到期日 |
| MISSING_FIELD | 缺少字段 |
| INVALID_PARAMETER | 无效参数 |
| CONNECTION_ERROR | 连接错误 |
| TIMEOUT | 超时 |
| VALIDATION_FAILED | 验证失败 |

**Format**: `{中文描述} (ERROR_CODE)`
**Example**: `交易风险 $600 超过限额 $500 (RISK_EXCEEDED)`

---

## Common Phrases (常用短语)

| English | Chinese |
|---------|---------|
| Loading... | 加载中... |
| Processing... | 处理中... |
| Please wait | 请稍候 |
| Sync complete | 同步完成 |
| Already cached | 已缓存 |
| Not found | 未找到 |
| Connection failed | 连接失败 |
| Invalid input | 输入无效 |
| Required field | 必填字段 |
| Optional field | 可选字段 |
| Recommended | 建议 |
| Warning | 警告 |
| Error occurred | 发生错误 |
| Operation failed | 操作失败 |
| Operation successful | 操作成功 |

---

## Emojis & Symbols (表情符号)

Keep emojis consistent across translations:

| Symbol | Usage |
|--------|-------|
| ✅ | Success, completed |
| ❌ | Error, failed |
| ⚠️ | Warning, caution |
| ⏭️ | Skipped |
| 📡 | Syncing, fetching data |
| 📊 | Data, statistics |
| 📈 | Market trends |
| 🛡️ | Safety, protection |
| 🔍 | Search, inspect |
| ⏸️ | Paused |
| 🤖 | AI/bot operation |

---

## Translation Examples (翻译示例)

### Good Examples (正确示例)

```python
# ✅ Correct
print(f"📡 正在同步 {count} 个标的...")
logger.error(f"获取数据失败 {symbol}: {e}")
error = "交易风险 $600 超过限额 $500 (RISK_EXCEEDED)"
```

### Bad Examples (错误示例)

```python
# ❌ Wrong - translated variable names
print(f"📡 正在同步 {数量} 个标的...")  # Don't translate 'count'

# ❌ Wrong - missing error code
error = "交易风险超限"  # Missing (RISK_EXCEEDED)

# ❌ Wrong - translated Jinja2 variable
{{ 符号池 }}  # Should be {{ symbol_pool }}
```

---

## Special Cases (特殊情况)

### 1. Bilingual Terms
Some contexts require both English and Chinese:

```
指挥官 (Commander)  # First mention in document
PUT_SPREAD 策略     # English term + Chinese context
```

### 2. Code in Markdown
Keep code blocks entirely in English:

```python
# ✅ Comments can be Chinese
def sync_data():
    """同步市场数据"""  # Docstring in Chinese
    print("正在同步...")  # User message in Chinese
    result = fetch_data()  # Code stays English
```

### 3. Mixed Documentation
For bilingual docs (like README):

```markdown
# System Overview | 系统概述

[English section]

---

## 中文说明

[Chinese section]
```

---

## Maintenance Notes (维护说明)

### Adding New Terms
1. Determine category (Domain/System/User)
2. Check for conflicts with existing translations
3. Add to appropriate section with notes
4. Update version number

### Review Checklist
- [ ] No conflicting translations
- [ ] All technical terms properly categorized
- [ ] Examples provided for ambiguous cases
- [ ] Error codes follow format standard

### Version History
- **v1.0** (2025-11-21): Initial glossary for localization project

---

**END OF GLOSSARY**
