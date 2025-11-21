# Agentic AlphaHive 交易脚本

这是为了替代不稳定的bash命令执行而创建的独立Python脚本集合。

## 脚本列表

### 1. 市场健康检查 (`market_health.py`)
快速检查市场状态和数据质量。

```bash
# 基础检查
python scripts/market_health.py

# JSON格式输出
python scripts/market_health.py --format json

# 详细模式
python scripts/market_health.py --verbose
```

### 2. 交易分析 (`trade_analysis.py`)
执行完整的交易分析流程，生成高置信度交易信号。

```bash
# 默认分析
python scripts/trade_analysis.py

# 试运行模式（不执行交易）
python scripts/trade_analysis.py --dry-run

# 指定板块分析
python scripts/trade_analysis.py --sectors TECH,FINANCE

# 提高置信度要求
python scripts/trade_analysis.py --min-confidence 0.80

# JSON格式输出
python scripts/trade_analysis.py --format json

# 详细模式
python scripts/trade_analysis.py --verbose
```

### 3. 策略运行器 (`strategy_runner.py`)
运行单个策略实例。

```bash
# 显示可用策略列表
python scripts/strategy_runner.py

# 运行特定策略
python scripts/strategy_runner.py tech_aggressive

# 试运行模式
python scripts/strategy_runner.py tech_aggressive --dry-run

# JSON格式输出
python scripts/strategy_runner.py tech_aggressive --format json
```

### 4. 风险检查 (`risk_check.py`)
分析当前持仓的风险状况。

```bash
# 基础风险检查
python scripts/risk_check.py

# JSON格式输出
python scripts/risk_check.py --format json

# 详细模式
python scripts/risk_check.py --verbose
```

## 通用参数

所有脚本都支持以下通用参数：

- `--format json|table` - 输出格式（默认：table）
- `--verbose` - 显示详细执行过程
- `--help` - 显示帮助信息

## 稳定性改进

这些独立脚本解决了之前bash执行大段代码的稳定性问题：

1. **语法检查** - Python解释器会在执行前检查语法错误
2. **错误处理** - 完整的异常处理和用户友好的错误信息
3. **参数验证** - 严格的输入参数验证
4. **输出格式化** - 统一的输出格式（表格/JSON）
5. **帮助文档** - 每个脚本都有完整的帮助信息

## 集成到slash命令

这些脚本可以直接集成到Claude Code的slash命令系统中，提供稳定的命令行接口。

## 注意事项

- 所有脚本都会自动添加项目路径到Python路径
- 脚本具有完整的错误处理机制
- 支持中文输出和错误信息
- 遵循项目的安全约束和风险管理原则