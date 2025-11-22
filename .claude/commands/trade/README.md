---
description: "帮助文档 - 显示交易系统完整命令参考"
---

# Trading Commands Reference

显示 Agentic AlphaHive 交易系统的完整命令文档。

---

## 📋 可用命令

### 核心交易命令

1. **`/trade:health`** - 市场健康检查
   - 检查市场开盘状态
   - 评估数据质量（GOOD/STALE/CRITICAL）
   - 显示 SPY、QQQ 关键指数价格

2. **`/trade:analyze`** - 完整交易分析
   - 执行7步交易分析工作流
   - 参数：`--sector`, `--confidence`, `--max-signals`
   - 生成高置信度交易信号

3. **`/trade:risk`** - 持仓风险分析
   - 分析当前持仓风险水平
   - 参数：`--threshold` (默认70)
   - 提供风险管理建议

4. **`/trade:sync`** - 手动数据同步
   - 从 ThetaData 同步最新市场数据
   - 参数：`--symbols`, `--force`
   - 更新本地数据缓存

---

## 🚀 快速开始

### 每日交易流程

```bash
# 1. 检查市场状态
/trade:health

# 2. 评估持仓风险
/trade:risk

# 3. 执行交易分析
/trade:analyze

# 4. 根据结果决定执行
```

### 针对特定板块分析

```bash
# 高置信度科技板块分析
/trade:analyze --sector=tech --confidence=0.85
```

### 数据质量问题处理

```bash
# 1. 检查数据质量
/trade:health

# 2. 如果 CRITICAL，同步数据
/trade:sync

# 3. 确认恢复
/trade:health
```

---

## 📊 参数说明

### `/trade:analyze` 参数

**`--sector`** (可选)
- `tech` - 科技板块
- `finance` - 金融板块
- `healthcare` - 医疗板块
- `energy` - 能源板块
- `ALL` - 所有板块（默认）

**`--confidence`** (可选，默认 0.75)
- 范围：0.0 - 1.0
- 推荐值：0.70 (宽松), 0.75 (平衡), 0.85 (严格)

**`--max-signals`** (可选，默认 10)
- 范围：1 - 20
- 限制返回的信号数量

### `/trade:risk` 参数

**`--threshold`** (可选，默认 70)
- 范围：0 - 100
- 风险评分阈值，超过则警告

### `/trade:sync` 参数

**`--symbols`** (可选)
- 格式：逗号分隔的股票代码
- 示例：`AAPL,NVDA,TSLA`

**`--force`** (可选)
- 强制全量同步（谨慎使用）
- 会消耗大量 API 配额

---

## 🎯 使用场景

### 场景 1: 开盘前准备

```bash
/trade:health        # 确认市场开盘
/trade:risk         # 检查持仓风险
/trade:analyze      # 寻找交易机会
```

### 场景 2: 特定板块深度分析

```bash
/trade:analyze --sector=tech --confidence=0.85 --max-signals=5
```

### 场景 3: 持仓监控

```bash
# 盘中每 1-2 小时
/trade:risk --threshold=60
```

### 场景 4: 数据维护

```bash
# 开盘前确保数据最新
/trade:sync
```

---

## ⚠️ 故障排查

### 数据质量 CRITICAL

**解决方案**:
1. 检查 Theta Terminal 是否运行
2. 运行 `/trade:sync` 同步数据
3. 检查网络连接

### 无交易信号

**解决方案**:
1. 降低置信度：`/trade:analyze --confidence=0.70`
2. 尝试其他板块：`/trade:analyze --sector=finance`
3. 增加信号数：`/trade:analyze --max-signals=20`

### 订单被拒绝

**原因**:
- 超过风险限额（单笔 $500）
- 超过资金限额（单笔 $2,000）
- 超过每日亏损限额（$1,000）
- 集中度超过 30%

**解决方案**: 调整仓位大小或等待限额重置

---

## 🔒 安全约束

所有交易受以下硬性限额保护（**不可绕过**）：

| 限额类型 | 值 |
|---------|-----|
| 单笔交易最大风险 | $500 |
| 单笔交易最大资金 | $2,000 |
| 每日累计亏损上限 | $1,000 |
| 单标的集中度 | ≤ 30% |
| 账户回撤熔断 | 10% |

---

## 📚 更多信息

详细文档请参考：
- **系统架构**: `README.md` Section 2-3
- **工作流说明**: `README.md` Section 5
- **脚本参考**: `README.md` Section 6
- **指挥官提示词**: `prompts/commander_system.md`

---

**提示**: 这是一个帮助文档命令。要执行实际交易操作，请使用上述列出的具体命令。
