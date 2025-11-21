# Slash Command 使用指南

本指南介绍如何使用新实现的Slash Command系统来简化交易操作和策略管理。

## 快速入门

### 基础命令

#### 1. 市场健康检查
```bash
# 快速检查市场状态
/market-health

# 详细市场分析
/market-health --detailed

# 检查数据质量
/market-health --data-quality
```

#### 2. 完整交易分析
```bash
# 执行默认分析
/trade-analysis

# 定制分析参数
/trade-analysis --sectors TECH,FINANCE --min-confidence 0.80

# 仅分析不执行
/trade-analysis --dry-run
```

#### 3. 风险检查
```bash
# 检查所有持仓风险
/risk-check

# 检查特定标的
/risk-check --symbol AAPL

# 仅显示操作建议
/risk-check --recommendations-only
```

### 策略管理

#### 1. 策略列表
```bash
# 列出所有策略
/strategy-list

# 详细信息
/strategy-list --detailed

# 查看性能数据
/strategy-list --performance

# 按板块筛选
/strategy-list --sector TECH
```

#### 2. 策略执行
```bash
# 运行策略
/strategy-run tech_aggressive

# 自定义参数
/strategy-run finance_conservative --confidence 0.85

# 仅显示信号
/strategy-run tech_aggressive --signals-only

# 详细模式
/strategy-run tech_aggressive --verbose --timing
```

#### 3. 策略创建
```bash
# 创建缠论策略
/create-strategy "使用缠论原理分析最近30天的K线图，识别笔和线段，结合MACD确认买卖点"

# 指定策略名称
/create-strategy "RSI均值回归策略" --name rsi_mean_reversion --sector TECH

# 预览模式
/create-strategy "双均线交叉策略" --dry-run
```

### 帮助系统

#### 1. 命令帮助
```bash
# 总体帮助
/trading-help

# 特定命令帮助
/trade-analysis --help
/strategy-run --help
/create-strategy --help
```

## 完整工作流程示例

### 日常交易流程

#### 1. 市场开盘前检查
```bash
# 1. 检查市场状态
/market-health

# 2. 如果市场状态良好，执行完整分析
if [ market_open == true ] && [ data_quality == "GOOD" ]; then
    /trade-analysis --min-confidence 0.75
fi

# 3. 检查持仓风险
/risk-check
```

#### 2. 策略运行流程
```bash
# 1. 查看可用策略
/strategy-list

# 2. 运行选定的策略
/strategy-run tech_aggressive --verbose

# 3. 检查执行结果
/strategy-list --performance --sort-by performance
```

#### 3. 新策略开发流程
```bash
# 1. 用自然语言创建策略
/create-strategy "基于RSI超买超卖的科技股均值回归策略"

# 2. 测试新策略
/strategy-run 新策略名称 --dry-run

# 3. 如有需要，调整参数
# 编辑生成的配置文件

# 4. 正式运行策略
/strategy-run 新策略名称
```

## 高级用法

### 参数组合优化

#### 交易分析优化
```bash
# 保守模式
/trade-analysis --min-confidence 0.85 --max-orders 1 --skip-sync

# 激进模式
/trade-analysis --min-confidence 0.65 --max-orders 5

# 特定市场环境
/trade-analysis --sectors TECH --min-confidence 0.80
```

#### 策略执行优化
```bash
# 批量执行
/strategy-run strategy1
/strategy-run strategy2
/strategy-run strategy3

# 监控模式
/strategy-run strategy_name --verbose --timing
```

### 自动化脚本

#### 每日检查脚本
```bash
#!/bin/bash
# 每日市场检查脚本

echo "=== 每日市场检查 ==="

# 1. 市场健康检查
echo "检查市场状态..."
market_status=$(/market-health --json | jq -r '.status')

if [ "$market_status" == "健康" ]; then
    echo "✅ 市场状态良好"

    # 2. 风险检查
    echo "检查持仓风险..."
    risk_score=$(/risk-check --json | jq -r '.risk_score')

    if [ "$risk_score" -lt 70 ]; then
        echo "✅ 风险水平可接受"

        # 3. 执行交易分析
        echo "执行交易分析..."
        /trade-analysis
    else
        echo "⚠️ 风险水平较高，建议优先处理持仓"
    fi
else
    echo "❌ 市场状态不适合交易"
fi
```

#### 策略回测脚本
```bash
#!/bin/bash
# 策略性能测试脚本

STRATEGIES=("tech_aggressive" "finance_conservative" "mean_reversion_spx")
CONFIDENCE_LEVELS=(0.70 0.75 0.80)

for strategy in "${STRATEGIES[@]}"; do
    echo "=== 测试策略: $strategy ==="

    for confidence in "${CONFIDENCE_LEVELS[@]}"; do
        echo "测试置信度: $confidence"
        /strategy-run "$strategy" --confidence "$confidence" --verbose
        echo "---"
    done
done
```

## 错误处理和故障排除

### 常见错误及解决方案

#### 1. 命令未找到
```bash
# 错误: 命令不存在
# 解决: 检查命令名称或使用 /trading-help

/trading-help
```

#### 2. 策略实例不存在
```bash
# 错误: 策略 'unknown_strategy' 不存在
# 解决: 查看可用策略列表

/strategy-list
```

#### 3. 参数错误
```bash
# 错误: 置信度参数超出范围
# 解决: 使用 --help 查看有效范围

/trade-analysis --help
```

#### 4. 数据连接问题
```bash
# 错误: 无法获取市场数据
# 解决: 跳过数据同步或检查连接

/market-health  # 检查连接状态
/trade-analysis --skip-sync  # 跳过数据同步
```

### 调试技巧

#### 1. 详细模式
```bash
# 显示详细执行过程
/strategy-run strategy_name --verbose

# 显示执行时间统计
/trade-analysis --timing

# 显示详细分析结果
/market-health --detailed
```

#### 2. 干运行模式
```bash
# 仅分析不执行
/trade-analysis --dry-run

# 仅生成信号不交易
/strategy-run strategy_name --dry-run
```

#### 3. 分步执行
```bash
# 1. 先检查市场
/market-health

# 2. 再检查风险
/risk-check

# 3. 最后执行分析
/trade-analysis
```

## 最佳实践

### 1. 命令使用原则

- **先检查后执行**: 使用市场健康检查确认环境
- **参数验证**: 使用 `--help` 了解参数范围
- **小步测试**: 使用 `--dry-run` 验证策略逻辑
- **日志记录**: 使用 `--verbose` 跟踪执行过程

### 2. 策略管理原则

- **定期评估**: 使用 `/strategy-list --performance` 监控表现
- **参数优化**: 根据实际表现调整策略参数
- **风险控制**: 定期使用 `/risk-check` 评估风险
- **记录决策**: 保持详细的策略调整记录

### 3. 系统集成原则

- **工作流标准化**: 建立固定的命令执行顺序
- **监控自动化**: 将关键检查自动化
- **备份机制**: 重要策略配置需要备份
- **版本控制**: 策略修改需要版本管理

## 进阶用法

### 1. 与现有技能集成

命令系统完全兼容现有的Python技能函数，可以无缝集成：

```bash
# 命令调用方式
/trade-analysis

# Python调用方式
from skills import run_full_trading_analysis
result = run_full_trading_analysis()
```

### 2. 自定义配置

用户可以创建自定义的配置文件：

```json
{
  "default_confidence": 0.75,
  "max_orders_per_day": 5,
  "risk_threshold": 70,
  "preferred_sectors": ["TECH", "FINANCE"]
}
```

### 3. 扩展命令

系统支持添加新的命令，只需在 `.claude/commands/trading/` 目录下创建新的 `.md` 文件即可。

---

通过Slash Command系统，您可以用最简单的方式执行复杂的交易操作，大大提高了交易系统的可用性和效率！