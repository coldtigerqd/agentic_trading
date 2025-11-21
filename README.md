# 产品规格书: Agentic AlphaHive Runtime

**日期**: 2025年11月21日
**架构类型**: 基于 Claude Code 的递归式自治交易系统 (Recursive Autonomous Trading System)
**核心协议**: Model Context Protocol (MCP) + Slash Commands
**版本**: v3.0 - Slash Command Integration

-----

## 1\. 系统概述 (System Overview)

**Agentic AlphaHive** 是一个无头（Headless）、非交互式的量化交易运行时环境。它不依赖传统的 Web 后端架构，而是以 **Claude Code** 为操作系统内核，通过 **MCP 协议** 连接外部金融设施，并集成了 **Slash Command 系统** 提供一键式交易操作。

系统的核心是一个"递归智能体"结构：主 Agent（指挥官）通过 **Slash Commands** 或 Python Skill（技能）来并发调度底层的 **Alpha Swarm（分析蜂群）**。系统具备参数与逻辑分离的架构，支持通过修改配置文件的"梦境进化"、自然语言策略创建，并配备独立于 AI 之外的"看门狗"进程以确保绝对安全。

**v3.0 重大更新**：引入 Slash Command 系统，将复杂的 Python 技能调用简化为单行命令，同时保持完整的 Template + Parameters 架构优势。

-----

## 2\. 目录结构 (Directory Structure)

系统文件结构遵循“逻辑即配置，代码即工具”的设计原则。

```text
agentic-alphahive/
├── .clauderc.json             # Claude Code 运行时权限与环境配置
├── .env                       # 敏感凭证 (IBKR API, ThetaData Key)
│
├── 🧠 prompts/                # [系统灵魂]
│   └── commander_system.md    # 主指挥官的 System Prompt (定义最高指令与决策流)
│
├── 🛠️ skills/                 # [核心能力] 注册给 Claude 的 Python 函数库
│   ├── __init__.py
│   ├── swarm_core.py          # [递归引擎] 封装了 AsyncIO 并发调度的核心 Skill
│   ├── math_core.py           # 确定性数学计算 (BS模型, 凯利公式)
│   └── execution_gate.py      # 订单构建与参数校验
│
├── ⚡ .claude/commands/        # [v3.0新增] Slash Command 系统
│   └── trading/               # 交易命令目录
│       ├── trade-analysis.md  # 完整交易分析命令
│       ├── market-health.md   # 市场健康检查命令
│       ├── risk-check.md      # 风险分析命令
│       ├── strategy-run.md    # 策略执行命令
│       ├── strategy-list.md   # 策略列表命令
│       ├── create-strategy.md # 自然语言策略创建
│       └── trading-help.md    # 命令帮助系统
│
├── 🐝 swarm_intelligence/     # [蜂群大脑] 参数与逻辑解耦区
│   ├── templates/             # [逻辑模版] Jinja2 格式的 Markdown (.md)
│   │   ├── vol_sniper.md
│   │   ├── news_sentiment.md
│   │   └── chan_lun_enhanced.md  # [v3.0新增] 增强版缠论策略模板
│   ├── active_instances/      # [实盘配置] 纯 JSON 参数文件
│   │   ├── tech_aggressive.json (指向 vol_sniper, threshold=80)
│   │   ├── finance_conservative.json (指向 vol_sniper, threshold=90)
│   │   └── chan_lun_tech_enhanced.json  # [v3.0新增] 缠论增强策略实例
│   ├── strategy_factory.py    # [v3.0新增] 自然语言策略创建引擎
│   └── execution_monitor.py   # [v3.0新增] 策略执行监控与性能分析
│
├── 🔌 mcp_servers/            # [感知与手脚] 标准 MCP 服务
│   ├── ibkr/                  # 交易执行与资金查询
│   ├── thetadata/             # thetadata official MCP server, which was pre-installed in the environment
│   └── memory/                # 长期记忆存取
│
├── 💾 data_lake/              # [数据黑匣子]
│   ├── snapshots/             # 决策现场还原 (Input Context Snapshots)
│   └── trades.db              # 结构化交易记录 (SQLite)
│
├── 🛌 dream_lab/              # [进化车间]
│   ├── optimizer.py           # 遗传算法引擎 (只修改 JSON 配置)
│   └── backtester.py          # 快速回测器
│
├── 📚 docs/                   # [v3.0新增] 用户文档
│   └── slash-command-guide.md # Slash Command 使用指南
│
└── 🚀 runtime/                # [运行环境]
    ├── main_loop.py           # 主唤醒循环 (Cron / Loop)
    └── watchdog.py            # [独立进程] 死手风控系统
```

-----

## 3\. 稳定执行架构 [v3.0 新增]

### 3.1 问题解决背景

用户反馈执行稳定性问题：
> "很奇怪，trading脚本执行之后，经常会使用bash执行一大段代码，是否能够明确使用某些脚本就好了，现在这种看起来很不稳定"

**解决方案**：创建了独立的Python脚本替代不稳定的bash执行，确保系统稳定可靠。

### 3.2 稳定脚本架构

**核心改进**：
- **之前**: `bash -c "大段Python代码"` - 不稳定，难以调试
- **现在**: `python scripts/name.py [参数]` - 稳定，易维护

#### 3.2.1 核心稳定脚本

```text
scripts/
├── market_health.py              # 市场健康检查脚本
├── trade_analysis.py             # 交易分析脚本
├── strategy_runner.py            # 策略运行器脚本
├── risk_check.py                 # 风险检查脚本
├── README.md                     # 脚本使用说明
└── SLASH_COMMAND_INTEGRATION.md  # 集成完成报告
```

#### 3.2.2 稳定性特性

每个稳定脚本具备以下特性：
- ✅ **完整参数验证** - 使用argparse进行严格的输入验证
- ✅ **错误处理机制** - 异常捕获和用户友好错误信息
- ✅ **语法检查** - Python解释器预检查语法错误
- ✅ **统一输出格式** - 支持表格和JSON两种输出格式
- ✅ **中文本地化** - 完整的中文用户界面
- ✅ **帮助文档** - 每个脚本都有`--help`支持

### 3.3 Slash Command 系统

Slash Command 系统是基于稳定脚本的用户界面层增强，将复杂操作简化为直观命令。

#### 3.3.1 命令到脚本映射

| Slash Command | 稳定脚本 | 主要功能 |
|---------------|----------|----------|
| `/trade-analysis` | `scripts/trade_analysis.py` | 完整交易分析流程 |
| `/strategy-run` | `scripts/strategy_runner.py` | 策略执行和信号生成 |
| `/market-health` | `scripts/market_health.py` | 市场健康状态检查 |
| `/risk-check` | `scripts/risk_check.py` | 持仓风险评估 |
| `/trading-help` | - | 帮助系统 |

#### 3.3.2 核心设计原则

- **零破坏性**：现有策略和技能无需任何修改
- **稳定执行**：完全避免bash执行大段代码
- **一键执行**：复杂的操作简化为单行命令
- **中文友好**：所有用户界面完全中文化
- **渐进增强**：用户可以选择传统方式或新命令方式

### 3.4 命令体系概览

#### 3.4.1 核心交易命令

```bash
# 完整交易分析 - 替代复杂的 Python 导入和调用
/trade-analysis                           # 默认参数执行
/trade-analysis --sectors TECH,FINANCE   # 指定板块
/trade-analysis --min-confidence 0.80    # 设置置信度阈值
/trade-analysis --dry-run               # 仅分析不执行

# 市场健康检查 - 快速评估市场状态
/market-health                          # 基础检查
/market-health --detailed               # 详细分析
/market-health --data-quality           # 数据质量评估

# 风险分析 - 持仓风险评估和管理
/risk-check                             # 所有持仓风险
/risk-check --symbol AAPL               # 特定标的
/risk-check --recommendations-only      # 仅显示操作建议
```

#### 3.4.2 策略管理命令

```bash
# 策略执行 - 运行特定策略实例
/strategy-run tech_aggressive            # 运行策略
/strategy-run finance_conservative --verbose --timing  # 详细模式
/strategy-run strategy_name --dry-run   # 仅生成信号

# 策略列表 - 查看和管理策略
/strategy-list                          # 列出所有策略
/strategy-list --detailed               # 详细信息
/strategy-list --performance            # 性能数据
/strategy-list --sector TECH            # 按板块筛选
```

#### 3.4.3 自然语言策略创建

```bash
# 中文自然语言策略创建 - 无需编写代码
/create-strategy "使用缠论原理分析最近30天的K线图，识别笔和线段"
/create-strategy "基于RSI超买超卖的科技股均值回归策略" --name rsi_mean_reversion
/create-strategy "双均线交叉策略" --sector TECH --dry-run  # 预览模式
```

### 3.5 实现架构

#### 3.5.1 稳定脚本集成

所有slash command现在都调用独立的稳定Python脚本，确保执行可靠性：

```python
# 命令内部实现（以 trade-analysis 为例）
def execute_command(params):
    # 调用稳定脚本而非内联代码
    cmd = [
        'python', 'scripts/trade_analysis.py',
        '--sectors', params.sectors,
        '--min-confidence', str(params.min_confidence),
        '--format', 'json'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)
```

#### 3.5.2 命令发现机制

命令文件位于 `.claude/commands/trading/` 目录下，所有命令都已更新使用稳定脚本：

```
.claude/commands/trading/
├── trade-analysis.md     # 核心交易分析命令 (已更新)
├── market-health.md      # 市场健康检查 (已更新)
├── risk-check.md         # 风险分析 (已更新)
├── strategy-run.md       # 策略执行 (已更新)
├── strategy-list.md      # 策略列表
├── create-strategy.md    # 自然语言策略创建
└── trading-help.md       # 帮助系统
```

#### 3.5.3 智能参数解析

每个稳定脚本支持丰富的参数组合，并自动进行类型验证和错误处理：

```bash
# 参数类型自动识别和转换
/trade-analysis --min-confidence 0.85 --max-orders 3 --skip-sync

# 错误处理和用户友好提示
/trade-analysis --min-confidence invalid
# ❌ 错误: 置信度必须是 0.0-1.0 之间的数字
```

#### 3.5.4 与现有技能的无缝集成

稳定脚本完全基于现有的 Python 技能，保持架构一致性：

```python
# 稳定脚本内部实现（以 trade_analysis.py 为例）
from skills.workflow_skills import run_full_trading_analysis

def main():
    args = parse_arguments()
    result = run_full_trading_analysis(
        sectors=sectors,
        min_confidence=args.min_confidence,
        max_orders_per_run=args.max_orders
    )
    format_output(result)
```

### 3.6 自然语言处理引擎

#### 3.6.1 策略概念提取

`swarm_intelligence/strategy_factory.py` 实现了强大的自然语言理解能力：

```python
# 交易概念字典
TRADING_CONCEPTS = {
    '技术分析': ['缠论', 'MACD', 'RSI', 'KDJ', '布林带'],
    '策略类型': ['均值回归', '动量策略', '套利策略', '趋势跟踪'],
    '市场环境': ['牛市', '熊市', '震荡市', '高波动'],
    '时间周期': ['日内', '短线', '中线', '长线']
}
```

#### 3.6.2 模板自动生成

基于提取的概念自动选择最合适的模板并生成参数建议：

```python
# 输入: "使用缠论原理分析科技股，结合MACD确认"
# 输出:
{
    "template": "chan_lun_enhanced.md",
    "suggested_parameters": {
        "symbol_pool": ["AAPL", "NVDA", "MSFT"],
        "lookback_days": 30,
        "indicators": ["MACD", "RSI", "VOLUME"]
    }
}
```

### 3.7 性能监控与执行追踪

#### 3.7.1 策略执行监控

`swarm_intelligence/execution_monitor.py` 提供全面的性能追踪：

```python
# 执行历史记录
execution_history = {
    "strategy_id": "tech_aggressive",
    "execution_time": "2025-11-21T10:30:00Z",
    "signals_generated": 5,
    "success_rate": 0.80,
    "execution_duration_ms": 1250
}
```

#### 3.7.2 性能指标

- **响应时间**: 命令执行时间 < 1秒（缓存命中）
- **成功率**: 策略创建成功率 > 95%
- **内存效率**: 相比基线增加 < 20MB
- **向后兼容**: 现有 Python 调用方式性能无变化

### 3.8 用户文档与帮助系统

#### 3.8.1 综合用户指南

`docs/slash-command-guide.md` 提供：
- 完整的使用示例和最佳实践
- 错误处理和故障排除指南
- 自动化脚本和工作流程示例
- 中文本地化界面

#### 3.8.2 内置帮助系统

```bash
# 总体帮助
/trading-help

# 特定命令帮助
/trade-analysis --help
/strategy-run --help
/create-strategy --help
```

### 3.9 最佳实践

#### 3.9.1 推荐工作流

```bash
# 日常交易流程
/market-health                    # 1. 检查市场状态
/risk-check                       # 2. 评估持仓风险
/trade-analysis --min-confidence 0.80  # 3. 执行交易分析
/strategy-list --performance      # 4. 查看策略表现
```

#### 3.9.2 稳定性保证

所有slash command现在都具备以下稳定性保证：

- ✅ **无bash执行** - 完全避免`bash -c "大段代码"`的不稳定性
- ✅ **错误隔离** - 单个脚本错误不影响其他命令
- ✅ **参数验证** - 严格的输入验证防止无效参数
- ✅ **资源管理** - 合理的内存和CPU使用
- ✅ **可测试性** - 每个脚本都可以独立测试

#### 3.9.3 自动化脚本示例

```bash
#!/bin/bash
# 每日市场检查脚本
echo "=== 每日市场检查 ==="

market_status=$(/market-health --json | jq -r '.status')
if [ "$market_status" == "健康" ]; then
    echo "✅ 市场状态良好"
    risk_score=$(/risk-check --json | jq -r '.risk_score')
    if [ "$risk_score" -lt 70 ]; then
        echo "✅ 风险水平可接受"
        /trade-analysis --min-confidence 0.75
    else
        echo "⚠️ 风险水平较高，建议优先处理持仓"
    fi
else
    echo "❌ 市场状态不适合交易"
fi
```

-----

## 4\. 核心模块详述 (Functional Modules)

### 4.1 递归蜂群引擎 (Recursive Swarm Engine)

**实现位置**: `skills/swarm_core.py`

这是系统将“并发 Agent”封装为“单一 Skill”的关键模块。

  * **输入**: 主 Agent 调用 `consult_swarm(sector="ALL")`。
  * **处理流程**:
    1.  **加载配置**: 扫描 `active_instances/` 下的所有 JSON 文件。
    2.  **渲染逻辑**: 读取 JSON 中指定的 `template` 路径，将参数（如阈值、标的池）注入 Markdown 模版，生成具体的 Prompt。
    3.  **并发推理**: 使用 `asyncio` 启动数十个并发的 LLM API 请求（Sub-agents），将渲染后的 Prompt 连同当前市场快照发给 API。
    4.  **数据快照**: 强制将本次所有 Sub-agents 接收到的输入数据序列化并存入 `data_lake/snapshots/`，用于事后复盘。
  * **输出**: 向主 Agent 返回一个清洗后的、标准化的信号列表 JSON。

### 3.2 指挥与执行 (Orchestration & Execution)

**实现位置**: Claude Code Runtime & `skills/execution_gate.py`

  * **指挥官 (Claude Code)**: 负责高级推理。它接收蜂群的信号列表，结合当前宏观环境和资金状态，进行最终的战略决策（Go/No-Go）。
  * **执行基元 (Primitives)**: 指挥官不直接生成下单代码，而是调用 `execution_gate.place_order_with_guard()`。该函数内部包含：
      * 参数合规性检查。
      * 算法订单参数封装（如 IBKR Adaptive Algo）。

### 3.3 梦境进化 (Dream Mode Evolution)

**实现位置**: `dream_lab/optimizer.py`

系统利用非交易时间进行自我迭代，且采用**参数突变**而非代码重写的方式，确保稳定性。

  * **评估**: 扫描 `trades.db`，计算每个 Instance（配置文件）的 Sharpe Ratio。
  * **变异**: 对表现不佳的 Instance 对应的 JSON 文件进行修改（例如：将 `iv_threshold` 从 80 调整为 85，或将 `stop_loss` 从 5% 调整为 3%）。
  * **验证**: 使用历史快照数据回测新配置，若更优则覆盖原 JSON。

### 3.4 独立看门狗 (Independent Watchdog)

**实现位置**: `runtime/watchdog.py`

一个完全独立于 AI 运行时的 Python 守护进程。

  * **连接**: 拥有独立的 IBKR API 连接句柄。
  * **心跳监测**: 监控 `main_loop.py` 的活跃状态，若 AI 进程死锁超过 60 秒，发送报警。
  * **资产熔断**: 轮询账户 `NetLiquidation`。若当日回撤 \> N%（硬编码），立即触发 **Panic Close**，强制平掉所有仓位并向用户发送紧急通知。

### 3.5 市场数据缓存 (Market Data Cache)

**实现位置**: `data_lake/market_data_manager.py`, `skills/market_data.py`, `runtime/data_fetcher.py`

高性能历史数据缓存系统，为回测和策略分析提供快速数据访问。

  * **存储架构**:
      * 基础粒度：5分钟 OHLCV K线数据
      * 缓存周期：最近3年历史数据
      * 存储容量：~500MB（50个标的 × 3年）
      * 动态聚合：支持即时聚合为 15分钟、1小时、日线级别

  * **观察列表 (Watchlist)**:
      * 动态管理：通过 `add_to_watchlist(symbol, priority)` 添加监控标的
      * 优先级更新：高优先级标的优先更新数据
      * 初始列表：SPY, QQQ, IWM, DIA, XLF, XLE, XLK, AAPL, NVDA, TSLA（10个核心标的）

  * **后台更新器**:
      * 更新频率：交易时段每5分钟自动更新
      * 非阻塞式：使用 asyncio 异步任务，不影响主交易逻辑
      * 交易时间检测：仅在美东时间 09:30-16:00（周一至周五）运行

  * **数据获取策略**:
      * 懒加载（Lazy Backfill）：首次查询时按需拉取历史数据
      * 增量更新：只拉取最新的增量数据，降低 API 调用
      * 指数退避重试：API 失败时采用 1s, 2s, 4s, 8s, 16s 递增重试

  * **Skill 接口**:
      ```python
      # 获取历史K线
      bars = get_historical_bars("AAPL", interval="5min", lookback_days=30)

      # 多时间框架分析
      mtf_data = get_multi_timeframe_data("NVDA", intervals=["5min", "1h", "daily"], lookback_days=30)

      # 获取最新价格
      latest = get_latest_price("SPY")

      # 管理观察列表
      add_to_watchlist("TSLA", priority=8, notes="High momentum")
      watchlist = get_watchlist()
      ```

  * **数据质量指标**:
      * `cache_hit`: 缓存命中率（预期数据覆盖率 ≥80%）
      * `freshness_seconds`: 数据新鲜度（最新K线距今秒数）
      * `gaps_detected`: 数据缺口检测（识别缺失的K线区间）
      * `query_time_ms`: 查询性能（目标 <10ms for 30天回溯）

  * **与蜂群集成**:
      * 蜂群可直接调用 `get_historical_bars()` 获取技术分析所需的历史数据
      * 多时间框架数据支持趋势识别和形态识别策略
      * 数据缓存极大降低了 ThetaData API 调用，提升策略分析速度

-----

## 4\. 数据流与交互协议 (Data Flow)

### 4.1 信号协议 (Signal Protocol)

蜂群（Skill）返回给指挥官的标准 JSON 格式：

```json
[
  {
    "instance_id": "tech_aggressive",
    "template_used": "vol_sniper",
    "target": "NVDA",
    "signal": "SHORT_PUT_SPREAD",
    "params": {"strike_short": 120, "strike_long": 115, "expiry": "20251128"},
    "confidence": 0.88,
    "reasoning": "Skew exceeds 2-sigma, earnings risk implies mean reversion."
  }
]
```

### 4.2 配置协议 (Configuration Protocol)

`active_instances/` 下的 JSON 配置文件示例：

```json
{
  "id": "tech_aggressive",
  "template": "vol_sniper.md",
  "parameters": {
    "symbol_pool": ["NVDA", "AMD", "TSLA"],
    "min_iv_rank": 80,
    "max_delta_exposure": 0.30,
    "sentiment_filter": "neutral_or_better"
  },
  "evolution_history": {
    "generation": 5,
    "last_mutated": "2025-11-18"
  }
}
```

-----

## 5\. 运行生命周期 (Lifecycle)

1.  **启动**: `runtime/watchdog.py` 先行启动，随后 `runtime/main_loop.py` 唤醒 Claude Code。
2.  **感知**: Claude Code 调用 `mcp-ibkr` 获取账户状态。
3.  **思考**: Claude Code 调用 `skills.consult_swarm()`。
      * *Swarm Skill 内部并发运行所有 Instances，存快照，返回信号。*
4.  **决策**: Claude Code 评估信号，调用 `skills.math_core.kelly_criterion` 计算仓位。
5.  **行动**: Claude Code 调用 `skills.execution_gate` 发送订单。
6.  **休眠**: 系统挂起，等待下一周期。
7.  **进化**: 休市后，`dream_lab` 进程启动，优化 JSON 配置文件。

-----

## 6\. 脚本明细 (Scripts Reference)

系统提供了一系列脚本工具用于运行、测试和维护。所有脚本均使用 **REST API** 与 ThetaData 通信（而非过时的 MCP 方法）。

### 6.1 核心运行脚本

#### `runtime/main_loop.py`
**功能**: 主交易循环，唤醒 Commander 进行交易决策

**使用方法**:
```bash
# 运行主交易循环（前台）
python runtime/main_loop.py

# 后台运行
nohup python runtime/main_loop.py > logs/main.log 2>&1 &
```

**说明**:
- 调用 Commander System Prompt 执行 SENSE-THINK-DECIDE-ACT 工作流
- 每个周期获取账户状态、咨询蜂群、执行订单
- 需要 IBKR Gateway 连接和环境变量配置

---

#### `runtime/watchdog.py`
**功能**: 独立看门狗进程，监控账户回撤并触发熔断器

**使用方法**:
```bash
# 单独启动看门狗
python runtime/watchdog.py

# 后台运行
nohup python runtime/watchdog.py > logs/watchdog.log 2>&1 &
```

**说明**:
- 独立进程运行，不依赖主循环
- 每60秒检查一次账户净值
- 回撤超过 10% 自动触发熔断器
- 使用独立的 IBKR 连接（client_id=999）

---

#### `runtime/data_sync_daemon.py`
**功能**: 数据同步守护进程，定期更新监控列表市场数据

**使用方法**:
```bash
# 前台运行（每10分钟同步一次）
python runtime/data_sync_daemon.py --interval 10

# 单次同步后退出
python runtime/data_sync_daemon.py --once

# 后台运行
nohup python runtime/data_sync_daemon.py --interval 10 > logs/data_sync.log 2>&1 &

# 使用 cron（每10分钟）
*/10 * * * * cd /path/to/agentic_trading && python runtime/data_sync_daemon.py --once
```

**说明**:
- ✅ 使用 REST API（httpx）获取数据，不依赖 MCP
- ✅ 增量更新：只获取新数据，自动去重
- ✅ 市场感知：只在交易时段主动同步
- ✅ 错误重试：网络失败自动重试

---

### 6.2 数据同步脚本

#### `scripts/demo_incremental_sync.py`
**功能**: 增量数据同步演示脚本，展示完整同步工作流

**使用方法**:
```bash
python scripts/demo_incremental_sync.py
```

**说明**:
- 演示如何使用 `skills` 模块进行增量同步
- 显示市场状态、数据新鲜度报告
- 可作为 Commander 工作流的参考

---

#### `scripts/run_sync_once.py`
**功能**: 一次性数据同步脚本，适合手动触发

**使用方法**:
```bash
python scripts/run_sync_once.py
```

**说明**:
- 执行一次完整的数据同步周期
- 更新所有监控列表中的股票数据
- 适合手动更新或 cron 任务

---

#### `scripts/sync_with_rest_api.py`
**功能**: 使用 REST API 的数据同步脚本，支持持续运行模式

**使用方法**:
```bash
# 单次同步
python scripts/sync_with_rest_api.py --once

# 持续运行（每10分钟）
python scripts/sync_with_rest_api.py --interval 10
```

**说明**:
- ✅ 直接通过 HTTP 请求获取数据，更稳定可靠
- 不依赖 MCP，使用 httpx.stream()
- 支持环境变量或 .env 文件配置 API 密钥

---

### 6.3 测试与验证脚本

#### `verify_setup.py`
**功能**: 系统设置验证脚本，测试所有核心组件

**使用方法**:
```bash
python verify_setup.py
```

**说明**:
- 测试技能库导入
- 验证数学函数（Kelly Criterion, Black-Scholes）
- 检查数据库连接
- 验证蜂群配置加载
- 测试 Commander 提示词
- 显示系统就绪状态

**预期输出**:
```
✅ All components verified successfully!

System Status:
  • Skills Library: Ready ✓
  • Data Persistence: Ready ✓
  • Swarm Intelligence: Ready ✓
  • Commander Prompt: Ready ✓
  • Safety Layer: Ready ✓
```

---

#### `test_template_localization.py`
**功能**: 模板本地化集成测试

**使用方法**:
```bash
python test_template_localization.py
```

**说明**:
- 验证所有蜂群策略模板正确渲染
- 检查实例配置文件结构
- 测试 Commander 提示词加载
- 验证中文字符编码（UTF-8）
- 确保 Jinja2 变量正确替换

---

#### `scripts/test_theta_fix.py`
**功能**: ThetaData API 修复验证测试

**使用方法**:
```bash
# 启动 Theta Terminal
java -jar ThetaTerminalv3.jar

# 运行测试
python scripts/test_theta_fix.py
```

**说明**:
- 测试 Quote Snapshot API
- 测试 OHLC Snapshot API
- 验证 CSV 解析是否匹配 ThetaData API 文档
- 需要 Theta Terminal 运行在 localhost:25503

---

#### `scripts/test_theta_terminal.py`
**功能**: Theta Terminal 连接测试

**使用方法**:
```bash
python scripts/test_theta_terminal.py
```

**说明**:
- 验证 Theta Terminal 是否正在运行
- 测试基本的 API 连接
- 快速健康检查工具

---

### 6.4 数据库种子脚本

#### `data_lake/seed_watchlist.py`
**功能**: 初始化监控列表数据

**使用方法**:
```bash
python -c "from data_lake.seed_watchlist import seed_default_watchlist; seed_default_watchlist()"
```

**说明**:
- 创建默认的监控列表（科技股、金融股等）
- 设置优先级和备注
- 首次设置系统时使用

---

### 6.5 脚本选择指南

| 使用场景 | 推荐脚本 |
|---------|---------|
| 启动交易系统 | `runtime/main_loop.py` |
| 启动安全监控 | `runtime/watchdog.py` |
| 定期数据同步 | `runtime/data_sync_daemon.py --interval 10` |
| 手动更新数据 | `scripts/run_sync_once.py` |
| 验证系统配置 | `verify_setup.py` |
| 测试 ThetaData 连接 | `scripts/test_theta_fix.py` |
| 测试模板本地化 | `test_template_localization.py` |
| 初始化监控列表 | `data_lake/seed_watchlist.py` |

---

### 6.6 已移除的过时脚本

以下脚本已被删除，因为它们使用了已弃用的 MCP 方法（已被 REST API 替代）：

- ❌ `runtime/data_fetcher.py` - 使用 MCP ThetaData 工具（已被 REST API 替代）
- ❌ `scripts/fetch_real_market_data.py` - 使用 MCP（功能已被 data_sync_daemon.py 替代）
- ❌ `scripts/incremental_data_sync.py` - 使用 MCP（功能已被 data_sync_daemon.py 替代）
- ❌ `scripts/populate_market_data.py` - 生成示例数据（不再需要，使用真实市场数据）
- ❌ `scripts/test_theta.py` - 基础测试（已被 test_theta_fix.py 替代）

**重要提示**: 所有新开发的脚本和工作流应该使用 **REST API**（通过 `skills.thetadata_client.fetch_snapshot_with_rest`）而不是 MCP ThetaData 工具。参见 `prompts/commander_system.md` 中的最新指导。