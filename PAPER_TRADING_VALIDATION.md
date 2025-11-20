# 模拟交易验证指南

## 概述

本指南指导您在考虑实盘交易前，使用 IBKR 模拟交易验证 Agentic AlphaHive Runtime 系统。

## 前置要求

### 1. IBKR 模拟交易账户

- 注册地址: https://www.interactivebrokers.com/en/trading/tws.php
- 下载并安装 **IB Gateway**（比 TWS 更轻量）
- **重要**: 使用模拟交易模式（端口 4002）

### 2. 所需 API 密钥

在项目根目录创建 `.env` 文件：

```bash
# 从示例文件复制
cp .env.example .env

# 编辑并填入您的密钥
nano .env
```

必需的密钥：
```
OPENROUTER_API_KEY=your_key_here    # 从 https://openrouter.ai/keys 获取
IBKR_PORT=4002                       # 模拟交易端口
IBKR_CLIENT_ID=1                     # 主 AI 客户端
THETADATA_API_KEY=your_key_here      # 可选，用于市场数据
```

### 3. 启动 IBKR Gateway

```bash
# 在 Linux/Mac 上
~/IBController/IBControllerGatewayStart.sh &

# 在 Windows 上
# 从开始菜单运行 IB Gateway

# 验证其运行在 4002 端口
netstat -an | grep 4002
```

**重要事项**:
- 在 IB Gateway 设置中启用 API 连接
- 将 "Read-Only API" 设置为 FALSE（模拟交易必需）
- 端口 4002 = 模拟交易网关

## 分步验证

### 步骤 1: 重置熔断器

熔断器可能在开发测试期间被触发：

```bash
# 检查状态
cat ~/trading_workspace/state/agent_memory.json

# 熔断器应显示:
{
  "safety_state": {
    "circuit_breaker_triggered": false,
    "circuit_breaker_timestamp": null
  }
}
```

✅ **已完成** - 熔断器已重置！

### 步骤 2: 验证 IBKR 连接

测试系统能否连接到 IBKR 模拟交易：

```bash
# 测试 IBKR MCP 服务器健康状态
python3 -c "
from mcp_servers.ibkr import get_connection_manager, ConnectionMode
manager = get_connection_manager()
manager.connect_sync(mode=ConnectionMode.PAPER_GATEWAY, client_id=1)
print(f'Connected: {manager.is_connected}')
"
```

预期输出：
```
✅ Connected to IBKR Paper Trading (Gateway)
Connected: True
```

或直接使用 MCP 工具：

```python
# 在 Claude Code 中
mcp__ibkr__health_check()
# 应返回: {"is_connected": true, "mode": "Paper Trading (Gateway)", ...}

mcp__ibkr__get_account()
# 应返回来自 IBKR 的真实账户数据，而非模拟的 $10,000
```

### 步骤 3: 安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 4: 初始化数据库

```bash
# 创建交易数据库
python -c "from data_lake import db_helpers; print('Database initialized')"

# 验证数据库存在
ls -lh data_lake/trades.db
```

### 步骤 5: 运行测试周期

启动带 IBKR 连接的运行时：

```bash
# 运行主循环（按 Ctrl+C 停止）
python runtime/main_loop.py
```

**关注内容：**

✅ **正常标志：**
```
INFO - === Agentic AlphaHive Runtime Starting ===
INFO - Watchdog process started (PID: XXXXX)
INFO - === Starting Trading Cycle ===
INFO - Current account value: $1,027,195.09    # <-- 来自 IBKR 的真实值！
INFO - Watchdog monitoring started
```

❌ **异常标志：**
```
WARNING - Circuit breaker active - skipping cycle    # 熔断器已触发
ERROR - Failed to connect to IBKR                    # IBKR Gateway 未运行
WARNING - Using fallback account value               # 无法连接到 IBKR
INFO - Initial account value: $10000.00              # 模拟数据（非真实 IBKR）
```

### 步骤 6: 运行 Commander 代理（通过 Claude Code）

主循环提供运行时，但 **Claude Code 充当指挥官** 做出交易决策。

在 Claude Code 中，启动一个交易周期：

```python
# === SENSE 阶段 ===
# 获取账户和持仓
account = mcp__ibkr__get_account()
positions = mcp__ibkr__get_positions()

print(f"账户: ${account['net_liquidation']:,.2f}")
print(f"持仓: {len(positions)}")

# 获取市场数据
symbols = ["AAPL", "NVDA", "TSLA"]
quotes = mcp__ThetaData__stock_snapshot_quote(symbol=symbols)

# === THINK 阶段 ===
from skills import consult_swarm

market_data = {
    "timestamp": "2025-11-20T01:00:00",
    "symbols": symbols,
    "quotes": quotes,
    "account": account,
    "positions": positions
}

# 咨询蜂群获取信号
signals = consult_swarm(sector="TECH", market_data=market_data)

print(f"蜂群返回 {len(signals)} 个信号:")
for signal in signals:
    print(f"  - {signal['instance_id']}: {signal['signal']} on {signal['target']}")

# === DECIDE 阶段 ===
from skills import place_order_with_guard

approved_trades = []
for signal in signals:
    if signal["signal"] == "NO_TRADE":
        continue

    # 根据安全限制验证
    result = place_order_with_guard(
        symbol=signal["target"],
        strategy=signal["signal"],
        legs=signal["params"]["legs"],
        max_risk=signal["params"]["max_risk"],
        capital_required=signal["params"]["capital_required"]
    )

    if result.success:
        approved_trades.append((signal, result))
    else:
        print(f"❌ 已拒绝: {result.error}")

# === ACT 阶段 ===
from skills.mcp_bridge import execute_order_with_ibkr

for signal, validated_order in approved_trades:
    try:
        # 提交到 IBKR
        ibkr_result = mcp__ibkr__place_order(
            symbol=signal["target"],
            strategy=signal["signal"],
            legs=signal["params"]["legs"],
            max_risk=signal["params"]["max_risk"],
            capital_required=signal["params"]["capital_required"]
        )

        # 更新交易状态
        final_result = execute_order_with_ibkr(
            validated_order=validated_order,
            legs=signal["params"]["legs"],
            symbol=signal["target"],
            strategy=signal["signal"],
            max_risk=signal["params"]["max_risk"],
            capital_required=signal["params"]["capital_required"],
            metadata={"ibkr_result": ibkr_result}
        )

        if final_result.success:
            print(f"✅ 订单已提交: {signal['target']} (order_id={final_result.order_id})")
        else:
            print(f"❌ IBKR 拒绝: {final_result.error}")

    except Exception as e:
        print(f"❌ 错误: {e}")
```

## 验证检查清单

在考虑实盘交易前完成这些测试：

### 安全层测试

- [ ] **最大风险违规**: 尝试 max_risk > $500 的订单
  - 预期: 拒绝并记录安全违规
- [ ] **最大资金违规**: 尝试 capital > $2000 的订单
  - 预期: 拒绝并记录安全违规
- [ ] **熔断器**: 模拟 10% 回撤
  - 预期: 所有交易停止，需手动重置

### 功能测试

- [ ] **账户数据**: 验证真实 IBKR 账户值（非 $10,000 模拟值）
- [ ] **持仓获取**: 从 IBKR 获取当前持仓
- [ ] **蜂群执行**: 蜂群在 30 秒内返回信号
- [ ] **订单验证**: place_order_with_guard() 正确验证
- [ ] **订单提交**: IBKR MCP 接受有效的模拟订单
- [ ] **快照记录**: 每个决策在 data_lake/snapshots/ 中创建快照
- [ ] **交易记录**: 订单记录到 trades.db

### 看门狗测试

- [ ] **心跳监控**: 看门狗检测到停滞的心跳（停止 main_loop）
- [ ] **真实账户值**: 看门狗显示真实 IBKR 值，而非 $10,000
- [ ] **熔断器触发**: 看门狗可在回撤时触发熔断器
- [ ] **独立进程**: 看门狗作为独立进程运行（用 `ps aux | grep watchdog` 检查）

### 30 天验证期

连续运行模拟交易 30 天：

1. **每日监控**（15 分钟/天）:
   - 检查日志中的错误
   - 查看 data_lake/snapshots/ 中的快照
   - 验证没有熔断器触发
   - 在 trades.db 中查看交易决策

2. **每周回顾**（1 小时/周）:
   - 分析 P&L（如果有交易执行）
   - 查看安全违规
   - 检查蜂群信号质量
   - 如需要更新策略模板

3. **追踪指标**:
   ```sql
   -- 查询交易数据库
   SELECT
       COUNT(*) as total_signals,
       SUM(CASE WHEN status='VALIDATED' THEN 1 ELSE 0 END) as validated,
       SUM(CASE WHEN status='REJECTED' THEN 1 ELSE 0 END) as rejected,
       AVG(CASE WHEN status='FILLED' THEN pnl ELSE NULL END) as avg_pnl
   FROM trades;
   ```

## 故障排除

### "Circuit breaker active - skipping cycle"

**原因**: 熔断器已触发（10% 回撤或手动触发）

**修复**:
```bash
# 重置熔断器
python -c "
import json
from pathlib import Path

memory_file = Path.home() / 'trading_workspace/state/agent_memory.json'
with open(memory_file, 'w') as f:
    json.dump({
        'safety_state': {
            'circuit_breaker_triggered': False,
            'circuit_breaker_timestamp': None
        }
    }, f, indent=2)

print('Circuit breaker reset')
"
```

### "Using fallback account value: $10,000"

**原因**: 看门狗无法连接到 IBKR Gateway

**修复**:
1. 验证 IBKR Gateway 正在运行: `netstat -an | grep 4002`
2. 检查 .env 中有正确的 IBKR_PORT=4002
3. 在 IB Gateway 设置中启用 API
4. 将 "Read-Only API" 设置为 FALSE

### "ERROR: Failed to connect to IBKR"

**原因**: IBKR Gateway 未运行或端口错误

**修复**:
1. 启动 IB Gateway: `~/IBController/IBControllerGatewayStart.sh`
2. 等待 30 秒启动
3. 验证: `telnet localhost 4002`
4. 检查日志: `~/IBController/Logs/`

### 蜂群返回空信号

**原因**: LLM API 密钥缺失或无效

**修复**:
```bash
# 检查 .env 文件
grep OPENROUTER_API_KEY .env

# 测试 OpenRouter 连接
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

## 成功标准

在过渡到实盘交易前：

### 技术要求
- ✅ 所有单元测试通过
- ✅ 看门狗在 60 秒内检测到冻结进程
- ✅ 真实 IBKR 数据流（非模拟 $10,000）
- ✅ 熔断器在 10% 回撤时触发
- ✅ 安全层拒绝超限订单
- ✅ 所有决策记录并带快照

### 验证要求
- ✅ 完成 30 天模拟交易
- ✅ 日志中零关键错误
- ✅ P&L 跟踪准确
- ✅ 看门狗从未漏检问题
- ✅ 手动紧急停止开关测试通过

### 人工批准要求
- ✅ 策略表现符合预期
- ✅ 风险管理正常工作
- ✅ 您理解并接受风险
- ✅ 资金分配已决定
- ✅ 应急程序已记录

## 验证后的后续步骤

1. **与导师或经验丰富的交易员一起审查 30 天结果**
2. **如需要调整安全限制**（在 .env 和 execution_gate.py 中）
3. **小额开始**实盘交易（例如 $5,000 账户）
4. **密切监控**实盘交易的第一周
5. **随着信心建立逐步扩大规模**

## 应急程序

如果模拟交易期间出现问题：

### 手动紧急停止开关
```bash
# 终止所有进程
pkill -f "python runtime/main_loop.py"
pkill -f "runtime.watchdog"

# 重置熔断器
python -c "from data_lake.db_helpers import reset_circuit_breaker; reset_circuit_breaker()"
```

### 关闭所有持仓（通过 IBKR）
```python
# 在 Claude Code 中
positions = mcp__ibkr__get_positions()

for pos in positions:
    print(f"正在关闭 {pos['symbol']}...")
    # 通过 IB Gateway UI 手动关闭或创建平仓订单
```

### 查看日志
```bash
# 检查发生了什么
tail -n 100 ~/trading_workspace/logs/main.log
tail -n 100 ~/trading_workspace/logs/watchdog.log

# 查看交易数据库
sqlite3 data_lake/trades.db "SELECT * FROM trades ORDER BY created_at DESC LIMIT 10;"
```

---

## 总结

模拟交易验证在实盘交易前是**强制性的**。花时间，彻底进行，不要跳过步骤。30 天验证期帮助您：

1. **建立信心**在系统的安全机制中
2. **理解** AI 的决策过程
3. **识别边缘情况**在冒真实资金风险之前
4. **根据市场条件优化策略**
5. **验证技术可靠性**在各种场景下

记住：**模拟交易应该是无聊的**。如果它令人兴奋或有压力，系统还没准备好进行实盘交易。
