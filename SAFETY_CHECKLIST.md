# Safety Checklist - Pre-Live Trading Validation

## 概述 (Overview)

在将 Agentic AlphaHive Runtime 系统转入实盘交易前，必须完成以下所有安全验证。此检查清单确保系统在真实资金环境中具备必要的安全保障。

**重要提示**: 跳过任何一项检查都可能导致资金损失。请认真对待每一项验证。

---

## Phase 1: 模拟交易验证 (Paper Trading Validation)

### 1.1 IBKR 模拟交易账户设置 ✅ / ❌

- [ ] IBKR 模拟交易账户已创建并激活
- [ ] IB Gateway 已安装并配置为模拟交易模式（端口 4002）
- [ ] API 连接已在 IB Gateway 设置中启用
- [ ] "Read-Only API" 设置为 FALSE
- [ ] 验证端口 4002 可访问：`netstat -an | grep 4002`

**验证命令**:
```bash
python3 -c "
from mcp_servers.ibkr import get_connection_manager, ConnectionMode
manager = get_connection_manager()
manager.connect_sync(mode=ConnectionMode.PAPER_GATEWAY, client_id=1)
print(f'Connected: {manager.is_connected}')
"
```

**预期输出**: `Connected: True`

---

### 1.2 模拟交易运行时长 ✅ / ❌

- [ ] 系统已在模拟交易环境运行至少 **30 天**
- [ ] 每日监控日志，无关键错误
- [ ] 熔断器（circuit breaker）未因误触发而中断
- [ ] 所有决策已记录并可审计（snapshots/ 和 trades.db）

**验证查询**:
```sql
-- 查询模拟交易统计
SELECT
    COUNT(*) as total_cycles,
    MIN(created_at) as first_cycle,
    MAX(created_at) as last_cycle,
    JULIANDAY(MAX(created_at)) - JULIANDAY(MIN(created_at)) as days_running
FROM trades;
```

**最低要求**: `days_running >= 30`

---

### 1.3 交易决策质量 ✅ / ❌

- [ ] 蜂群（swarm）在 30 秒内返回信号（性能测试）
- [ ] 至少 80% 的信号有 confidence >= 0.70
- [ ] 无异常高频交易（每日交易次数 < 20）
- [ ] 订单验证拒绝率在合理范围（10-30%）

**验证查询**:
```sql
-- 信号质量统计
SELECT
    COUNT(*) as total_signals,
    AVG(confidence) as avg_confidence,
    SUM(CASE WHEN status='VALIDATED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as validation_rate
FROM trades;
```

---

## Phase 2: 安全层验证 (Safety Layer Validation)

### 2.1 硬编码限制测试 ✅ / ❌

**测试场景 1: 超出最大风险限制**
- [ ] 尝试提交 max_risk = $600 的订单（超过 $500 限制）
- [ ] 验证订单被拒绝，错误消息清晰
- [ ] 安全违规已记录到 `safety_events` 表

**测试场景 2: 超出最大资金限制**
- [ ] 尝试提交 capital_required = $2500 的订单（超过 $2000 限制）
- [ ] 验证订单被拒绝
- [ ] 安全违规已记录

**测试场景 3: 超出集中度限制**
- [ ] 尝试在单一标的（如 NVDA）上分配超过 30% 的账户价值
- [ ] 验证订单被拒绝

**验证查询**:
```sql
-- 安全违规统计
SELECT
    violation_type,
    COUNT(*) as count,
    MAX(created_at) as last_occurrence
FROM safety_events
GROUP BY violation_type;
```

**预期结果**: 至少 3 个不同类型的安全违规记录

---

### 2.2 熔断器（Circuit Breaker）测试 ✅ / ❌

**测试场景: 模拟 10% 回撤**

- [ ] 手动修改账户初始值，模拟 10% 回撤
- [ ] 验证熔断器自动触发
- [ ] 验证所有后续交易周期被跳过
- [ ] 验证需要手动重置才能恢复

**触发测试**:
```python
# 在 watchdog.py 中临时降低阈值
CIRCUIT_BREAKER_THRESHOLD = 0.05  # 5% for testing

# 运行系统，观察熔断器触发
```

**验证**:
```bash
# 检查 agent_memory.json
cat ~/trading_workspace/state/agent_memory.json | jq '.safety_state'

# 预期输出:
# {
#   "circuit_breaker_triggered": true,
#   "circuit_breaker_timestamp": "2025-11-21T10:30:00"
# }
```

**重置测试**:
```bash
python -c "
from data_lake.db_helpers import reset_circuit_breaker
reset_circuit_breaker()
"
```

---

### 2.3 订单验证完整性 ✅ / ❌

- [ ] 所有订单必须通过 `place_order_with_guard()`
- [ ] 验证无代码路径绕过安全层
- [ ] 代码审查确认无 `ibkr_mcp.place_order()` 的直接调用

**代码审查**:
```bash
# 搜索绕过安全层的调用
grep -r "ibkr.*place_order" --include="*.py" | grep -v "place_order_with_guard"

# 预期输出: 仅在 execution_gate.py 内部有 IBKR 调用
```

---

## Phase 3: 看门狗（Watchdog）验证

### 3.1 心跳监控测试 ✅ / ❌

**测试场景: 模拟 AI 进程冻结**

- [ ] 启动 main_loop.py 和 watchdog.py
- [ ] 手动停止 main_loop.py（`kill -STOP <pid>`）
- [ ] 验证 watchdog 在 60 秒内检测到心跳停止
- [ ] 验证 watchdog 日志记录异常

**验证**:
```bash
# 查看 watchdog 日志
tail -f ~/trading_workspace/logs/watchdog.log

# 预期输出:
# [2025-11-21 10:30:00] WARNING - Heartbeat stale (120 seconds old)
# [2025-11-21 10:30:00] CRITICAL - AI process frozen, triggering emergency actions
```

---

### 3.2 独立 IBKR 连接测试 ✅ / ❌

- [ ] 验证 watchdog 使用 client_id=999（独立于 AI 的 client_id=1）
- [ ] 验证 watchdog 可在 AI 断开时仍连接 IBKR
- [ ] 验证 watchdog 可独立执行平仓操作

**验证**:
```bash
# 检查 IBKR 连接
netstat -an | grep 4002

# 应看到 2 个独立连接（AI + Watchdog）
```

---

### 3.3 紧急平仓测试 ✅ / ❌

**测试场景: Watchdog 强制平仓**

- [ ] 在模拟账户中持有至少 1 个持仓
- [ ] 手动触发 `panic_close_all_positions()`
- [ ] 验证所有持仓被平仓
- [ ] 验证市价单（market orders）被提交到 IBKR

**测试代码**:
```python
from runtime.watchdog import panic_close_all_positions
from ib_insync import IB

ib = IB()
ib.connect('localhost', 4002, clientId=999)
panic_close_all_positions(ib)
ib.disconnect()
```

---

## Phase 4: 数据完整性验证

### 4.1 数据库持久化 ✅ / ❌

- [ ] trades.db 存在并可读
- [ ] 所有交易已记录（trade_id 连续）
- [ ] 数据库未损坏（SQLite integrity check）

**验证**:
```bash
sqlite3 data_lake/trades.db "PRAGMA integrity_check;"
# 预期输出: ok

sqlite3 data_lake/trades.db "SELECT COUNT(*) FROM trades;"
# 应返回 > 0
```

---

### 4.2 快照可审计性 ✅ / ❌

- [ ] 每个交易决策有对应快照（snapshots/）
- [ ] 快照包含完整上下文（市场数据、蜂群输入、信号输出）
- [ ] 快照文件名格式正确（timestamp-based）

**验证**:
```bash
# 列出最近 10 个快照
ls -lt ~/trading_workspace/snapshots/*.json | head -10

# 验证快照结构
python -c "
import json
from pathlib import Path

snapshots = sorted(Path.home().glob('trading_workspace/snapshots/*.json'))
if snapshots:
    with open(snapshots[-1]) as f:
        data = json.load(f)
    assert 'instance_id' in data
    assert 'rendered_prompt' in data
    assert 'market_data' in data
    print('✓ Snapshot structure valid')
"
```

---

## Phase 5: 系统可靠性验证

### 5.1 长时间运行稳定性 ✅ / ❌

- [ ] 系统连续运行 7 天无崩溃
- [ ] 内存泄漏检查（内存使用稳定）
- [ ] 日志文件大小在可管理范围（< 1GB/月）

**监控命令**:
```bash
# 检查进程内存使用
ps aux | grep "python.*main_loop"

# 检查日志文件大小
du -sh ~/trading_workspace/logs/
```

---

### 5.2 错误恢复能力 ✅ / ❌

**测试场景 1: IBKR 连接丢失**
- [ ] 关闭 IB Gateway
- [ ] 验证系统优雅处理连接错误
- [ ] 重启 IB Gateway 后系统自动恢复

**测试场景 2: LLM API 故障**
- [ ] 模拟 LLM API 超时（mock timeout）
- [ ] 验证蜂群执行跳过失败实例
- [ ] 验证至少部分信号仍能返回

**测试场景 3: 磁盘空间不足**
- [ ] 模拟磁盘满（临时限制快照目录大小）
- [ ] 验证系统不崩溃
- [ ] 验证错误日志清晰

---

## Phase 6: 人工审查 (Manual Review)

### 6.1 策略逻辑审查 ✅ / ❌

- [ ] 所有蜂群模板（templates/）已由人工审查
- [ ] 策略逻辑符合风险偏好
- [ ] 参数配置（active_instances/）合理
- [ ] 无过度激进的参数（如 min_iv_rank < 50）

---

### 6.2 Commander 提示词审查 ✅ / ❌

- [ ] `prompts/commander_system.md` 已审查
- [ ] 安全约束清晰表述
- [ ] 工作流程（SENSE-THINK-DECIDE-ACT）无漏洞
- [ ] 技能（skills）使用说明准确

---

### 6.3 代码审查 ✅ / ❌

- [ ] 所有 skills/ 模块已审查
- [ ] 无硬编码 API 密钥
- [ ] 错误处理完善
- [ ] 无已知安全漏洞

---

## Phase 7: 实盘前最终检查

### 7.1 资金分配决策 ✅ / ❌

- [ ] 决定实盘交易初始资金量（建议 $5,000 - $10,000）
- [ ] 理解并接受最大可能损失（熔断器：10% 回撤）
- [ ] 紧急联系人和应急程序已记录

---

### 7.2 监控和告警 ✅ / ❌

- [ ] 日志监控计划已制定（每日检查）
- [ ] 异常告警机制已设置（可选：邮件/短信）
- [ ] 手动干预程序已记录并测试

---

### 7.3 回滚计划 ✅ / ❌

- [ ] 紧急停止开关已测试（`pkill -f main_loop`）
- [ ] 手动平仓流程已记录
- [ ] 回退到模拟交易的步骤已文档化

---

## 最终批准

**在签署此检查清单前，请确保**:

- [ ] 我已完成所有 Phase 1-7 的检查项
- [ ] 我理解系统的风险和限制
- [ ] 我已测试所有应急程序
- [ ] 我准备好监控和维护实盘交易系统
- [ ] 我接受可能的资金损失风险

**签署人**: ________________________
**日期**: ________________________
**初始资金**: $________________________

---

## 应急联系方式

**系统管理员**: ________________________
**交易监督**: ________________________
**IBKR 客服**: 1-877-442-2757

---

## 附录: 快速参考命令

### 紧急停止系统
```bash
pkill -f "python runtime/main_loop.py"
pkill -f "runtime.watchdog"
```

### 重置熔断器
```bash
python -c "from data_lake.db_helpers import reset_circuit_breaker; reset_circuit_breaker()"
```

### 查看最近日志
```bash
tail -n 100 ~/trading_workspace/logs/main.log
tail -n 100 ~/trading_workspace/logs/watchdog.log
```

### 查看当前持仓
```python
from mcp_servers.ibkr import get_positions
positions = get_positions()
for pos in positions:
    print(f"{pos['symbol']}: {pos['position']} @ ${pos['avgCost']}")
```

---

**记住**: 模拟交易应该是无聊的。如果它令人兴奋或有压力，系统还没准备好进行实盘交易。
