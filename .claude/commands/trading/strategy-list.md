---
name: 策略列表
description: 列出所有可用的策略实例及其状态和性能信息
category: 策略管理
tags: [strategy, list, status, monitoring]
---

# 策略列表命令

显示所有可用的交易策略实例，包括策略配置、历史表现和执行状态，帮助用户选择合适的策略。

## 命令语法
```bash
/strategy-list [选项]
```

## 参数选项

### 显示控制
- `--detailed` - 显示详细策略信息
- `--status-only` - 仅显示策略状态
- `--performance` - 显示历史表现数据

### 过滤选项
- `--sector <板块>` - 按板块筛选策略
- `--active-only` - 仅显示活跃策略
- `--template <模板名>` - 显示使用特定模板的策略

### 排序选项
- `--sort-by <字段>` - 排序字段: name, sector, last_run, performance
- `--reverse` - 逆序排列

### 帮助信息
- `--help` - 显示此帮助信息

## 使用示例

### 基础列表
```bash
# 显示所有策略
/strategy-list

# 简洁状态显示
/strategy-list --status-only

# 详细信息显示
/strategy-list --detailed
```

### 筛选和过滤
```bash
# 按板块筛选
/strategy-list --sector TECH

# 仅活跃策略
/strategy-list --active-only

# 使用特定模板的策略
/strategy-list --template vol_sniper.md
```

### 排序和性能
```bash
# 按最后运行时间排序
/strategy-list --sort-by last_run

# 显示历史表现
/strategy-list --performance

# 按表现逆序排列
/strategy-list --performance --sort-by performance --reverse
```

## 策略信息结构

每个策略实例包含以下信息：

### 基础信息
- **策略名称**: 策略的唯一标识
- **所属板块**: 策略适用的市场板块
- **模板名称**: 使用的策略模板
- **创建时间**: 策略实例的创建日期
- **最后修改**: 上次参数调整时间

### 配置参数
- **标的池**: 策略监控的股票/ETF列表
- **核心参数**: 策略的关键配置参数
- **风险控制**: 限制性参数和约束条件

### 状态信息
- **活跃状态**: 策略是否处于活跃使用状态
- **最后运行**: 上次执行时间
- **运行频率**: 策略执行的频率
- **数据新鲜度**: 依赖数据的新鲜程度

### 性能指标
- **总运行次数**: 历史执行次数
- **平均信号数**: 每次运行生成的平均信号数
- **高置信率**: 高置信度信号的比例
- **平均执行时间**: 平均运行耗时

## 输出格式

### 基础列表模式
```json
{
  "total_strategies": 5,
  "active_strategies": 3,
  "last_update": "2025-11-21 13:45:30",
  "strategies": [
    {
      "name": "tech_aggressive",
      "sector": "TECH",
      "template": "vol_sniper.md",
      "status": "活跃",
      "last_run": "2025-11-21 10:30:15",
      "signal_count": 2
    },
    {
      "name": "finance_conservative",
      "sector": "FINANCE",
      "template": "vol_sniper.md",
      "status": "活跃",
      "last_run": "2025-11-21 09:15:22",
      "signal_count": 1
    }
  ]
}
```

### 详细信息模式
```json
{
  "strategies": [
    {
      "name": "tech_aggressive",
      "metadata": {
        "id": "tech_aggressive",
        "sector": "TECH",
        "template": "vol_sniper.md",
        "created": "2025-11-15",
        "last_modified": "2025-11-18"
      },
      "configuration": {
        "symbol_pool": ["NVDA", "AMD", "TSLA"],
        "min_iv_rank": 80,
        "max_delta_exposure": 0.30,
        "sentiment_filter": "neutral_or_better"
      },
      "status": {
        "active": true,
        "last_run": "2025-11-21 10:30:15",
        "run_frequency": "每日2-3次",
        "data_freshness": "良好"
      },
      "performance": {
        "total_runs": 45,
        "avg_signals_per_run": 2.1,
        "high_confidence_rate": 0.78,
        "avg_execution_time": 3.2,
        "success_rate": 0.82
      }
    }
  ]
}
```

### 性能数据模式
```json
{
  "performance_summary": {
    "total_strategies": 5,
    "total_runs": 156,
    "avg_signals_per_run": 1.8,
    "overall_success_rate": 0.76,
    "avg_execution_time": 2.9
  },
  "strategy_performance": [
    {
      "name": "tech_aggressive",
      "runs": 45,
      "avg_signals": 2.1,
      "high_confidence_rate": 0.78,
      "success_rate": 0.82,
      "avg_execution_time": 3.2,
      "performance_trend": "稳定",
      "last_7_days": {
        "runs": 7,
        "signals": 16,
        "successes": 6
      }
    }
  ]
}
```

### 状态概览模式
```json
{
  "strategy_overview": {
    "total_strategies": 5,
    "active_strategies": 3,
    "paused_strategies": 1,
    "archived_strategies": 1
  },
  "by_sector": {
    "TECH": 2,
    "FINANCE": 1,
    "GENERAL": 2
  },
  "by_template": {
    "vol_sniper.md": 3,
    "mean_reversion.md": 2
  },
  "health_status": {
    "all_strategies_healthy": true,
    "issues_found": 0,
    "warnings": [
      "finance_conservative 7天未运行",
      "correlation_arb_tech_pairs 数据可能过期"
    ]
  }
}
```

## 策略状态说明

### 活跃状态分类
- **活跃**: 正常使用，定期执行
- **暂停**: 临时停止使用，可随时恢复
- **归档**: 不再使用，仅作记录
- **错误**: 配置或执行问题，需要修复

### 性能评估
- **优秀**: 成功率 > 80%，信号质量高
- **良好**: 成功率 60-80%，表现稳定
- **一般**: 成功率 40-60%，需要监控
- **不佳**: 成功率 < 40%，需要调整

### 数据状态
- **新鲜**: 所有依赖数据都是最新的
- **正常**: 大部分数据新鲜，少量延迟
- **过期**: 部分关键数据过期，需要更新
- **缺失**: 重要数据不可用

## 集成说明

此命令使用以下功能：
- `load_all_strategy_instances()` - 加载所有策略配置
- `get_strategy_performance()` - 获取历史表现数据
- `analyze_strategy_health()` - 分析策略健康状态
- `filter_and_sort_strategies()` - 策略筛选和排序

## 使用建议

### 策略选择
- 根据市场环境选择对应板块策略
- 优先考虑表现优异的活跃策略
- 避免同时使用过多相似策略

### 性能监控
- 定期查看策略表现趋势
- 关注成功率和信号质量变化
- 及时调整表现不佳的策略

### 维护管理
- 定期清理归档不用的策略
- 更新过时的策略配置
- 监控策略依赖的数据质量

---
*此命令帮助用户全面了解策略状态，做出明智的策略选择决策。*