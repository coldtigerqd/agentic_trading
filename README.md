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