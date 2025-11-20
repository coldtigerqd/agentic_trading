# 中文本地化提案总结 | Chinese Localization Proposal Summary

**日期 | Date**: 2025-11-21
**分支 | Branch**: `feature/chinese-localization`
**OpenSpec 变更 ID | Change ID**: `localize-to-chinese`
**状态 | Status**: ✅ 已验证 | Validated

---

## 📋 执行概要 | Executive Summary

本提案旨在**全面将 Agentic AlphaHive Runtime 系统本地化为中文**，包括所有核心组件：

- ✅ **系统提示词**（Commander System Prompt）
- ✅ **蜂群策略模板**（5个策略完整翻译）
- ✅ **Python 技能输出**（日志、状态消息、错误提示）
- ✅ **验证与错误消息**（带英文错误代码）
- ✅ **核心文档**（README 双语、QUICKSTART 全中文）

---

## 🎯 核心目标 | Core Objectives

### 当前痛点 | Current Pain Points
- 中文使用者需要不断在脑海中翻译英文系统输出
- 调试和监控需要英文理解能力
- 策略模板对中文分析师不够友好
- 混合语言文档增加认知负担
- 日志分析和事故响应速度较慢

### 期望成果 | Desired Outcomes
- 指挥官使用中文提示词进行决策推理
- 蜂群策略以中文生成信号和解释
- 所有运行时输出使用中文（保留技术术语英文）
- 错误消息中文为主，英文代码辅助（便于grep）
- 文档对纯中文使用者友好

---

## 📦 交付范围 | Deliverables

### ✅ 包含在内 | In Scope

| 组件 | 文件/模块 | 工作量 |
|------|----------|--------|
| **系统提示词** | `prompts/commander_system.md` | 4 小时 |
| **蜂群模板** | `swarm_intelligence/templates/*.md` (5个) | 10 小时 |
| **技能输出** | `skills/*.py` (14个模块) | 20 小时 |
| **验证消息** | `execution_gate.py`, `safety.py`, `data_quality.py` | 8 小时 |
| **文档** | `README.md`(双语), `QUICKSTART.md`(全中文) | 7 小时 |
| **测试验证** | 集成测试、回归测试、原生人士审核 | 11 小时 |

**总计**: ~60 小时（3周，1人全职）

### ❌ 不包含 | Out of Scope
- MCP 服务器内部代码（底层协议处理）
- 第三方库代码
- 测试文件内容（保持英文以维护代码一致性）
- Git 提交消息（保持英文以支持国际协作）

---

## 🏗️ 实施计划 | Implementation Plan

### 第一阶段：提示词与模板（第1周）
- [x] 创建翻译术语表（50+术语）
- [ ] 翻译 Commander 系统提示词
- [ ] 翻译 5 个蜂群策略模板
- [ ] 集成测试：完整蜂群咨询流程

### 第二阶段：技能输出（第2周）
- [ ] 本地化 14 个技能模块（print/log/docstring）
- [ ] 重点：`market_data.py`, `swarm_core.py`, `execution_gate.py`
- [ ] 集成测试：完整交易周期（SENSE-THINK-DECIDE-ACT）

### 第三阶段：验证与错误（第3周）
- [ ] 本地化安全验证器拒绝消息
- [ ] 创建错误代码注册表（ERROR_CODES）
- [ ] 统一错误消息格式：`{中文消息} ({ERROR_CODE})`
- [ ] 集成测试：15+错误场景

### 第四阶段：文档（第4周）
- [ ] 翻译 README.md（双语，中文优先）
- [ ] 翻译 QUICKSTART.md（全中文）
- [ ] 添加关键模块的中文注释
- [ ] 集成测试：文档完整性验证

### 第五阶段：最终验证（第5周）
- [ ] UTF-8 编码审计
- [ ] 完整系统回归测试
- [ ] 原生中文人士审核
- [ ] OpenSpec 验证与归档

---

## 📐 设计原则 | Design Principles

### 1️⃣ 术语分类策略 | Terminology Classification

| 类别 | 处理方式 | 示例 |
|------|----------|------|
| **领域术语** | 保持英文 | PUT_SPREAD, OHLC, MACD, RSI |
| **系统概念** | 翻译为中文 | Commander → 指挥官, Swarm → 蜂群 |
| **用户消息** | 完全中文化 | 错误消息、状态更新、日志 |

### 2️⃣ 标准译名 | Standard Translations

```yaml
Commander: 指挥官
Alpha Swarm: Alpha蜂群
Signal: 信号
Strategy: 策略
Risk: 风险
Safety Layer: 安全层
Circuit Breaker: 熔断机制
Fresh Data: 新鲜数据
Stale Data: 过期数据
```

### 3️⃣ 错误代码策略 | Error Code Strategy

所有错误消息格式：**中文描述 + 英文代码（括号内）**

```python
# 正确示例 | Correct Example
"交易风险 $600 超过限额 $500 (RISK_EXCEEDED)"

# 错误示例 | Wrong Example
"Trade risk $600 exceeds limit"  # ❌ 全英文
"交易风险超限"  # ❌ 缺少错误代码
```

**优势**：
- ✅ 中文使用者快速理解
- ✅ 支持 `grep "RISK_EXCEEDED"` 搜索日志
- ✅ 国际团队仍可通过代码理解错误类型

### 4️⃣ 代码结构保持不变 | Code Structure Preservation

```python
# ✅ 正确：变量/函数名保持英文，消息中文化
def sync_watchlist_incremental(skip_if_market_closed: bool = True):
    """增量同步监控列表中的市场数据"""
    print(f"正在同步 {len(symbols)} 个标的...")
    return {"success": True, "message": "同步完成"}

# ❌ 错误：不要翻译变量/函数名
def 增量同步监控列表(如果市场关闭则跳过: bool = True):  # ❌
    同步信息 = 获取同步状态()  # ❌
```

---

## ✅ 验证标准 | Success Criteria

| 标准 | 验证方法 |
|------|----------|
| Commander 中文推理 | 运行完整交易周期，检查输出语言 |
| 蜂群信号中文解释 | 调用 `consult_swarm()`，验证 `reasoning` 字段 |
| 所有日志中文化 | 检查 `logs/*.log`，确保无英文用户消息 |
| 安全验证器中文拒绝 | 触发 8 种拒绝场景，验证消息格式 |
| 文档可用性 | 中文母语者使用文档完成系统设置 |
| 无功能回退 | 回归测试通过，性能无下降 |

---

## 📊 任务分解 | Task Breakdown

**总计**: 31 个任务 | 5 个阶段 | ~60 小时

### 并行机会 | Parallel Opportunities
- **5 个模板翻译**可并行执行（任务 1.3-1.7）
- **10 个技能模块**可分配给 2 人（任务 2.1-2.8）
- **文档翻译**可并行进行（任务 4.1-4.3）

### 关键路径 | Critical Path
1. 任务 1.1（术语表）→ 阻塞所有翻译任务
2. 任务 1.2（Commander 提示词）→ 阻塞集成测试
3. 任务 5.2（回归测试）→ 阻塞最终签收

详细任务清单见：`openspec/changes/localize-to-chinese/tasks.md`

---

## 🛡️ 风险缓解 | Risk Mitigation

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 金融术语翻译准确性 | 中 | 创建术语表，领域专家审核 |
| 提示词对语言敏感 | 高 | 广泛测试 Commander 行为 |
| 字符编码问题 | 低 | 全局 UTF-8，多终端测试 |
| 混合语言调试困惑 | 低 | 保持英文变量名和错误代码 |

---

## 📚 相关文件 | Related Files

| 文件 | 描述 |
|------|------|
| `openspec/changes/localize-to-chinese/proposal.md` | 完整提案 |
| `openspec/changes/localize-to-chinese/design.md` | 架构设计 |
| `openspec/changes/localize-to-chinese/tasks.md` | 31 个任务清单 |
| `openspec/changes/localize-to-chinese/specs/` | 4 个功能规范 |

---

## 🚀 下一步行动 | Next Steps

1. **审核提案**：团队评审 OpenSpec 提案
2. **分配任务**：从任务 1.1（术语表）开始
3. **并行开发**：模板翻译和技能模块可并行
4. **持续验证**：每完成一个阶段进行集成测试
5. **原生审核**：第 4 周邀请中文母语者审核
6. **归档上线**：通过验证后执行 `openspec archive localize-to-chinese`

---

## 🎯 预期影响 | Expected Impact

### 用户体验提升 | UX Improvements
- ⏱️ **调试时间减少 40%**（中文使用者）
- 📈 **策略开发效率提升 30%**（中文分析师）
- 🛡️ **事故响应速度提升 50%**（中文运维团队）

### 技术债务 | Technical Debt
- ➕ **增加**: 维护双语文档
- ➖ **减少**: 移除临时混合语言注释
- ⚖️ **平衡**: 通过术语表和维护指南保持一致性

### 国际化基础 | i18n Foundation
本次硬编码中文实现为未来 i18n 框架奠定基础：
- ✅ 术语表可转换为翻译文件（`zh-CN.json`）
- ✅ 错误代码注册表支持多语言扩展
- ✅ 代码结构支持配置化语言切换

---

## ✅ OpenSpec 验证状态 | Validation Status

```bash
$ openspec validate localize-to-chinese --strict
✅ Change 'localize-to-chinese' is valid
```

**所有规范已通过验证**：
- ✅ 提示词本地化规范（3 个需求）
- ✅ 技能输出本地化规范（4 个需求）
- ✅ 验证消息本地化规范（4 个需求）
- ✅ 文档本地化规范（4 个需求）

---

## 📞 联系方式 | Contact

如有疑问或需要澄清，请：
1. 查看 OpenSpec 提案：`openspec show localize-to-chinese`
2. 审核设计文档：`openspec/changes/localize-to-chinese/design.md`
3. 查看任务清单：`openspec/changes/localize-to-chinese/tasks.md`

---

**此提案由 OpenSpec 生成并验证 | Generated and validated by OpenSpec**
**分支 | Branch**: `feature/chinese-localization`
**提交 | Commit**: `7354cad`
