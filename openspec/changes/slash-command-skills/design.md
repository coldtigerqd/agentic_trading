# Slash Command技能调用与策略系统增强

## 变更ID
`slash-command-skills`

## 变更描述
在保持现有Template + Parameters优秀架构的基础上，添加Slash Command简化调用接口，增强策略编写和管理体验，实现"一行命令启用"的便捷操作。

## 核心设计原则

### 保持现有价值
- ✅ **保留Template + Parameters架构**：不破坏现有的灵活性和参数化能力
- ✅ **保持现有技能库**：不重写高质量的Python技能实现
- ✅ **保持策略实例系统**：继续支持active_instances配置

### 增强用户体验
- 🎯 **Slash Command调用**：`/trade-analysis`替代复杂import
- 🎯 **自然语言策略创建**：`/create-strategy "基于缠论的突破策略"`
- 🎯 **一键策略执行**：`/strategy-run tech_aggressive`
- 🎯 **简化调试和监控**：更好的错误信息和执行状态

## 解决方案架构

### 1. Slash Command层面 (新增)

```
.claude/commands/trading/
├── trade-analysis.md      # 完整交易分析
├── market-health.md       # 市场健康检查
├── risk-check.md          # 持仓风险分析
├── strategy-run.md        # 运行指定策略实例
├── strategy-list.md       # 列出可用策略
└── create-strategy.md     # 自然语言创建策略
```

### 2. 策略系统层面 (增强)

**现有结构 (保持不变)**：
```
swarm_intelligence/
├── templates/             # Markdown策略模板 (保持)
├── active_instances/      # JSON参数配置 (保持)
└── instances/             # 归档的策略实例 (保持)
```

**新增增强功能**：
```
swarm_intelligence/
├── strategy_factory.py    # 策略创建工厂 (新增)
├── template_validator.py  # 模板验证工具 (新增)
└── strategy_helper.py     # 策略辅助函数 (新增)
```

### 3. 技能调用层面 (简化)

**当前方式** (复杂，容易出错)：
```python
# Commander需要手动导入和调用
from skills import run_full_trading_analysis
result = run_full_trading_analysis(
    sectors=["TECH"],
    min_confidence=0.75,
    max_orders_per_run=2
)
```

**新方式** (简单，一行命令)：
```bash
/trade-analysis --sectors TECH --min-confidence 0.75
# 或
/strategy-run tech_aggressive
```

## 详细实现方案

### 第一阶段：核心Slash Commands

#### 1.1 `/trade-analysis` - 完整交易分析
```markdown
---
name: Trading Analysis
description: Execute complete trading analysis workflow
category: Trading
---

# Trading Analysis

执行完整的交易分析流程，包括市场检查、数据同步、蜂群咨询和信号执行。

## 参数
- `--sectors`: 板块列表 (默认: ALL)
- `--min-confidence`: 最低置信度 (默认: 0.75)
- `--max-orders`: 最大订单数 (默认: 2)

## 使用示例
```bash
/trade-analysis
/trade-analysis --sectors TECH,FINANCE --min-confidence 0.80
```

## 执行逻辑
```python
from skills import run_full_trading_analysis

# 解析参数并执行
result = run_full_trading_analysis(
    sectors=parse_sectors(args.sectors),
    min_confidence=float(args.min_confidence),
    max_orders_per_run=int(args.max_orders)
)

# 格式化返回结果
return format_trading_result(result)
```
```

#### 1.2 `/strategy-run` - 运行策略实例
```markdown
---
name: Strategy Runner
description: Execute specific strategy instance
category: Trading
---

# Strategy Runner

运行指定的策略实例，支持单个或批量执行。

## 参数
- `instance`: 策略实例ID (必需)
- `market-data`: 是否同步最新市场数据 (默认: true)
- `dry-run`: 仅分析不执行交易 (默认: false)

## 使用示例
```bash
/strategy-run tech_aggressive
/strategy-run mean_reversion_spx --dry-run true
/strategy-run correlation_arb_tech_pairs --market-data false
```

## 执行逻辑
```python
from skills.swarm_core import consult_swarm
from skills.data_sync import sync_watchlist_incremental

# 加载策略实例
instance = load_strategy_instance(args.instance)

# 可选数据同步
if args.market_data:
    sync_watchlist_incremental()

# 执行策略
signals = consult_swarm(
    sector=instance['sector'],
    market_data=get_market_snapshot(),
    template=instance['template'],
    parameters=instance['parameters']
)

return format_strategy_result(signals, instance)
```

#### 1.3 `/create-strategy` - 自然语言创建策略
```markdown
---
name: Strategy Creator
description: Create new strategy from natural language description
category: Trading
---

# Strategy Creator

根据自然语言描述自动创建策略模板和参数配置。

## 参数
- `description`: 策略描述 (必需)
- `sector`: 板块分类 (默认: GENERAL)
- `validate`: 是否验证模板语法 (默认: true)

## 使用示例
```bash
/create-strategy "使用缠论原理分析最近30天的K线图，识别笔和线段，结合MACD确认买卖点"
/create-strategy "基于RSI超买超卖的均值回归策略，在科技股中寻找机会" --sector TECH
```

## 执行逻辑
```python
from swarm_intelligence.strategy_factory import create_strategy_from_description

# 解析策略描述
strategy_config = create_strategy_from_description(
    description=args.description,
    sector=args.sector
)

# 生成模板文件
template_path = create_template_file(strategy_config)

# 生成参数配置
parameters_path = create_parameters_file(strategy_config)

# 验证生成结果
if args.validate:
    validate_strategy_template(template_path)
    validate_strategy_parameters(parameters_path)

return format_creation_result(strategy_config, template_path, parameters_path)
```

### 第二阶段：策略编写增强

#### 2.1 增强的模板系统
**新增模板辅助函数**：
```python
# swarm_intelligence/template_helper.py

def extract_technical_concepts(description: str) -> List[str]:
    """从描述中提取技术概念"""
    concepts = []
    if "缠论" in description:
        concepts.extend(["笔", "线段", "中枢", "背驰", "分型"])
    if "MACD" in description:
        concepts.extend(["MACD", "DIF", "DEA", "柱状图"])
    # ... 更多概念
    return concepts

def suggest_parameters(concepts: List[str]) -> Dict:
    """基于技术概念建议参数"""
    params = {}
    if "缠论" in concepts:
        params.update({
            "lookback_days": {"default": 30, "description": "K线分析周期"},
            "min_pen_bars": {"default": 5, "description": "笔的最小K线数"}
        })
    if "MACD" in concepts:
        params.update({
            "macd_fast": {"default": 12, "description": "MACD快线周期"},
            "macd_slow": {"default": 26, "description": "MACD慢线周期"}
        })
    return params

def generate_template_skeleton(description: str, concepts: List[str]) -> str:
    """生成模板骨架"""
    skeleton = f"""# {extract_strategy_name(description)}

{description}

## 策略逻辑

### 1. 技术分析框架
"""

    if "缠论" in concepts:
        skeleton += """
#### 缠论分析
- **笔的识别**: 识别K线顶底分型，连接成笔
- **线段形成**: 通过笔的组合形成线段
- **中枢分析**: 识别价格震荡区间
- **背驰检测**: 比较走势力度变化
"""

    if "MACD" in concepts:
        skeleton += """
#### MACD确认
- **趋势判断**: DIF和DEA金叉死叉
- **力度确认**: 柱状图变化
- **背离检测**: 价格与指标背离
"""

    # 添加执行指令部分
    skeleton += f"""

## 执行指令

```python
from skills import (
    get_multi_timeframe_data,
    {{ generate_skill_imports(concepts) }}
)

# 获取市场数据
data = get_multi_timeframe_data(
    symbols={{ parameters.symbol_pool | tojson }},
    intervals=["daily"],
    lookback_days={{ parameters.lookback_days }}
)

# 应用策略分析
{{ generate_strategy_code(concepts) }}

# 生成交易信号
signals = generate_trading_signals(
    analysis_result=analysis,
    min_confidence={{ parameters.min_confidence }}
)

return signals
```

## 输出格式

返回标准交易信号格式：
```json
{
  "signal": "SHORT_PUT_SPREAD|SHORT_CALL_SPREAD|IRON_CONDOR|NO_TRADE",
  "target": "SYMBOL",
  "confidence": 0.80,
  "reasoning": "详细分析理由...",
  "params": {...}
}
```
"""
    return skeleton
```

#### 2.2 缠论策略模板示例
**增强后的缠论模板** (`templates/chan_lun_strategy.md`)：
```markdown
# 缠论趋势跟踪策略

基于缠论分析原理，识别K线笔段结构，结合技术指标确认买卖点的高概率交易策略。

## 策略参数

- **symbol_pool**: 标的池 {{ parameters.symbol_pool|join(', ') }}
- **lookback_days**: K线分析周期 {{ parameters.lookback_days }}天
- **min_pen_bars**: 笔的最小K线数 {{ parameters.min_pen_bars }}根
- **pivot_strength**: 分型确认强度 {{ parameters.pivot_strength }}
- **volume_threshold**: 成交量确认阈值 {{ parameters.volume_threshold }}
- **min_confidence**: 最低置信度 {{ parameters.min_confidence }}

## 缠论核心分析

### 1. 分型识别与笔的构建
```python
from skills import (
    get_multi_timeframe_data,
    identify_chanlun_fractals,
    build_pen_segments,
    analyze_pivots
)

# 识别顶底分型
fractals = identify_chanlun_fractals(
    bars=daily_bars,
    min_strength={{ parameters.pivot_strength }}
)

# 构建笔段
pens = build_pen_segments(
    fractals=fractals,
    min_bars={{ parameters.min_pen_bars }}
)

# 分析分型强弱
pivot_strength = analyze_pivots(fractals, pens)
```

### 2. 线段与中枢分析
```python
from skills import (
    build_segments_from_pens,
    identify_zhongshu,
    detect_breakouts
)

# 由笔构建线段
segments = build_segments_from_pens(pens)

# 识别中枢震荡
zhongshu = identify_zhongshu(segments)

# 检测中枢突破
breakout_signals = detect_breakouts(
    segments=segments,
    zhongshu=zhongshu,
    volume_threshold={{ parameters.volume_threshold }}
)
```

### 3. 背驰与力度分析
```python
from skills import (
    calculate_momentum_divergence,
    analyze_trend_strength,
    measure_price_momentum
)

# 计算动量背驰
divergence = calculate_momentum_divergence(
    price_data=daily_bars,
    segments=segments
)

# 分析趋势强度
trend_strength = analyze_trend_strength(
    current_segment=segments[-1] if segments else None,
    historical_segments=segments[:-1]
)
```

### 4. 多指标确认体系
```python
from skills import (
    calculate_macd,
    calculate_rsi,
    calculate_volume_profile,
    confirm_signals
)

# MACD趋势确认
macd_result = calculate_macd(daily_bars, fast=12, slow=26, signal=9)

# RSI动量确认
rsi_result = calculate_rsi(daily_bars, period=14)

# 成交量分析
volume_profile = calculate_volume_profile(daily_bars)

# 多指标信号确认
confirmed_signals = confirm_signals(
    breakout_signals=breakout_signals,
    macd_result=macd_result,
    rsi_result=rsi_result,
    volume_profile=volume_profile,
    min_confirmation=3  # 至少3个指标确认
)
```

## 信号生成逻辑

### 做多信号条件
1. **缠论结构**: 向上突破中枢上轨
2. **MACD确认**: DIF上穿DEA，柱状图由负转正
3. **成交量确认**: 突破时成交量放大 {{ parameters.volume_threshold }}%以上
4. **趋势强度**: 当前线段力度大于前一线段
5. **背驰状态**: 无明显顶背驰信号

### 做空信号条件
1. **缠论结构**: 向下突破中枢下轨
2. **MACD确认**: DIF下穿DEA，柱状图由正转负
3. **成交量确认**: 突破时成交量放大 {{ parameters.volume_threshold }}%以上
4. **趋势强度**: 当前线段力度大于前一线段
5. **背驰状态**: 无明显底背驰信号

## 期权策略选择

### 强势突破信号 → SHORT_CALL_SPREAD
- 在突破价位上方选择看涨价差
- 捕获趋势延续的权利金收益

### 弱势反弹信号 → SHORT_PUT_SPREAD
- 在支撑位上方选择看跌价差
- 利用反弹卖出虚值看跌期权

### 横盘整理信号 → IRON_CONDOR
- 在中枢上下轨构建铁鹰价差
- 收取时间价值，等待突破

### 信号不足 → NO_TRADE
- 多指标确认不足
- 缠论结构不清晰
- 市场环境不确定

## 执行指令

```python
# 综合分析并生成交易信号
from skills import generate_option_signals, calculate_position_size

# 汇总所有分析结果
analysis_summary = {
    "fractals": fractals,
    "pens": pens,
    "segments": segments,
    "zhongshu": zhongshu,
    "breakout_signals": breakout_signals,
    "macd_result": macd_result,
    "rsi_result": rsi_result,
    "confirmed_signals": confirmed_signals,
    "divergence": divergence,
    "trend_strength": trend_strength
}

# 生成期权交易信号
option_signals = generate_option_signals(
    analysis_data=analysis_summary,
    symbol_pool={{ parameters.symbol_pool | tojson }},
    min_confidence={{ parameters.min_confidence }},
    strategy_type="defined_risk_only"
)

# 计算建议仓位大小
for signal in option_signals:
    if signal['signal'] != 'NO_TRADE':
        position_size = calculate_position_size(
            signal=signal,
            account_risk_per_trade=0.02,  # 每笔交易风险2%
            max_position_size=2000
        )
        signal['suggested_position_size'] = position_size

return option_signals
```

## 输出格式要求

必须返回严格遵循以下格式的JSON数组：

```json
[
  {
    "signal": "SHORT_PUT_SPREAD",
    "target": "NVDA",
    "confidence": 0.82,
    "reasoning": "缠论显示向上突破中枢上轨$145，MACD金叉确认，成交量放大45%。结构完整，无背驰信号。",
    "params": {
      "legs": [...],
      "max_risk": 400,
      "capital_required": 500,
      "suggested_position_size": 2
    },
    "technical_analysis": {
      "zhongshu_breakout": true,
      "macd_confirmation": true,
      "volume_confirmation": true,
      "divergence_check": "none"
    }
  }
]
```

## 市场数据

当前市场数据快照：

```json
{{ market_data|tojson(indent=2) }}
```
```

### 第三阶段：工具和验证

#### 3.1 策略验证工具
```python
# swarm_intelligence/template_validator.py

def validate_template_syntax(template_path: str) -> Dict:
    """验证模板语法正确性"""
    errors = []
    warnings = []

    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查必需章节
    required_sections = ['策略参数', '执行指令', '输出格式']
    for section in required_sections:
        if section not in content:
            errors.append(f"缺少必需章节: {section}")

    # 检查Jinja2语法
    try:
        from jinja2 import Template
        Template(content)
    except Exception as e:
        errors.append(f"Jinja2模板语法错误: {str(e)}")

    # 检查技能导入
    import re
    skill_imports = re.findall(r'from skills import \((.*?)\)', content, re.DOTALL)
    if not skill_imports:
        warnings.append("未发现技能导入语句")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

def validate_parameters_syntax(parameters_path: str) -> Dict:
    """验证参数配置语法正确性"""
    errors = []
    warnings = []

    try:
        import json
        with open(parameters_path, 'r', encoding='utf-8') as f:
            params = json.load(f)

        # 检查必需字段
        required_fields = ['id', 'sector', 'template', 'parameters']
        for field in required_fields:
            if field not in params:
                errors.append(f"缺少必需字段: {field}")

        # 检查模板文件存在
        template_path = f"swarm_intelligence/templates/{params.get('template', '')}"
        if not os.path.exists(template_path):
            warnings.append(f"模板文件不存在: {template_path}")

    except json.JSONDecodeError as e:
        errors.append(f"JSON格式错误: {str(e)}")
    except Exception as e:
        errors.append(f"参数文件读取错误: {str(e)}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
```

#### 3.2 策略执行监控
```python
# swarm_intelligence/execution_monitor.py

class StrategyExecutionMonitor:
    def __init__(self):
        self.execution_history = []
        self.performance_metrics = {}

    def log_execution(self, strategy_id: str, execution_result: Dict):
        """记录策略执行结果"""
        execution_record = {
            "timestamp": datetime.now().isoformat(),
            "strategy_id": strategy_id,
            "signals_generated": len(execution_result.get('signals', [])),
            "high_confidence_signals": len([
                s for s in execution_result.get('signals', [])
                if s.get('confidence', 0) >= 0.80
            ]),
            "execution_time": execution_result.get('execution_time', 0),
            "errors": execution_result.get('errors', [])
        }

        self.execution_history.append(execution_record)

        # 更新性能指标
        self.update_performance_metrics(strategy_id, execution_record)

    def get_performance_report(self, strategy_id: str = None) -> Dict:
        """获取性能报告"""
        if strategy_id:
            records = [r for r in self.execution_history if r['strategy_id'] == strategy_id]
        else:
            records = self.execution_history

        if not records:
            return {"message": "暂无执行记录"}

        return {
            "total_executions": len(records),
            "avg_signals_per_execution": sum(r['signals_generated'] for r in records) / len(records),
            "avg_high_confidence_rate": sum(
                r['high_confidence_signals'] / max(r['signals_generated'], 1) for r in records
            ) / len(records),
            "avg_execution_time": sum(r['execution_time'] for r in records) / len(records),
            "error_rate": sum(1 for r in records if r['errors']) / len(records)
        }
```

## 预期收益

### 用户体验提升
- **调用简化**: 从复杂的Python import → 一行Slash Command
- **策略创建**: 自然语言描述 → 自动生成模板+参数
- **调试友好**: 更好的错误信息和执行状态
- **监控完善**: 执行历史和性能统计

### 开发效率提升
- **保持架构**: 不破坏现有优秀的Template + Parameters设计
- **渐进增强**: 新功能与现有功能共存
- **模板辅助**: 自动生成模板骨架和参数建议
- **验证工具**: 自动检查语法和逻辑错误

### 系统健壮性
- **向后兼容**: 现有策略继续正常工作
- **错误隔离**: 新功能不影响现有功能
- **版本管理**: 支持策略模板的版本控制
- **A/B测试**: 支持多个策略版本并行测试

## 实施计划

### 第一周：Slash Command基础 (2-3天)
1. 创建核心 trading commands 结构
2. 实现 `/trade-analysis` 和 `/market-health`
3. 基础参数解析和错误处理
4. 集成测试和验证

### 第二周：策略执行增强 (3-4天)
1. 实现 `/strategy-run` 和 `/strategy-list`
2. 增强策略实例管理
3. 添加执行监控和性能统计
4. 优化错误处理和用户反馈

### 第三周：自然语言策略创建 (3-4天)
1. 实现 `/create-strategy` 核心逻辑
2. 策略描述解析和概念提取
3. 模板自动生成和参数建议
4. 验证工具和语法检查

### 第四周：完善和优化 (2-3天)
1. 缠论策略模板增强示例
2. 用户文档和使用指南
3. 性能优化和错误修复
4. 全面测试和用户验收

**总计：10-14天**

## 风险控制

### 技术风险
- **复杂性控制**: 新功能不增加原有系统复杂度
- **性能影响**: Slash Command响应时间控制在1秒内
- **兼容性保证**: 确保现有策略100%继续工作

### 实施风险
- **渐进式发布**: 分阶段实施，每个阶段独立可用
- **回滚机制**: 保持原有调用方式作为备用方案
- **用户培训**: 提供详细的使用文档和示例

## 成功指标

### 功能指标
- [ ] 所有核心技能都有对应的Slash Command
- [ ] 策略创建时间减少80% (从手动编写到自动生成)
- [ ] 新手用户创建第一个策略的时间 < 5分钟
- [ ] 100%向后兼容性

### 性能指标
- [ ] Slash Command响应时间 < 1秒
- [ ] 策略执行时间与原方式相比 < 110%
- [ ] 内存使用增长 < 20MB

### 用户体验指标
- [ ] 用户满意度 > 4.5/5
- [ ] 错误率降低70%
- [ ] 策略创建成功率 > 95%