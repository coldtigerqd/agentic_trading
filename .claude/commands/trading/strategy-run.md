---
name: 策略运行
description: 执行指定的策略实例，支持单个或批量策略运行
category: 策略管理
tags: [strategy, execution, swarm, signals]
---

# 策略运行命令

执行指定的策略实例，调用蜂群智能分析并生成交易信号，支持多种执行模式和参数控制。

## 命令语法
```bash
/strategy-run [策略名] [选项]
```

## 实现方式
此命令使用稳定的Python脚本 `scripts/strategy_runner.py` 来执行，避免了bash执行大段代码的不稳定性问题。

## 参数说明

### 可选参数
- `策略名` - 要运行的策略实例名称，对应 `swarm_intelligence/active_instances/` 中的文件名。如果未提供，将显示可用策略列表。

### 执行控制
- `--dry-run` - 仅分析不执行交易 (默认: false)
- `--verbose` - 显示详细执行过程 (默认: false)

### 输出选项
- `--format <格式>` - 输出格式: table|json (默认: table)

### 帮助信息
- `--help` - 显示此帮助信息

## 支持的参数
脚本支持以下完整的参数列表：
```bash
python scripts/strategy_runner.py [strategy_name] [--dry-run] [--verbose] [--format json|table] [--help]
```

## 使用示例

### 基础策略执行
```bash
# 显示可用策略列表
/strategy-run

# 运行科技股激进策略
/strategy-run tech_aggressive

# 运行金融保守策略
/strategy-run finance_conservative

# 干运行模式
/strategy-run tech_aggressive --dry-run
```

### 输出格式控制
```bash
# JSON格式输出
/strategy-run tech_aggressive --format json

# 详细模式
/strategy-run tech_aggressive --verbose

# 组合参数
/strategy-run tech_aggressive --dry-run --verbose --format json
```

## 可用策略实例

### 科技股策略
- `tech_aggressive` - 科技股激进波动率策略
- `tech_trend_follower` - 科技趋势跟踪策略
- `breakout_scout_tech` - 科技股突破侦察策略

### 其他板块策略
- `finance_conservative` - 金融保守策略
- `mean_reversion_spx` - 标普均值回归策略
- `correlation_arb_tech_pairs` - 科技配对套利策略

## 执行流程

### 1. 策略实例加载
- 读取策略配置文件 (`active_instances/*.json`)
- 加载对应模板文件
- 验证策略参数完整性

### 2. 市场数据准备
- 可选：同步最新市场数据
- 构建市场快照
- 验证数据质量

### 3. 蜂群智能分析
- 渲染策略模板
- 并发执行蜂群分析
- 收集分析结果和信号

### 4. 信号过滤和排序
- 应用置信度过滤器
- 按置信度排序信号
- 验证信号完整性

### 5. 风险评估和建议
- 计算建议仓位大小
- 风险收益比评估
- 执行建议生成

## 输出格式

### 基础执行结果
```json
{
  "strategy_name": "tech_aggressive",
  "execution_time": "2025-11-21 13:45:30",
  "market_session": "REGULAR",
  "data_quality": "GOOD",
  "signals": [
    {
      "signal": "SHORT_PUT_SPREAD",
      "target": "NVDA",
      "confidence": 0.82,
      "reasoning": "IV rank 88%，中性情绪，技术支撑确认",
      "params": {
        "legs": [...],
        "max_risk": 400,
        "capital_required": 500
      }
    }
  ],
  "summary": {
    "total_signals": 1,
    "high_confidence_signals": 1,
    "execution_duration": 2.3
  }
}
```

### 详细执行模式
```json
{
  "strategy_info": {
    "name": "tech_aggressive",
    "template": "vol_sniper.md",
    "sector": "TECH",
    "parameters": {
      "symbol_pool": ["NVDA", "AMD", "TSLA"],
      "min_iv_rank": 80,
      "max_delta_exposure": 0.30
    }
  },
  "execution_details": {
    "data_sync_time": 1.2,
    "template_render_time": 0.1,
    "swarm_consultation_time": 1.8,
    "signal_processing_time": 0.2,
    "total_time": 3.3
  },
  "market_context": {
    "spy_trend": "SIDEWAYS",
    "market_volatility": 18.5,
    "vix_level": "MODERATE"
  },
  "analysis_results": {
    "symbols_analyzed": 3,
    "signals_generated": 5,
    "signals_filtered": 1,
    "confidence_distribution": {
      "high": 1,
      "medium": 2,
      "low": 2
    }
  }
}
```

### 仅信号模式
```json
{
  "actionable_signals": [
    {
      "signal": "SHORT_PUT_SPREAD",
      "target": "NVDA",
      "confidence": 0.82,
      "max_risk": 400,
      "recommended_position": 1
    }
  ]
}
```

## 错误处理

### 常见错误及解决方案

#### 策略实例不存在
```
错误: 策略实例 'unknown_strategy' 不存在
解决: 使用 /strategy-list 查看可用策略
```

#### 模板文件缺失
```
错误: 策略模板 'missing_template.md' 未找到
解决: 检查策略配置中的template字段
```

#### 市场数据问题
```
错误: 市场数据质量 CRITICAL，跳过执行
解决: 使用 --market-data false 或等待数据刷新
```

#### 参数验证失败
```
错误: 置信度参数超出范围 (0.0-1.0)
解决: 使用有效的置信度数值
```

## 集成说明

此命令封装了以下核心功能：
- `load_strategy_instance()` - 策略实例加载
- `sync_watchlist_incremental()` - 数据同步
- `consult_swarm()` - 蜂群智能咨询
- `filter_signals()` - 信号过滤
- `calculate_position_size()` - 仓位计算

## 性能特性

### 执行时间
- **数据同步**: 1-3秒 (如需要)
- **模板渲染**: < 1秒
- **蜂群分析**: 1-5秒
- **总计**: 通常 < 10秒

### 并发支持
- 支持多个策略并发执行
- 智能资源管理
- 结果聚合和去重

## 最佳实践

### 策略选择
- 根据市场环境选择合适策略
- 避免同时运行过多相似策略
- 定期评估策略表现

### 参数调优
- 根据风险承受能力调整置信度
- 考虑市场波动率影响
- 保持仓位大小合理

### 执行监控
- 关注执行时间和数据质量
- 记录策略表现
- 定期评估策略有效性

---
*此命令提供灵活的策略执行能力，支持多种执行模式和详细的分析报告。*