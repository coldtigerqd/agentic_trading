---
name: 风险检查
description: 分析当前持仓风险，提供风险评分和具体操作建议
category: 交易
tags: [risk, analysis, positions, safety]
---

# 风险检查命令

全面分析当前持仓状况，识别高风险仓位并提供风险管理建议，确保交易组合安全可控。

## 命令语法
```bash
/risk-check [选项]
```

## 实现方式
此命令使用稳定的Python脚本 `scripts/risk_check.py` 来执行，避免了bash执行大段代码的不稳定性问题。

## 参数选项

### 显示选项
- `--verbose` - 显示详细信息 (默认: 表格格式)
- `--format <格式>` - 输出格式: table|json (默认: table)

### 帮助信息
- `--help` - 显示此帮助信息

## 支持的参数
脚本支持以下完整的参数列表：
```bash
python scripts/risk_check.py [--format json|table] [--verbose] [--help]
```

## 使用示例

### 全面风险检查
```bash
# 检查所有持仓风险
/risk-check

# 详细模式
/risk-check --verbose

# JSON格式输出
/risk-check --format json

# 组合参数
/risk-check --verbose --format json
```

## 风险评估维度

### 1. 期权到期风险
- **临近到期**: < 7天到期的期权合约
- **极度风险**: < 3天到期的期权合约
- **影响**: 需要立即处理或展期

### 2. 亏损幅度风险
- **警戒亏损**: 亏损 > 15%
- **严重亏损**: 亏损 > 25%
- **影响**: 考虑止损或调整策略

### 3. 集中度风险
- **单一标的集中**: 单个标的占组合 > 30%
- **高集中度**: 单个标的占组合 > 40%
- **影响**: 分散化投资，降低集中风险

### 4. 策略风险
- **卖出期权风险**: 无保护卖出期权
- **杠杆风险**: 过度使用杠杆
- **流动性风险**: 低成交量标的

## 输出格式

### 基础风险报告
```json
{
  "risk_score": 65,
  "overall_status": "中等风险",
  "total_positions": 8,
  "total_exposure": 15680,
  "positions_at_risk": 2,
  "immediate_actions": [
    "AAPL: 临近到期（5天），建议平仓或展期",
    "NVDA: 大额亏损（-18%），考虑止损"
  ],
  "recommendations": [
    "降低单个标的集中度",
    "监控亏损仓位的止损点",
    "检查期权到期日历"
  ]
}
```

### 详细分析报告
```json
{
  "portfolio_summary": {
    "total_positions": 8,
    "total_exposure": 15680,
    "total_unrealized_pnl": -245.67,
    "risk_score": 65,
    "risk_level": "中等风险",
    "last_updated": "2025-11-21 13:45:30"
  },
  "risk_analysis": {
    "expiry_risk": {
      "expiring_positions": 2,
      "critical_expiry": 1,
      "expiry_risk_score": 25
    },
    "loss_risk": {
      "losing_positions": 3,
      "severe_losses": 1,
      "loss_risk_score": 30
    },
    "concentration_risk": {
      "largest_position": "AAPL",
      "largest_percentage": 38.5,
      "concentration_score": 10
    }
  },
  "positions_at_risk": [
    {
      "symbol": "AAPL",
      "contract_type": "OPT",
      "expiry": "2025-11-26",
      "days_to_expiry": 5,
      "risk_type": "临近到期",
      "urgency": "HIGH",
      "action": "CLOSE_OR_ROLL",
      "unrealized_pnl": -125.50,
      "unrealized_pnl_percent": -12.5,
      "recommendation": "建议立即平仓或展期至12月到期"
    },
    {
      "symbol": "NVDA",
      "contract_type": "OPT",
      "risk_type": "大额亏损",
      "urgency": "MEDIUM",
      "action": "REVIEW_STOP_LOSS",
      "unrealized_pnl": -890.25,
      "unrealized_pnl_percent": -22.3,
      "recommendation": "考虑设置止损点，评估是否继续持有"
    }
  ],
  "risk_mitigation": [
    {
      "category": "期权到期",
      "suggestion": "检查到期日历，提前1周展期临近到期的期权",
      "priority": "HIGH"
    },
    {
      "category": "亏损控制",
      "suggestion": "设置-20%止损点，控制单笔最大亏损",
      "priority": "MEDIUM"
    },
    {
      "category": "分散化",
      "suggestion": "将单一标的持仓降至30%以下",
      "priority": "MEDIUM"
    }
  ],
  "monitoring_alerts": [
    "AAPL期权5天后到期，需要关注",
    "NVDA亏损接近-20%，密切监控",
    "组合风险评分65，需要定期检查"
  ]
}
```

### 仅操作建议模式
```json
{
  "immediate_actions": [
    {
      "action": "平仓或展期",
      "target": "AAPL 2025-11-26 PUT",
      "reason": "5天后到期",
      "deadline": "今天收盘前"
    },
    {
      "action": "设置止损",
      "target": "NVDA 看涨价差",
      "reason": "亏损-22.3%",
      "suggested_stop": "-25%"
    }
  ],
  "preventive_measures": [
    "将AAPL仓位减至组合25%以下",
    "建立亏损-20%的系统性止损规则",
    "每周检查一次期权到期日历"
  ]
}
```

## 风险评分系统

### 评分维度 (0-100分)
- **到期风险** (0-35分): 基于到期日临近程度
- **亏损风险** (0-35分): 基于亏损幅度和金额
- **集中度风险** (0-20分): 基于单一标的占比
- **其他风险** (0-10分): 流动性、杠杆等

### 风险等级
- 🟢 **低风险** (0-30): 组合状况良好
- 🟡 **中等风险** (31-70): 需要关注，建议调整
- 🔴 **高风险** (71-100): 需要立即采取行动

## 紧急行动指南

### 高紧急度 (>24小时)
- 期权 < 3天到期
- 亏损 > 25%
- 单一标的 > 50% 集中度

### 中紧急度 (<1周)
- 期权 < 7天到期
- 亏损 15-25%
- 单一标的 30-50% 集中度

### 常规监控 (>1周)
- 亏损 10-15%
- 单一标的 20-30% 集中度
- 策略性风险点

## 集成说明

此命令封装了以下技能和功能：
- `mcp__ibkr__get_positions()` - 获取当前持仓
- `run_position_risk_analysis()` - 风险分析计算
-期权到期日计算和亏损评估
- 集中度分析和建议生成

## 使用建议

### 定期检查频率
- **每日开市前**: 快速风险检查
- **重大市场波动后**: 详细风险分析
- **新仓位建立后**: 风险重新评估

### 风险管理原则
- 及时处理到期期权
- 严格执行止损纪律
- 保持投资组合分散化
- 定期评估风险承受能力

---
*此命令帮助用户全面了解持仓风险，提供专业化的风险管理建议，确保交易安全。*