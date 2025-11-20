# 产品规格书: Agentic AlphaHive Runtime

**日期**: 2025年11月19日
**架构类型**: 基于 Claude Code 的递归式自治交易系统 (Recursive Autonomous Trading System)
**核心协议**: Model Context Protocol (MCP)

-----

## 1\. 系统概述 (System Overview)

**Agentic AlphaHive** 是一个无头（Headless）、非交互式的量化交易运行时环境。它不依赖传统的 Web 后端架构，而是以 **Claude Code** 为操作系统内核，通过 **MCP 协议** 连接外部金融设施。

系统的核心是一个“递归智能体”结构：主 Agent（指挥官）通过调用 Python Skill（技能）来并发调度底层的 **Alpha Swarm（分析蜂群）**。系统具备参数与逻辑分离的架构，支持通过修改配置文件的“梦境进化”，并配备独立于 AI 之外的“看门狗”进程以确保绝对安全。

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
└── 🚀 runtime/                # [运行环境]
    ├── main_loop.py           # 主唤醒循环 (Cron / Loop)
    └── watchdog.py            # [独立进程] 死手风控系统
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