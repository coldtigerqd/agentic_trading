---
name: 策略创建
description: 使用自然语言描述自动创建交易策略模板和参数配置
category: 策略管理
tags: [strategy, creation, natural-language, automation]
---

# 策略创建命令

通过自然语言描述自动创建完整的交易策略，包括生成Markdown模板、参数配置文件，并支持后续的策略实例化。

## 命令语法
```bash
/create-strategy "策略描述" [选项]
```

## 参数说明

### 必需参数
- `策略描述` - 用自然语言描述的交易策略

### 策略配置
- `--name <策略名>` - 指定策略名称
- `--sector <板块>` - 指定策略适用的板块 (默认: GENERAL)
- `--template <模板名>` - 指定模板文件名

### 创建选项
- `--validate` - 验证生成的模板语法 (默认: true)
- `--dry-run` - 仅预览不创建文件
- `--overwrite` - 覆盖已存在的策略文件

### 帮助信息
- `--help` - 显示此帮助信息

## 使用示例

### 基础策略创建
```bash
# 使用缠论原理创建策略
/create-strategy "使用缠论原理分析最近30天的K线图，识别笔和线段，结合MACD确认买卖点，在科技股中寻找机会"

# 创建RSI均值回归策略
/create-strategy "基于RSI超买超卖的均值回归策略，在70以上卖出，30以下买入，适合大蓝筹股"

# 创建波动率策略
/create-strategy "利用隐含波动率扩张的权利金卖出策略，寻找IV rank超过80%的期权"
```

### 指定参数创建
```bash
# 指定策略名称和板块
/create-strategy "科技股趋势跟踪策略" --name tech_trend_tracker --sector TECH

# 使用特定模板
/create-strategy "改进版波动率狙击策略" --template vol_sniper.md --name enhanced_vol_sniper
```

### 预览和验证
```bash
# 仅预览不创建
/create-strategy "双均线交叉策略" --dry-run

# 跳过验证（快速创建）
/create-strategy "简单价格突破策略" --validate false
```

## 支持的策略概念

### 技术分析概念
- **缠论**: 笔、线段、中枢、背驰、分型
- **均线**: MA、EMA、双均线交叉、均线支撑阻力
- **指标**: RSI、MACD、KDJ、布林带、ATR
- **形态**: 头肩、三角形、矩形、楔形

### 期权策略概念
- **波动率**: IV Rank、IV Percentile、波动率微笑
- **策略类型**: 垂直价差、水平价差、对角价差
- **希腊字母**: Delta、Gamma、Theta、Vega风险管理
- **到期管理**: 时间衰减、展期策略

### 市场环境概念
- **趋势**: 上升趋势、下降趋势、横盘整理
- **波动**: 高波动、低波动、波动率突发
- **情绪**: 恐慌、贪婪、中性、乐观
- **事件**: 财报、FOMC、经济数据、地缘政治

## 策略创建流程

### 1. 概念提取
分析自然语言描述，识别：
- 技术分析概念和方法
- 策略类型和工具
- 时间周期和参数范围
- 风险控制要求

### 2. 模板生成
根据提取的概念创建：
- Markdown策略模板文件
- 完整的分析流程说明
- 技能导入和执行指令
- 输出格式规范

### 3. 参数建议
基于策略特征建议：
- 标的池配置
- 关键参数范围
- 风险控制参数
- 执行时间窗口

### 4. 验证优化
检查和优化：
- Jinja2模板语法
- 技能函数正确性
- 参数合理性
- 文档完整性

## 生成文件结构

成功创建后生成以下文件：

### 策略模板文件
```
swarm_intelligence/templates/策略名称.md
```
包含完整的策略逻辑分析流程。

### 参数配置文件
```
swarm_intelligence/active_instances/策略名称.json
```
包含策略的所有可调参数。

## 输出示例

### 成功创建示例
```json
{
  "status": "success",
  "strategy_name": "chanlun_tech_strategy",
  "files_created": [
    "swarm_intelligence/templates/chanlun_tech_strategy.md",
    "swarm_intelligence/active_instances/chanlun_tech_strategy.json"
  ],
  "summary": {
    "template_path": "swarm_intelligence/templates/chanlun_tech_strategy.md",
    "config_path": "swarm_intelligence/active_instances/chanlun_tech_strategy.json",
    "strategy_type": "技术分析策略",
    "target_sectors": ["TECH"],
    "complexity": "中等",
    "estimated_signals_per_run": "1-3"
  },
  "next_steps": [
    "检查生成的模板文件",
    "调整参数配置",
    "使用 /strategy-run 测试策略",
    "根据实际表现优化参数"
  ]
}
```

### 预览模式输出
```json
{
  "status": "preview",
  "strategy_analysis": {
    "concepts_detected": [
      "缠论分析",
      "笔和线段识别",
      "MACD确认",
      "科技股"
    ],
    "suggested_template": "基于缠论的技术分析模板",
    "recommended_parameters": {
      "symbol_pool": ["AAPL", "NVDA", "AMD", "TSLA"],
      "lookback_days": 30,
      "pen_threshold": 5,
      "macd_params": {
        "fast": 12,
        "slow": 26,
        "signal": 9
      }
    }
  },
  "files_to_create": [
    "swarm_intelligence/templates/chanlun_tech_strategy.md",
    "swarm_intelligence/active_instances/chanlun_tech_strategy.json"
  ]
}
```

### 常见策略模板

#### 缠论策略模板
```markdown
# 缠论趋势跟踪策略

使用缠论原理识别笔、线段结构，结合技术指标确认买卖点...

## 参数配置
- **symbol_pool**: 分析标的池
- **lookback_days**: K线分析周期
- **pen_threshold**: 笔的最小K线数
- **zhongshu_depth**: 中枢分析深度
```

#### 波动率策略模板
```markdown
# 隐含波动率策略

基于IV Rank和波动率微笑的权利金卖出策略...

## 参数配置
- **min_iv_rank**: 最小IV Rank要求
- **max_exposure**: 最大敞口限制
- **dte_range**: 到期日范围
- **sentiment_filter**: 情绪过滤器
```

## 高级功能

### 策略模板增强
- **多时间周期分析**: 支持日线、周线、月线同时分析
- **多指标确认**: 自动组合相关技术指标
- **动态参数调整**: 根据市场环境自动调整参数
- **风险评估内置**: 集成完整的风险控制逻辑

### 参数优化建议
- **历史回测推荐**: 基于历史数据推荐参数范围
- **波动率适配**: 根据不同波动率环境调整参数
- **行业特征化**: 针对不同行业的策略参数定制
- **风险预算**: 整合风险预算管理参数

## 验证和测试

### 语法验证
- Jinja2模板语法检查
- 技能函数导入验证
- 参数类型和范围验证
- 输出格式正确性检查

### 逻辑验证
- 策略逻辑完整性检查
- 边界条件处理验证
- 错误场景覆盖测试
- 性能影响评估

## 错误处理

### 常见错误及解决方案

#### 概念识别失败
```
错误: 无法识别有效的交易概念
解决: 提供更具体的策略描述，包含明确的技术分析术语
```

#### 模板生成失败
```
错误: 无法生成策略模板
解决: 检查描述是否包含足够的策略细节
```

#### 参数冲突
```
错误: 生成的参数存在逻辑冲突
解决: 系统将自动调整参数范围，避免冲突
```

#### 文件已存在
```
错误: 策略文件已存在
解决: 使用 --overwrite 参数覆盖，或选择不同的策略名称
```

## 集成说明

此命令使用以下核心功能：
- `extract_trading_concepts()` - 概念提取引擎
- `generate_strategy_template()` - 模板生成器
- `suggest_strategy_parameters()` - 参数建议系统
- `validate_strategy_files()` - 文件验证器

## 最佳实践

### 策略描述技巧
- **具体化**: 使用具体的技术分析术语
- **结构化**: 明确分析流程和决策逻辑
- **量化**: 提供具体的参数范围和阈值
- **场景化**: 描述适用的市场环境和条件

### 参数优化建议
- 从保守参数开始
- 基于历史数据调整
- 考虑不同市场环境
- 定期回顾和优化

### 策略验证流程
- 先用干运行测试
- 小仓位实盘验证
- 逐步扩大规模
- 持续监控和优化

---
*此命令让策略创建变得简单直观，大大降低了量化交易的入门门槛！*