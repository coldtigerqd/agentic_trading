# 项目上下文

## 目的

**Agentic AlphaHive Runtime** 是一个无头、非交互式的量化交易系统，使用 **Claude Code** 作为核心操作系统，通过 **模型上下文协议（MCP）** 集成外部金融基础设施，并配备 **Slash Command 系统** 提供一键式交易操作。

**核心目标：**
- 具有递归代理架构（指挥官 + Alpha蜂群）的自主期权交易
- 为安全的"梦境模式"进化实现参数-逻辑分离
- 独立于AI决策的硬编码安全层
- 快照驱动的决策记录以实现完全可审计性
- 先模拟交易，通过明确安全门槛后再实盘交易
- **[v3.0新增]** 通过 Slash Command 系统实现用户友好的命令行界面
- **[v3.0新增]** 支持中文自然语言策略创建和一键执行
- **[v3.0新增]** 完全保持 Template + Parameters 架构的灵活性优势
- **[v3.1新增]** 稳定脚本架构，避免bash执行大段代码的不稳定性
- **[v3.1新增]** 完整的错误处理和参数验证机制
- **[v3.1新增]** 统一的表格和JSON输出格式支持

## 技术栈

### 核心运行时
- **Claude Code**: 主要代理编排和决策引擎
- **Python 3**: MCP服务器实现、安全层、交易工具
- **MCP协议 (2024-11-05)**: Claude与外部服务之间的通信
- **[v3.0新增] Slash Commands**: 一键式命令行界面，简化复杂操作
- **[v3.0新增] 自然语言处理**: 中文策略概念提取和模板生成
- **[v3.1新增] 稳定Python脚本**: 独立脚本替代bash执行，确保系统稳定性
- **[v3.1新增] 参数解析器**: argparse统一参数处理和验证
- **[v3.1新增] 错误处理框架**: 完整的异常捕获和用户友好错误信息

### 金融基础设施
- **Interactive Brokers (IBKR)**: 订单执行和账户管理
- **ThetaData API**: 市场数据、期权链、历史数据
- **ib_insync**: IBKR TWS/Gateway集成的Python库

### 数据与处理
- **asyncio**: 并发蜂群代理操作
- **SQLite**: 交易记录和历史数据存储
- **Jinja2**: 蜂群代理提示的模板渲染
- **JSON**: 配置和参数存储
- **[v3.0新增] Strategy Factory**: 自然语言策略创建引擎
- **[v3.0新增] Execution Monitor**: 策略执行监控和性能分析
- **[v3.0新增] 概念字典**: 交易概念和策略模式的中文识别
- **[v3.1新增] 稳定脚本集**: 市场健康、交易分析、策略运行、风险检查的独立Python脚本
- **[v3.1新增] 中文本地化**: 完整的中文用户界面和错误信息
- **[v3.1新增] 输出格式化**: 统一的表格和JSON输出格式支持

### 测试与验证
- **pytest**: MCP服务器的测试框架
- **pytest-asyncio**: 异步测试支持
- **Mock IBKR连接**: 安全测试的模拟交易模式

## 项目约定

### 代码风格

**Python (MCP服务器和工具):**
- 遵循PEP 8并包含类型提示
- 描述性函数/变量命名：`validate_order()`, `max_trade_risk`
- 所有公共函数需要包含Args/Returns部分的文档字符串
- 使用数据类进行结构化配置（例如：`SafetyLimits`）

**文件命名:**
- 下划线命名：`swarm_core.py`, `execution_gate.py`
- 测试文件：`test_*.py`模式
- MCP服务器：专用目录中的`server.py`
- **[v3.0新增]** Slash Commands: `.claude/commands/trading/*.md`
- **[v3.1新增]** Stable Scripts: `scripts/*.py` (market_health.py, trade_analysis.py, strategy_runner.py, risk_check.py)

**配置文件:**
- 参数使用JSON：`active_instances/*.json`
- 模板使用Markdown：`templates/*.md`
- 密钥使用环境变量：`.env`文件
- **[v3.0新增]** 用户文档：`docs/slash-command-guide.md`

### 架构模式

**递归代理结构:**
- **指挥官** (Claude Code): 高级决策、策略选择
- **Alpha蜂群** (并发子代理): 通过`swarm_core.py`技能进行并行分析
- **关注点分离**: 逻辑（模板）vs 参数（JSON配置）
- **[v3.0新增] Slash Commands**: 用户友好的命令行界面，简化技能调用
- **[v3.0新增] 自然语言接口**: 中文策略描述到可执行模板的转换

**MCP服务器模式:**
- 每个集成是一个独立的MCP服务器（IBKR、ThetaData、Memory）
- 服务器通过stdio上的JSON-RPC暴露工具
- 安全验证在API调用之前发生，而非之后

**[v3.0新增] Slash Command 架构:**
- 命令发现：`.claude/commands/trading/` 目录自动扫描
- 参数解析：智能类型转换和验证
- 零破坏集成：完全基于现有 Python 技能，无业务逻辑重写
- 多语言支持：完全中文化的用户界面

**[v3.1新增] 稳定脚本架构:**
- 脚本执行：完全避免 `bash -c "大段代码"` 的不稳定性问题
- 错误隔离：单个脚本错误不影响其他命令的执行
- 参数标准化：统一使用argparse进行参数验证和帮助生成
- 输出格式：支持表格和JSON两种标准输出格式
- 中文本地化：完整的中文错误信息和用户界面

**安全层:**
- `safety.py`中的硬编码限制（未经人工批准不得修改）
- 具有独立IBKR连接的独立看门狗进程（`runtime/watchdog.py`）
- 熔断机制：日亏损限额、回撤触发器、连续亏损限制
- 订单执行前验证，而非执行后

**数据流:**
1. 市场数据 → 蜂群分析 → 信号聚合 → 指挥官决策
2. 所有蜂群输入保存到`data_lake/snapshots/`以确保可重现性
3. 订单在提交IBKR前通过安全层验证
4. 结果记录到`trades.db`用于后期分析

### 测试策略

**MCP服务器测试:**
- 单元测试：`tests/test_tools.py`, `tests/test_safety.py`
- 集成测试：`tests/test_integration.py`（需要IBKR连接）
- 连接测试：`tests/test_connection.py`
- 运行方式：`pytest mcp-servers/ibkr/tests/`

**安全验证:**
- 所有订单操作针对安全限制进行测试
- 模拟交易环境先于模拟交易
- 模拟交易验证先于实盘交易
- 使用模拟回撤测试熔断机制

**蜂群测试:**
- 模板渲染验证
- 并发代理执行压力测试
- 信号聚合和去重测试

### Git工作流程

**分支策略:**
- `main`: 仅稳定、经过测试的代码
- 新功能的功能分支
- 重大变更使用OpenSpec提案

**提交约定:**
- 安全变更：`[SAFETY] 描述` - 需要额外审查
- MCP变更：`[MCP] 描述`
- 代理逻辑：`[AGENT] 描述`
- 配置/参数：`[CONFIG] 描述` - 可通过梦境模式修改

**关键文件:**
- `safety.py`: 任何变更需要人工批准
- `watchdog.py`: 独立安全进程，AI不得修改
- `.env`: 永远不要提交到git

## Domain Context

**Options Trading:**
- Primary strategy: Volatility-based spreads (put spreads, call spreads)
- Metrics: IV Rank, IV Percentile, Delta, Theta, Vega exposure
- Risk management: Defined-risk strategies only (no naked options)

**Market Data:**
- Real-time quotes via ThetaData MCP
- Options chains with Greeks from ThetaData
- Position tracking via IBKR API
- News sentiment analysis (planned via news-sentiment MCP)

**Agent Decision Making:**
- Swarm produces signals with confidence scores
- Commander evaluates signals against portfolio state
- Kelly criterion for position sizing
- Final go/no-go based on macro conditions + risk limits

**Terminology:**
- **Instance**: A specific swarm configuration (template + parameters)
- **Template**: Logic/strategy in Jinja2 Markdown format
- **Swarm**: Concurrent execution of all active instances
- **Signal**: Output from swarm analysis (symbol, strategy, confidence)
- **Commander**: Primary Claude Code agent orchestrating everything
- **[v3.0新增] Slash Command**: 一键式命令，简化复杂的 Python 技能调用
- **[v3.0新增] Natural Language Strategy**: 中文描述的策略，可自动转换为可执行模板
- **[v3.0新增] Strategy Factory**: 自然语言策略创建引擎
- **[v3.0新增] Execution Monitor**: 策略执行监控和性能分析组件

## Important Constraints

### Safety Constraints (HARD LIMITS)
- **Max trade risk**: $500 per trade
- **Max trade capital**: $2,000 per trade
- **Daily loss limit**: $1,000 (triggers shutdown)
- **Max portfolio concentration**: 30% in any single symbol
- **Drawdown circuit breaker**: 10% account drawdown triggers full stop
- **Consecutive loss limit**: 5 losses triggers suspension

### Technical Constraints
- IBKR connection required for all trading operations
- Paper trading (port 4002) before live trading (port 4001)
- MCP protocol version 2024-11-05 compatibility
- Python 3.8+ required for asyncio features

### Operational Constraints
- Watchdog process must run independently of agent
- All trading decisions must be logged with full context snapshots
- No direct code generation for orders (use `execution_gate.py` primitives)
- Configuration changes (JSON) allowed; template logic changes require review

### Regulatory/Risk Constraints
- Options-approved IBKR account required
- Defined-risk strategies only (no naked positions)
- Pre-market and after-hours trading requires explicit approval
- All trades subject to safety layer validation (no bypasses)

## External Dependencies

### Critical Services
- **Interactive Brokers TWS/Gateway**:
  - Paper Trading: localhost:4002
  - Live Trading: localhost:4001
  - Required: Running TWS/Gateway before agent starts

- **ThetaData API**:
  - Real-time market data
  - Options chains and Greeks
  - Historical data for backtesting
  - API key in `.env` file

### MCP Servers (Internal)
- **ibkr** (`mcp-servers/ibkr/`): Trading execution, account queries, position management
- **news-sentiment** (`mcp-servers/news-sentiment/`): News analysis for sentiment filtering
- **memory** (planned): Long-term agent memory and state persistence

### Python Libraries
- `ib_insync`: IBKR API wrapper (install: `pip install ib_insync`)
- `asyncio`: Built-in async runtime
- `pytest`, `pytest-asyncio`: Testing framework
- `jinja2`: Template rendering for swarm prompts
- **[v3.0新增] 自然语言处理库**: 用于中文策略概念提取和匹配
- **[v3.0新增] 执行监控库**: 策略性能追踪和分析

### File System Dependencies
- `~/trading_workspace/state/agent_memory.json`: Agent state persistence
- `~/trading_workspace/logs/`: Safety violations, circuit breaker events
- `data_lake/snapshots/`: Decision context archival
- `data_lake/trades.db`: Trade history database
- **[v3.0新增]** `.claude/commands/trading/`: Slash Command 命令定义文件
- **[v3.0新增]** `docs/slash-command-guide.md`: 用户使用指南和最佳实践
- **[v3.0新增]** `swarm_intelligence/strategy_factory.py`: 策略创建引擎
- **[v3.0新增]** `swarm_intelligence/execution_monitor.py`: 执行监控数据库
- **[v3.1新增]** `scripts/`: 稳定Python脚本目录，包含market_health.py、trade_analysis.py、strategy_runner.py、risk_check.py
- **[v3.1新增]** `scripts/README.md`: 稳定脚本使用说明文档
- **[v3.1新增]** `scripts/SLASH_COMMAND_INTEGRATION.md`: Slash Command集成完成报告
