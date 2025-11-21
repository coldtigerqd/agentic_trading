# 指挥官代码示例参考

本文档包含 Agentic AlphaHive 指挥官系统的所有代码示例。这些示例仅供**技术参考、调试和学习**使用。

> **重要提示**：在实际运行中，指挥官应该使用高级技能封装的接口，而不是直接执行这些代码。

---

## 目录

1. [完整交易分析流程](#完整交易分析流程)
2. [市场健康检查](#市场健康检查)
3. [持仓风险分析](#持仓风险分析)
4. [订单执行决策](#订单执行决策)
5. [每日开盘前流程](#每日开盘前流程)
6. [最佳实践对比](#最佳实践对比)

---

## 完整交易分析流程

### 基本用法

```python
from skills import run_full_trading_analysis
from mcp__ibkr import get_account, get_positions

# 1. 获取账户信息
account = get_account()
print(f"账户净值: ${account['net_liquidation']:,.2f}")

# 2. 执行完整分析（封装所有步骤）
result = run_full_trading_analysis(
    sectors=["TECH", "FINANCE"],
    min_confidence=0.80,
    max_orders_per_run=2
)

# 3. 评估结果
print(f"市场状态: {result.market_session}")
print(f"信号数量: {len(result.signals)}")
print(f"高置信信号: {len(result.high_confidence_signals)}")

# 4. 检查警告和错误
if result.errors:
    print(f"⚠️ 错误: {len(result.errors)}")
    for error in result.errors:
        print(f"  • {error}")

if result.warnings:
    print(f"⚠️ 警告: {len(result.warnings)}")
    for warning in result.warnings[:3]:
        print(f"  • {warning}")
```

### run_full_trading_analysis() 自动执行的步骤

1. ✅ 市场状态检查
2. ✅ 数据新鲜度检查
3. ✅ 数据同步（如果需要）
4. ✅ 市场背景分析（SPY趋势和波动率）
5. ✅ 蜂群智能咨询
6. ✅ 信号过滤（按置信度）
7. ✅ 完整错误处理和降级逻辑

---

## 市场健康检查

### 快速健康检查

在执行完整分析前，先快速检查市场状态和数据质量：

```python
from skills import run_market_health_check

health = run_market_health_check()

print(f"市场状态: {health['session']}")
print(f"数据质量: {health['data_quality']}")

if health['data_quality'] == 'CRITICAL':
    print("⚠️ 数据质量严重问题，建议延迟交易")
elif health['market_open']:
    print("✅ 市场开盘，数据质量良好")
    # 继续完整分析
else:
    print(f"⏸️ 市场关闭 ({health['session']})")
```

### 数据质量检查逻辑

```python
health = run_market_health_check()

if health['data_quality'] == 'CRITICAL':
    # 数据过期，不要进行蜂群咨询
    print("数据质量问题，延迟交易")
else:
    # 数据良好，继续分析
    result = run_full_trading_analysis()
```

---

## 持仓风险分析

### 基本用法

定期检查现有持仓的风险：

```python
from mcp__ibkr import get_positions
from skills import run_position_risk_analysis

positions = get_positions()
risk = run_position_risk_analysis(positions)

print(f"风险评分: {risk['risk_score']}/100")
print(f"总持仓: {risk['total_positions']}")
print(f"风险持仓: {len(risk['positions_at_risk'])}")

# 显示建议
if risk['recommendations']:
    print("\n建议:")
    for rec in risk['recommendations']:
        print(f"  • {rec}")

# 高风险警报
if risk['risk_score'] > 70:
    print("\n⚠️ 高风险警报！优先处理现有持仓")
```

---

## 订单执行决策

### 完整订单执行流程

```python
from skills import place_order_with_guard, kelly_criterion

# 评估高置信信号
for signal in result.high_confidence_signals:

    # 1. 计算仓位大小（Kelly Criterion）
    position_size = kelly_criterion(
        win_prob=signal['confidence'],
        win_amount=estimate_profit(signal),
        loss_amount=estimate_loss(signal),
        bankroll=account['net_liquidation'],
        fraction=0.25  # 保守的四分之一Kelly
    )

    if position_size < 100:
        print(f"跳过 {signal['target']}: 仓位太小 (${position_size})")
        continue

    # 2. 检查集中度
    if check_concentration_limit(signal['target'], position_size):

        # 3. 通过安全验证提交订单
        result = place_order_with_guard(
            symbol=signal['target'],
            strategy=signal['signal'],
            legs=signal.get('legs', []),
            max_risk=signal.get('max_risk', 100),
            capital_required=signal.get('capital_required', 500),
            metadata={
                'confidence': signal['confidence'],
                'source': signal.get('instance_id'),
                'reasoning': signal.get('reasoning', '')
            }
        )

        if result.success:
            print(f"✅ 订单已提交: {signal['target']} {signal['signal']}")
            print(f"   交易ID: {result.trade_id}")
        else:
            print(f"❌ 订单被拒绝: {result.error}")
            # 安全层拒绝是正常的，说明限额保护生效
```

---

## 每日开盘前流程

### 完整的日常交易分析流程

```python
from skills import run_market_health_check, run_full_trading_analysis, run_position_risk_analysis
from mcp__ibkr import get_account, get_positions

print("=== 日常交易分析流程 ===\n")

# 步骤 1: 快速健康检查
health = run_market_health_check()

if health['data_quality'] == 'CRITICAL':
    print("❌ 数据质量严重问题，终止分析")
    exit(1)

# 步骤 2: 检查现有持仓风险
positions = get_positions()
risk = run_position_risk_analysis(positions)

if risk['risk_score'] > 70:
    print("⚠️ 高风险警报！优先处理现有持仓")
    for rec in risk['recommendations']:
        print(f"  • {rec}")

# 步骤 3: 完整交易分析
if health['market_open']:
    result = run_full_trading_analysis(
        sectors=["TECH", "FINANCE"],
        min_confidence=0.80,
        max_orders_per_run=2
    )

    if len(result.high_confidence_signals) > 0:
        print(f"\n发现 {len(result.high_confidence_signals)} 个高置信信号")

        for signal in result.high_confidence_signals:
            print(f"\n信号: {signal['target']}")
            print(f"  策略: {signal['signal']}")
            print(f"  置信度: {signal['confidence']:.2f}")
            print(f"  来源: {signal.get('instance_id', 'unknown')}")
else:
    print("⏸️ 市场关闭，跳过新信号分析")
```

---

## 最佳实践对比

### ✅ 推荐：使用高级技能

```python
# Good: 使用封装的技能
result = run_full_trading_analysis()
health = run_market_health_check()
```

### ❌ 避免：内联Python代码

```python
# Bad: 避免在Commander中执行大量内联代码
python3 << 'EOF'
# ... 100+ 行代码
EOF
```

---

## 调试技巧

### 1. 检查技能返回值

```python
result = run_full_trading_analysis()

# 检查返回的数据结构
print(f"返回类型: {type(result)}")
print(f"可用属性: {dir(result)}")

# 检查错误
if hasattr(result, 'errors') and result.errors:
    print("错误详情:")
    for error in result.errors:
        print(f"  {error}")
```

### 2. 测试单个技能

```python
# 测试市场健康检查
from skills import run_market_health_check
health = run_market_health_check()
print(health)

# 测试 IBKR 连接
from mcp__ibkr import health_check
status = health_check()
print(status)
```

### 3. 数据质量诊断

```python
from skills import run_market_health_check

health = run_market_health_check()

print(f"市场状态: {health['session']}")
print(f"数据质量: {health['data_quality']}")
print(f"市场开盘: {health['market_open']}")

if 'data_freshness' in health:
    print(f"数据新鲜度: {health['data_freshness']}")
```

---

## 错误处理模式

### 模式 1: 早期退出

```python
health = run_market_health_check()

if health['data_quality'] == 'CRITICAL':
    print("数据质量严重问题，终止")
    return

# 继续执行...
```

### 模式 2: 降级处理

```python
result = run_full_trading_analysis()

if result.errors:
    print("分析遇到错误，使用降级策略")
    # 使用更保守的参数重试
    result = run_full_trading_analysis(
        min_confidence=0.90,  # 提高置信度要求
        max_orders_per_run=1   # 减少订单数量
    )
```

### 模式 3: 详细日志

```python
import logging

logging.basicConfig(level=logging.DEBUG)

result = run_full_trading_analysis()

if result.warnings:
    for warning in result.warnings:
        logging.warning(warning)

if result.errors:
    for error in result.errors:
        logging.error(error)
```

---

## 技能 API 参考

### 高级工作流技能

| 技能 | 签名 | 返回类型 |
|------|------|----------|
| `run_full_trading_analysis` | `(sectors, min_confidence, max_orders_per_run)` | `TradingAnalysisResult` |
| `run_market_health_check` | `()` | `dict` |
| `run_position_risk_analysis` | `(positions)` | `dict` |

### 原子技能

| 技能 | 签名 | 返回类型 |
|------|------|----------|
| `consult_swarm` | `(sector, market_data)` | `list[Signal]` |
| `place_order_with_guard` | `(symbol, strategy, legs, max_risk, capital_required, metadata)` | `OrderResult` |
| `kelly_criterion` | `(win_prob, win_amount, loss_amount, bankroll, fraction)` | `float` |

---

## 版本历史

- **v2.0.0** (2025-11-21): 初始版本，从 commander_system.md 迁移代码示例
- **v3.0.0** (2025-11-21): 完善调试技巧和错误处理模式

---

**注意**：本文档仅供参考。在实际生产环境中，指挥官应遵循 `prompts/commander_system.md` 中的声明式指导原则，使用高级技能接口而非直接执行代码。
