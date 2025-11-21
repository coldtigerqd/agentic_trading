---
name: 交易帮助
description: 显示所有可用的交易命令和使用指南
category: 交易
tags: [help, trading, commands]
---

# 交易系统帮助

## 可用命令

### 市场分析命令
- `/trade-analysis` - 执行完整的交易分析流程
- `/market-health` - 快速检查市场健康状态
- `/risk-check` - 分析当前持仓风险

### 策略管理命令
- `/strategy-run <策略名>` - 运行指定的策略实例
- `/strategy-list` - 列出所有可用的策略
- `/create-strategy "描述"` - 用自然语言创建新策略

### 帮助命令
- `/trading-help` - 显示此帮助信息

## 使用示例

### 基础分析
```bash
# 执行完整交易分析
/trade-analysis

# 指定板块分析
/trade-analysis --sectors TECH,FINANCE --min-confidence 0.80
```

### 策略执行
```bash
# 运行现有策略
/strategy-run tech_aggressive

# 列出可用策略
/strategy-list
```

### 策略创建
```bash
# 用自然语言创建策略
/create-strategy "使用缠论原理分析最近30天的K线图，识别笔和线段，结合MACD确认买卖点"
```

## 命令说明

所有交易命令都支持以下通用参数：
- `--help` - 显示命令详细帮助
- `--dry-run` - 仅分析不执行实际交易（策略命令）
- `--verbose` - 显示详细执行信息

## 获取特定命令帮助

使用 `--help` 参数获取具体命令的详细说明：
```bash
/trade-analysis --help
/strategy-run --help
```

---
*此帮助系统通过Slash Command Integration提案实现，旨在简化交易操作和策略管理。*