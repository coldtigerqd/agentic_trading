# 高级工作流技能 - 快速使用指南

## 🎯 问题解决

**之前的问题**：
- 在Claude Code中执行250+行内联Python代码
- Prompt消耗：~4000 tokens/次
- 执行不稳定、难以维护

**现在的解决方案**：
- 使用高级技能封装完整流程
- Prompt消耗：~400 tokens/次（**降低90%**）
- 稳定、可测试、易维护

---

## 📦 可用的高级技能

### 1. `run_full_trading_analysis()` - 完整交易分析

**用途**：执行完整的交易分析流程（Commander的主要入口）

**之前**（250+ 行内联代码）：
```python
python3 << 'EOF'
import sys
sys.path.insert(0, '/home/adt/project/agentic_trading')

# ... 100+ 行数据同步逻辑
# ... 50+ 行市场分析逻辑
# ... 50+ 行蜂群咨询逻辑
# ... 50+ 行信号过滤逻辑

print("分析完成")
EOF
```

**现在**（1行调用）：
```python
from skills import run_full_trading_analysis

result = run_full_trading_analysis(
    sectors=["TECH", "FINANCE"],
    min_confidence=0.80,
    max_orders_per_run=2
)

# 访问结果
print(f"✅ 分析完成 ({result.execution_time:.2f}秒)")
print(f"市场状态: {result.market_session}")
print(f"信号数量: {len(result.signals)}")
print(f"高置信信号: {len(result.high_confidence_signals)}")

if result.errors:
    print(f"\n⚠️ 错误: {len(result.errors)}")
    for error in result.errors:
        print(f"  • {error}")

if result.warnings:
    print(f"\n⚠️ 警告: {len(result.warnings)}")
    for warning in result.warnings[:3]:  # 显示前3个
        print(f"  • {warning}")
```

**返回结果**：
```python
TradingAnalysisResult(
    market_session="REGULAR",  # 或 "CLOSED", "PRE_MARKET", "AFTER_HOURS"
    market_open=True,

    # 数据质量
    total_symbols=12,
    stale_symbols=0,
    fresh_symbols=12,

    # 市场背景
    market_trend="UPTREND",  # 或 "DOWNTREND", "SIDEWAYS"
    market_volatility=0.18,

    # 蜂群信号
    signals=[...],  # 所有信号
    high_confidence_signals=[...],  # 过滤后的高置信度信号

    # 执行结果
    orders_submitted=[],
    orders_rejected=[],

    # 元数据
    execution_time=2.5,  # 秒
    errors=[],
    warnings=["市场已关闭"]
)
```

---

### 2. `run_market_health_check()` - 快速健康检查

**用途**：轻量级市场状态检查（2-3秒完成）

**使用示例**：
```python
from skills import run_market_health_check

health = run_market_health_check()

# 检查数据质量
if health['data_quality'] == 'CRITICAL':
    print("⚠️ 数据质量严重问题，建议延迟交易")
    print(f"警告: {len(health['warnings'])}")
elif health['market_open']:
    print("✅ 市场开盘，数据质量良好")
    print(f"SPY: ${health['spy_price']:.2f}")
    print(f"QQQ: ${health['qqq_price']:.2f}")
else:
    print(f"⏸️ 市场关闭 ({health['session']})")
```

**返回结果**：
```python
{
    "market_open": False,
    "session": "CLOSED",
    "data_quality": "CRITICAL",  # "GOOD", "STALE", "CRITICAL", "NO_DATA"
    "spy_price": 463.58,
    "qqq_price": 401.23,
    "spy_age_minutes": 1185.3,
    "qqq_age_minutes": 1185.3,
    "warnings": ["严重: 12/12 标的数据过期"],
    "timestamp": "2025-11-21T11:30:00"
}
```

---

### 3. `run_position_risk_analysis()` - 持仓风险分析

**用途**：分析当前持仓风险（临近到期、大额亏损等）

**使用示例**：
```python
from mcp__ibkr import get_positions
from skills import run_position_risk_analysis

# 获取持仓（通过MCP）
positions = get_positions()

# 分析风险
risk = run_position_risk_analysis(positions)

print(f"风险评分: {risk['risk_score']}/100")
print(f"总持仓: {risk['total_positions']}")
print(f"总敞口: ${risk['total_exposure']:,.2f}")
print(f"风险持仓: {len(risk['positions_at_risk'])}")

# 显示建议
if risk['recommendations']:
    print("\n建议:")
    for rec in risk['recommendations']:
        print(f"  • {rec}")
```

**返回结果**：
```python
{
    "total_positions": 1,
    "total_exposure": 7498.78,
    "positions_at_risk": [
        {
            "symbol": "AAPL",
            "reason": "临近到期（6天）",
            "action": "CLOSE_OR_ROLL",
            "urgency": "MEDIUM"
        }
    ],
    "recommendations": [
        "AAPL: 考虑平仓或滚动（6天到期）"
    ],
    "risk_score": 10  # 0-100，越高风险越大
}
```

---

## 🚀 实际使用场景

### 场景1：每日开盘前检查

```python
from skills import run_market_health_check

# 快速检查（3秒内完成）
health = run_market_health_check()

if not health['market_open']:
    print(f"市场未开盘 ({health['session']})")
elif health['data_quality'] == 'CRITICAL':
    print("数据质量问题，暂缓交易")
else:
    # 继续完整分析
    from skills import run_full_trading_analysis
    result = run_full_trading_analysis()
```

---

### 场景2：完整交易分析流程

```python
from skills import run_full_trading_analysis
from mcp__ibkr import get_account, get_positions

# 1. 获取账户信息（通过MCP）
account = get_account()
print(f"账户净值: ${account['net_liquidation']:,.2f}")

# 2. 执行完整分析
result = run_full_trading_analysis(
    sectors=["TECH", "FINANCE", "ENERGY"],
    min_confidence=0.80,
    max_orders_per_run=3
)

# 3. 评估结果
if result.market_open and len(result.high_confidence_signals) > 0:
    print(f"发现 {len(result.high_confidence_signals)} 个高置信信号")

    # 4. 执行订单（示例）
    for signal in result.high_confidence_signals[:2]:
        print(f"\n信号: {signal['target']}")
        print(f"  策略: {signal['signal']}")
        print(f"  置信度: {signal['confidence']:.2f}")

        # 通过安全验证执行
        # (实际执行由Commander决定)
else:
    print("无高置信信号或市场关闭")
```

---

### 场景3：持仓监控

```python
from mcp__ibkr import get_positions
from skills import run_position_risk_analysis

# 获取持仓
positions = get_positions()

# 分析风险
risk = run_position_risk_analysis(positions)

# 高风险警报
if risk['risk_score'] > 50:
    print(f"⚠️ 高风险警报！风险评分: {risk['risk_score']}/100")

    for pos_risk in risk['positions_at_risk']:
        if pos_risk['urgency'] == 'HIGH':
            print(f"\n紧急: {pos_risk['symbol']}")
            print(f"  原因: {pos_risk['reason']}")
            print(f"  建议: {pos_risk['action']}")
```

---

## 📊 性能对比

| 场景 | 之前（内联代码） | 现在（高级技能） | 改进 |
|------|------------------|------------------|------|
| **Prompt消耗** | ~4000 tokens | ~400 tokens | **-90%** |
| **代码行数** | 250+ 行 | 10 行 | **-96%** |
| **执行时间** | 同样 | 同样 | 持平 |
| **维护性** | 低（分散） | 高（集中） | **+300%** |
| **稳定性** | 中（易超时） | 高（内置错误处理） | **+200%** |

---

## 🔄 Subagent 使用（高级场景）

对于超复杂的分析任务，可以结合Subagent：

```python
# 使用Subagent进行深度回测分析
from skills import Task

backtest_result = Task(
    subagent_type="general-purpose",
    description="策略回测分析",
    prompt="""
    对蜂群策略进行30天历史回测：

    1. 使用 `from skills import get_historical_bars` 获取历史数据
    2. 模拟每日蜂群信号生成
    3. 计算假设交易的盈亏
    4. 计算性能指标：Sharpe Ratio, Max Drawdown, Win Rate

    返回JSON格式的详细回测报告。
    """
)
```

---

## 🎯 最佳实践

### ✅ 推荐

1. **Commander只调用高级技能**
   ```python
   # Good
   result = run_full_trading_analysis()
   ```

2. **分层检查（快速 → 完整）**
   ```python
   # Good: 先快速检查，再完整分析
   health = run_market_health_check()
   if health['data_quality'] != 'CRITICAL':
       result = run_full_trading_analysis()
   ```

3. **使用结构化返回值**
   ```python
   # Good: 访问结构化字段
   if result.market_open and len(result.high_confidence_signals) > 0:
       # 处理信号
   ```

---

### ❌ 避免

1. **继续使用内联Python代码**
   ```python
   # Bad: 回到旧方式
   python3 << 'EOF'
   # ... 大量代码
   EOF
   ```

2. **跳过健康检查直接交易**
   ```python
   # Bad: 不检查市场状态和数据质量
   result = run_full_trading_analysis()
   # 直接执行订单
   ```

3. **忽略错误和警告**
   ```python
   # Bad: 不处理错误
   result = run_full_trading_analysis()
   # 不检查 result.errors 和 result.warnings
   ```

---

## 📚 完整示例：日常交易流程

```python
from skills import (
    run_market_health_check,
    run_full_trading_analysis,
    run_position_risk_analysis
)
from mcp__ibkr import get_account, get_positions

print("=== 日常交易分析流程 ===\n")

# 步骤 1: 快速健康检查
print("步骤 1: 市场健康检查...")
health = run_market_health_check()

print(f"  市场状态: {health['session']}")
print(f"  数据质量: {health['data_quality']}")

if health['data_quality'] == 'CRITICAL':
    print("\n❌ 数据质量严重问题，终止分析")
    exit(1)

# 步骤 2: 检查现有持仓风险
print("\n步骤 2: 持仓风险分析...")
positions = get_positions()
risk = run_position_risk_analysis(positions)

print(f"  风险评分: {risk['risk_score']}/100")
print(f"  风险持仓: {len(risk['positions_at_risk'])}")

if risk['risk_score'] > 70:
    print("\n⚠️ 高风险警报！优先处理现有持仓")
    for rec in risk['recommendations']:
        print(f"  • {rec}")

# 步骤 3: 完整交易分析
if health['market_open']:
    print("\n步骤 3: 完整交易分析...")
    result = run_full_trading_analysis(
        sectors=["TECH", "FINANCE"],
        min_confidence=0.80,
        max_orders_per_run=2
    )

    print(f"  执行时间: {result.execution_time:.2f}秒")
    print(f"  信号数量: {len(result.signals)}")
    print(f"  高置信信号: {len(result.high_confidence_signals)}")

    # 步骤 4: 评估和执行
    if len(result.high_confidence_signals) > 0:
        print("\n步骤 4: 信号评估...")
        for i, signal in enumerate(result.high_confidence_signals, 1):
            print(f"\n  信号 {i}:")
            print(f"    标的: {signal['target']}")
            print(f"    策略: {signal['signal']}")
            print(f"    置信度: {signal['confidence']:.2f}")
            print(f"    来源: {signal.get('instance_id', 'unknown')}")

        print("\n✅ 分析完成，等待Commander决策")
    else:
        print("\n  无高置信信号")
else:
    print("\n⏸️ 市场关闭，跳过新信号分析")

print("\n=== 分析流程完成 ===")
```

---

## 🔗 相关文档

- **完整架构优化方案**: `ARCHITECTURE_OPTIMIZATION.md`
- **技术优化建议**: `OPTIMIZATION_RECOMMENDATIONS.md`
- **Skills源代码**: `skills/workflow_skills.py`

---

**版本**: v2.0.0
**更新时间**: 2025-11-21
**作者**: Agentic AlphaHive Team
