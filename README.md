# 产品规格书: Agentic AlphaHive Runtime

**日期**: 2025年11月19日
**架构类型**: 基于 Claude Code 的递归式自治交易系统 (Recursive Autonomous Trading System)
**核心协议**: Model Context Protocol (MCP)

-----

## 1\. 系统概述 (System Overview)

**Agentic AlphaHive** 是一个基于 **Claude Code** 的自主交易分析系统。它采用**手动命令触发**的交互模式，通过 **MCP 协议** 连接外部金融设施进行实时交易分析和执行。

**运行模式**: 通过 Claude Code 命令手动触发交易分析（如输入"请开始一次交易分析"），而非自动循环运行。

系统的核心是一个"递归智能体"结构：主 Agent（指挥官，Commander）通过调用 Python Skill（技能）来并发调度底层的 **Alpha Swarm（分析蜂群）**。系统具备参数与逻辑分离的架构，支持通过修改配置文件的"梦境进化"（未来功能），并配备独立于 AI 之外的"看门狗"进程监控账户风险。

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
├── 🐝 swarm_intelligence/     # [蜂群大脑] 参数与逻辑解耦区
│   ├── templates/             # [逻辑模版] Jinja2 格式的 Markdown (.md)
│   │   ├── vol_sniper.md
│   │   └── news_sentiment.md
│   └── active_instances/      # [实盘配置] 纯 JSON 参数文件
│       ├── tech_aggressive.json (指向 vol_sniper, threshold=80)
│       └── finance_conservative.json (指向 vol_sniper, threshold=90)
│
├── 🔌 mcp-servers/            # [感知与手脚] 标准 MCP 服务
│   └── ibkr/                  # 交易执行与资金查询 (MCP server)
│                              # 注: ThetaData 使用 REST API,不再使用 MCP
│
├── 💾 data_lake/              # [数据黑匣子]
│   ├── db_config.py           # 统一数据库配置
│   ├── db_helpers.py          # 交易与安全事件日志
│   ├── market_data_manager.py # 市场数据缓存管理
│   ├── snapshot_manager.py    # 决策快照管理
│   ├── seed_watchlist.py      # 监控列表初始化
│   ├── snapshots/             # 决策现场还原 (Input Context Snapshots)
│   └── trades.db              # 结构化交易记录 (SQLite)
│
└── 🚀 runtime/                # [运行环境]
    ├── data_sync_daemon.py    # 数据同步守护进程
    ├── watchdog.py            # [独立进程] 账户风险监控系统
    └── legacy/                # 已弃用的脚本
        └── main_loop.py       # (已弃用) 原自动循环模式
```

-----

## 3\. 核心模块详述 (Functional Modules)

### 3.1 递归蜂群引擎 (Recursive Swarm Engine)

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

**实现位置**: Claude Code Runtime & `skills/workflow_skills.py`, `skills/execution_gate.py`

  * **指挥官 (Claude Code)**: 负责高级推理。通过手动命令触发交易分析流程，接收蜂群的信号列表，结合当前宏观环境和资金状态，进行最终的战略决策（Go/No-Go）。
  * **工作流技能 (Workflow Skills)**: 提供高级工作流函数，如 `run_full_trading_analysis()`, `run_market_health_check()`, `run_position_risk_analysis()`，封装完整的分析流程。
  * **执行基元 (Primitives)**: 指挥官不直接生成下单代码，而是调用 `execution_gate.place_order_with_guard()`。该函数内部包含：
      * 参数合规性检查。
      * 安全限额验证（单笔风险 ≤$500，资金 ≤$2,000）。
      * 算法订单参数封装（如 IBKR Adaptive Algo）。

### 3.3 独立看门狗 (Independent Watchdog)

**实现位置**: `runtime/watchdog.py`

一个完全独立于 AI 运行时的 Python 守护进程。

  * **连接**: 拥有独立的 IBKR API 连接句柄。
  * **资产熔断**: 轮询账户 `NetLiquidation`。若当日回撤 ≥10%（硬编码），立即触发 **Panic Close**，强制平掉所有仓位并向用户发送紧急通知。
  * **注**: 手动命令模式下不再需要心跳监测，进程状态由 Claude Code 管理。

### 3.4 市场数据缓存 (Market Data Cache)

**实现位置**: `data_lake/market_data_manager.py`, `skills/thetadata_client.py`, `runtime/data_sync_daemon.py`

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
      * 使用 **REST API** 直接与 ThetaData 通信（不再使用 MCP）
      * 懒加载（Lazy Backfill）：首次查询时按需拉取历史数据
      * 增量更新：只拉取最新的增量数据，降低 API 调用
      * 指数退避重试：API 失败时采用 1s, 2s, 4s, 8s, 16s 递增重试

  * **数据访问接口**:
      ```python
      # 通过 data_lake 模块访问
      from data_lake import insert_bars, get_bars, get_latest_bar

      # 或通过 workflow skills 访问
      # run_full_trading_analysis() 会自动处理数据同步
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

**手动命令触发模式** (Manual Command-Triggered Mode):

1.  **准备**: 确保 `runtime/watchdog.py` 在后台运行（可选，用于账户熔断监控）。
2.  **触发**: 用户在 Claude Code 中输入命令，如"请开始一次交易分析"。
3.  **健康检查**: Commander 调用 `run_market_health_check()` 检查市场状态和数据质量。
4.  **分析**: Commander 调用 `run_full_trading_analysis()`：
      * 内部调用 `skills.consult_swarm()` 并发运行所有蜂群实例
      * 存储决策快照到 `data_lake/snapshots/`
      * 返回过滤后的高置信信号列表
5.  **决策**: Commander 评估信号，调用 `skills.math_core.kelly_criterion` 计算仓位大小。
6.  **执行**: Commander 调用 `skills.execution_gate.place_order_with_guard()` 提交订单。
      * 订单经过安全层验证（风险限额、集中度检查）
      * 验证通过后发送至 IBKR
7.  **记录**: 交易结果和决策日志自动存入 `data_lake/trades.db`。
8.  **待命**: 系统等待下次用户命令触发。

**后台数据同步** (可选):
- 运行 `runtime/data_sync_daemon.py` 在非交易时段自动更新市场数据缓存。

-----

## 6\. 脚本明细 (Scripts Reference)

系统提供了一系列脚本工具用于运行、测试和维护。所有脚本均使用 **REST API** 与 ThetaData 通信（而非过时的 MCP 方法）。

### 6.1 核心运行脚本

#### `runtime/legacy/main_loop.py`
**状态**: ⚠️ 已弃用 (Deprecated)

**原功能**: 自动交易循环，每5分钟唤醒 Commander 进行交易决策

**为什么弃用**:
- 系统已转为手动命令触发模式
- 提供更好的用户控制和降低 API 成本
- 参见 `MIGRATION.md` 了解详情

**替代方案**:
- 在 Claude Code 中手动输入命令："请开始一次交易分析"
- 或使用 workflow skills: `run_full_trading_analysis()`

---

#### `runtime/watchdog.py`
**功能**: 独立看门狗进程，监控账户风险并触发熔断器

**使用方法**:
```bash
# 单独启动看门狗
python runtime/watchdog.py

# 后台运行
nohup python runtime/watchdog.py > logs/watchdog.log 2>&1 &
```

**说明**:
- 独立进程运行，完全独立于 Claude Code
- 每60秒检查一次账户净值
- 回撤超过 10% 自动触发熔断器（Panic Close）
- 使用独立的 IBKR 连接（client_id=999）
- **注**: 手动命令模式下不再监控心跳（进程由 Claude Code 管理）

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

**注**: `scripts/run_sync_once.py` 和 `scripts/sync_with_rest_api.py` 已被删除，功能已整合到 `runtime/data_sync_daemon.py` 和 workflow skills 中。

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

### 6.5 交易运行时脚本

以下脚本提供了完整的交易分析、健康检查和风险管理功能。

#### `runtime/trade_analyze.py`
**功能**: 完整的7步交易分析工作流

**使用方法**:
```bash
# 分析所有板块，置信度0.75，最多10个信号
python runtime/trade_analyze.py

# 只分析科技板块，置信度0.85
python runtime/trade_analyze.py --sector=tech --confidence=0.85

# 准备模式（只分析不执行）
python runtime/trade_analyze.py --prepare-only

# 强制同步数据
python runtime/trade_analyze.py --force-sync
```

**说明**:
- ✅ 完整7步工作流：健康检查 → 账户状态 → 持仓风险 → 蜂群分析 → 信号过滤 → 风险评估 → 执行决策
- ✅ 支持板块过滤：`tech`（科技）、`finance`（金融）、`healthcare`（医疗）、`energy`（能源）、`ALL`（全部）
- ✅ 可配置置信度阈值（0.0-1.0）
- ✅ 准备模式可用于回测和分析
- ✅ 自动检查市场状态和数据质量
- ✅ 完整的交互式提示和错误处理

**工作流步骤**:
1. 市场健康检查（数据质量、市场状态）
2. 账户状态获取（净值、可用资金）
3. 持仓风险分析（风险评分、集中度）
4. 蜂群智能分析（并发咨询多个实例）
5. 信号过滤（按置信度和板块）
6. 风险评估（Kelly仓位计算、投资组合约束）
7. 执行决策（准备模式或实际下单）

---

#### `runtime/trade_health.py`
**功能**: 快速市场健康检查工具

**使用方法**:
```bash
python runtime/trade_health.py
```

**说明**:
- ✅ 快速检查市场开盘状态
- ✅ 评估数据质量（GOOD / STALE / CRITICAL）
- ✅ 显示关键指数价格（SPY、QQQ）和数据年龄
- ✅ 提供明确的建议（数据同步、交易建议）
- ✅ 退出码：0=正常，1=市场关闭，2=数据质量CRITICAL

**典型输出**:
```
======================================================================
市场健康检查
======================================================================
检查时间: 2025-11-22 10:30:00

市场状态: REGULAR
市场开盘: ✅ YES
数据质量: GOOD

SPY: $457.23 (数据年龄: 0h 5m)
QQQ: $389.45 (数据年龄: 0h 5m)

建议:
  🟢 数据质量 GOOD - 可以正常交易
======================================================================
```

---

#### `runtime/trade_risk.py`
**功能**: 持仓风险分析工具

**使用方法**:
```bash
# 使用默认阈值70
python runtime/trade_risk.py

# 自定义风险阈值
python runtime/trade_risk.py --threshold=60
```

**说明**:
- ✅ 分析当前持仓的风险水平
- ✅ 计算风险评分（0-100）
- ✅ 识别需要关注的高风险持仓
- ✅ 提供具体的行动建议
- ✅ 退出码：0=风险可控，1=风险超过阈值

**风险等级**:
- 🟢 低风险（评分 0-40）：可正常交易
- 🟡 中等风险（评分 41-70）：需要监控
- 🔴 高风险（评分 71-100）：建议减仓或对冲

**注**: 此脚本需要通过 Claude Code 环境运行以访问 IBKR MCP 持仓数据。直接运行将使用模拟数据。

---

### 6.6 脚本选择指南

| 使用场景 | 推荐方法 |
|---------|---------|
| 完整交易分析 | `python runtime/trade_analyze.py` 或 `/trade:analyze` |
| 快速市场检查 | `python runtime/trade_health.py` 或 `/trade:health` |
| 持仓风险分析 | `python runtime/trade_risk.py` 或 `/trade:risk` |
| 手动数据同步 | `python runtime/data_sync_daemon.py --once` 或 `/trade:sync` |
| 启动安全监控 | `python runtime/watchdog.py` (后台运行) |
| 定期数据同步 | `python runtime/data_sync_daemon.py --interval 10` |
| 验证系统配置 | `python verify_setup.py` |
| 测试 ThetaData 连接 | `python scripts/test_theta_fix.py` |
| 测试模板本地化 | `python test_template_localization.py` |
| 初始化监控列表 | `python -c "from data_lake import seed_initial_watchlist; seed_initial_watchlist()"` |

**Slash Commands**: 在 Claude Code 中可使用 `/trade:*` 系列命令作为快捷方式调用上述脚本。

---

## 7\. 未来功能规划 (Roadmap)

以下功能目前尚未实现，但已纳入开发计划：

### 7.1 梦境进化 (Dream Mode Evolution)

**规划位置**: `dream_lab/optimizer.py` (未来实现)

**目标**: 系统利用非交易时间进行自我迭代，采用**参数突变**而非代码重写的方式，确保稳定性。

**功能设计**:
  * **评估**: 扫描 `trades.db`，计算每个 Instance（配置文件）的 Sharpe Ratio
  * **变异**: 对表现不佳的 Instance 对应的 JSON 文件进行修改（例如：将 `iv_threshold` 从 80 调整为 85）
  * **验证**: 使用历史快照数据回测新配置，若更优则覆盖原 JSON

**状态**: 📋 已规划，未实现

---

### 7.2 新闻情绪分析 (News Sentiment Analysis)

**规划位置**: `mcp-servers/news-sentiment/` (部分实现)

**目标**: 通过新闻 API 获取实时新闻，分析市场情绪，辅助交易决策。

**状态**: 🚧 开发中

---

### 7.3 回测基础设施 (Backtesting Infrastructure)

**规划位置**: `dream_lab/backtester.py` (未来实现)

**目标**: 快速回测器，用于验证策略有效性和优化参数。

**状态**: 📋 已规划，未实现

---

### 7.4 遗传算法优化器 (Genetic Algorithm Optimizer)

**目标**: 自动化参数优化，通过遗传算法寻找最优策略参数组合。

**状态**: 📋 已规划，未实现

---

**重要提示**: README 中描述的所有功能均为**当前已实现**的功能。未来功能已移至此 Roadmap 部分，避免混淆。