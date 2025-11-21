# slash-command-integration Specification

## Purpose
提供用户友好的 Slash Command 系统，将复杂的 Python 技能调用简化为单行命令，同时保持完整的 Template + Parameters 架构优势。

## Requirements
### Requirement: Slash Command Discovery System
**Priority:** MUST
**Category:** Core Infrastructure

系统 MUST 提供自动发现和加载 Slash Command 的机制。

#### Scenario: Commands automatically discovered by Claude Code

**Given** 命令文件存储在 `.claude/commands/trading/` 目录下
**When** Claude Code 启动或刷新命令列表
**Then** 系统:
- 自动扫描目录下所有 `.md` 文件
- 解析命令元数据（名称、描述、参数）
- 使命令可用于用户调用

**Verification:**
- 所有 `.md` 文件被识别为命令
- 命令按文件名字母顺序排列
- 无效的命令文件被跳过并记录警告

#### Scenario: Command metadata parsing

**Given** 命令文件包含标准化的 YAML 前置元数据
**When** 系统解析命令文件
**Then** 系统:
- 提取命令名称、描述、用法示例
- 解析参数定义和类型信息
- 生成帮助文本和错误提示

**Verification:**
- 元数据格式符合 Claude Code 规范
- 参数类型正确识别（string、number、boolean）
- 缺失元数据的命令仍可加载但功能受限

### Requirement: Core Trading Commands
**Priority:** MUST
**Category:** User Interface

系统 MUST 提供完整的交易操作命令集。

#### Scenario: Execute complete trading analysis

**Given** 用户想要执行完整的交易分析流程
**When** 用户调用 `/trade-analysis --sectors TECH,FINANCE --min-confidence 0.80`
**Then** 系统:
- 解析参数（sectors、confidence、max_orders等）
- 调用 `run_full_trading_analysis()` 技能
- 格式化输出结果供用户查看
- 记录命令执行历史

**Verification:**
- 命令响应时间 < 2秒
- 参数正确类型转换和验证
- 错误信息清晰可操作
- 输出格式结构化且易读

#### Scenario: Quick market health check

**Given** 用户需要快速评估市场状态
**When** 用户调用 `/market-health --detailed`
**Then** 系统:
- 检查市场开盘状态
- 评估数据质量和新鲜度
- 返回关键指数和状态信息
- 提供交易建议

**Verification:**
- 市场状态分类准确（OPEN/CLOSED/AFTER_HOURS）
- 数据质量指标实时更新
- 建议基于当前市场环境

#### Scenario: Position risk analysis

**Given** 用户需要评估当前持仓风险
**When** 用户调用 `/risk-check --symbol AAPL`
**Then** 系统:
- 获取指定标的的持仓信息
- 计算风险指标（希腊字母、集中度等）
- 提供具体操作建议
- 生成风险报告

**Verification:**
- 风险评分算法一致性
- 建议基于风险管理原则
- 支持多标的批量分析

### Requirement: Strategy Management Commands
**Priority:** MUST
**Category:** Strategy Interface

系统 MUST 提供策略执行和管理命令。

#### Scenario: Execute specific strategy instance

**Given** 用户想要运行特定策略配置
**When** 用户调用 `/strategy-run tech_aggressive --verbose --dry-run`
**Then** 系统:
- 加载 `tech_aggressive` 实例配置
- 渲染对应的策略模板
- 执行分析并生成信号
- 显示详细执行过程（verbose模式）
- 仅生成信号不执行（dry-run模式）

**Verification:**
- 策略配置文件正确加载
- 模板渲染无错误
- 执行时间监控和记录
- 支持多种执行模式组合

#### Scenario: List and analyze available strategies

**Given** 用户需要查看所有可用策略
**When** 用户调用 `/strategy-list --performance --sector TECH`
**Then** 系统:
- 扫描 `active_instances/` 目录
- 提取策略元数据和性能数据
- 按指定条件筛选和排序
- 格式化显示策略列表

**Verification:**
- 支持多种筛选条件（sector、status、performance）
- 性能数据计算准确
- 列表格式便于快速浏览

### Requirement: Natural Language Strategy Creation
**Priority:** MUST
**Category:** Advanced Features

系统 MUST 支持中文自然语言策略创建。

#### Scenario: Create strategy from Chinese description

**Given** 用户用中文描述策略："使用缠论原理分析科技股，结合MACD确认买卖点"
**When** 用户调用 `/create-strategy "使用缠论原理分析科技股，结合MACD确认买卖点" --name chanlun_tech`
**Then** 系统:
- 提取交易概念（缠论、MACD、科技股）
- 选择最合适的策略模板
- 生成建议的参数配置
- 创建策略实例文件
- 验证生成的配置有效性

**Verification:**
- 概念提取准确率 > 90%
- 模板选择匹配用户意图
- 参数建议合理且可执行
- 生成的文件语法正确

#### Scenario: Strategy template auto-generation

**Given** 系统识别用户描述的策略类型
**When** 无法找到完美匹配的现有模板
**Then** 系统:
- 基于概念组合生成基础模板结构
- 包含常用的技术分析元素
- 提供模板自定义指导
- 保存为新的模板文件

**Verification:**
- 生成的模板结构完整
- 包含必要的导入和函数调用
- 支持后续参数化配置

### Requirement: Intelligent Parameter Processing
**Priority:** MUST
**Category:** User Experience

系统 MUST 提供智能参数解析和验证。

#### Scenario: Automatic parameter type conversion

**Given** 用户输入混合类型的参数
**When** 调用 `/trade-analysis --min-confidence 0.85 --max-orders 3 --skip-sync`
**Then** 系统:
- 自动将字符串转换为正确类型
- 验证参数范围和格式
- 提供详细的错误信息

**Verification:**
- 数字参数正确转换（int/float）
- 布尔参数支持多种格式（true/1/yes）
- 枚举参数验证白名单值

#### Scenario: Comprehensive error handling

**Given** 用户输入无效参数或参数组合
**When** 命令执行过程中检测到错误
**Then** 系统:
- 提供具体的错误位置和原因
- 建议正确的参数格式
- 显示命令使用示例
- 不崩溃系统，优雅降级

**Verification:**
- 错误信息包含足够上下文
- 建议基于实际情况有效
- 错误日志记录完整

### Requirement: Performance Monitoring
**Priority:** SHOULD
**Category:** Observability

系统 SHOULD 提供命令执行监控和性能分析。

#### Scenario: Execution time tracking

**Given** 用户执行任意 Slash Command
**When** 命令开始执行
**Then** 系统:
- 记录开始和结束时间戳
- 计算总执行时间
- 监控各阶段耗时
- 生成性能报告

**Verification:**
- 时间记录精确到毫秒
- 性能数据持久化存储
- 支持历史性能查询

#### Scenario: Command usage analytics

**Given** 系统运行一段时间
**When** 管理员需要了解使用情况
**Then** 系统:
- 统计各命令使用频率
- 分析用户行为模式
- 识别性能瓶颈
- 生成使用报告

**Verification:**
- 使用统计准确性 > 95%
- 报告格式易于分析
- 支持多维度数据查询

### Requirement: Backward Compatibility
**Priority:** MUST
**Category:** Migration

系统 MUST 保持与现有 Python 技能的完全兼容性。

#### Scenario: Existing Python imports continue working

**Given** 现有代码使用 Python 导入方式调用技能
**When** 运行现有代码
**Then** 所有现有功能:
- 无任何修改继续正常工作
- 性能无显著下降
- API 接口保持不变

**Verification:**
- 现有测试套件全部通过
- 性能基准测试达标
- API 兼容性测试通过

#### Scenario: Hybrid usage patterns supported

**Given** 用户同时使用 Slash Commands 和 Python 调用
**When** 混合使用两种方式
**Then** 系统:
- 共享相同的基础技能函数
- 保持状态一致性
- 避免重复执行或冲突

**Verification:**
- 状态同步正确
- 资源共享有效
- 无竞态条件

### Requirement: Comprehensive Help System
**Priority:** SHOULD
**Category:** Documentation

系统 SHOULD 提供完整的帮助和文档系统。

#### Scenario: Built-in command help

**Given** 用户需要了解命令使用方法
**When** 用户调用 `/trade-analysis --help`
**Then** 系统:
- 显示命令用途和描述
- 列出所有可用参数
- 提供使用示例
- 说明注意事项

**Verification:**
- 帮助信息准确完整
- 示例可实际执行
- 格式清晰易读

#### Scenario: General trading commands help

**Given** 用户需要了解所有可用命令
**When** 用户调用 `/trading-help`
**Then** 系统:
- 列出所有交易相关命令
- 提供快速使用指南
- 推荐最佳工作流程
- 包含故障排除指导

**Verification:**
- 命令列表完整且最新
- 工作流经过验证
- 故障排除覆盖常见问题