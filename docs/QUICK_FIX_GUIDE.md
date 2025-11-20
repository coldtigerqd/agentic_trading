# ThetaData API 修复 - 快速指南

## 🔧 需要做什么？

如果您遇到 ThetaData API 数据错误或字段不匹配的问题，请按照以下步骤操作：

### 1. 安装新依赖

```bash
cd /home/adt/project/agentic_trading
pip install -r requirements.txt
```

这将安装：
- `httpx>=0.27.0` - ThetaData API 客户端（替代 requests）
- `pytz>=2024.1` - 时区处理

### 2. 验证 Theta Terminal 运行

```bash
# 检查 Theta Terminal 是否运行
curl http://localhost:25503/v3/stock/snapshot/quote?symbol=SPY

# 如果未运行，启动它：
java -jar ThetaTerminalv3.jar
```

### 3. 运行测试验证修复

```bash
python scripts/test_theta_fix.py
```

**预期输出**：
```
=== Testing Quote Snapshot API ===

SPY:
  Timestamp: 2025-11-20T15:59:59.999
  Bid: $587.23 x 100 (Q)
  Ask: $587.25 x 200 (Q)
  Mid: $587.24

=== Testing OHLC Snapshot API ===

SPY:
  Timestamp: 2025-11-20T00:00:00.000
  Open:   $585.50
  High:   $588.00
  Low:    $584.20
  Close:  $587.24
  Volume: 45,234,567
  Count:  123,456

✓ All tests completed
```

---

## ✅ 修复内容总结

### 1. HTTP 客户端迁移
- **从**: `requests.Session()`
- **到**: `httpx.stream()`
- **原因**: ThetaData 官方推荐，更好的流式性能

### 2. CSV 字段解析修复

#### OHLC Snapshot
- **错误**: 字段顺序假设为 `Open, High, Low, Close, Volume`
- **正确**: `timestamp, symbol, open, high, low, close, volume, count`

#### Quote Snapshot
- **错误**: 字段顺序假设为 `Bid, Bid Size, Ask, Ask Size, Mid, Volume`
- **正确**: `timestamp, symbol, bid_size, bid_exchange, bid, bid_condition, ask_size, ask_exchange, ask, ask_condition`

### 3. 便捷函数修复
- 移除对不存在的 `quote['last']` 字段的引用
- 使用 `quote['mid']` 替代
- 正确处理缺失的 `volume` 数据

---

## 🚨 破坏性变更

**数据结构已更改**，如果您有代码依赖旧的字段，需要更新：

### 旧代码示例（会报错）：
```python
ohlc = client.get_ohlc_snapshot("AAPL")
price = ohlc['close']  # ❌ 可能读取到错误的值（之前是字段错位）
```

### 新代码（正确）：
```python
ohlc = client.get_ohlc_snapshot("AAPL")
price = ohlc['close']  # ✅ 现在读取正确的收盘价
timestamp = ohlc['timestamp']  # ✅ 新增字段
symbol = ohlc['symbol']  # ✅ 新增字段
count = ohlc['count']  # ✅ 新增字段（交易笔数）
```

---

## 📚 相关文档

- [完整修复文档](./THETADATA_API_FIX.md)
- [ThetaData API - OHLC](https://docs.thetadata.us/operations/stock_snapshot_ohlc.html)
- [ThetaData API - Quote](https://docs.thetadata.us/operations/stock_snapshot_quote.html)
- [Theta Terminal 设置](./THETA_TERMINAL_SETUP.md)

---

## 💡 故障排查

### 问题：`ModuleNotFoundError: No module named 'httpx'`
**解决方案**：
```bash
pip install httpx>=0.27.0
```

### 问题：`ConnectError: Cannot connect to Theta Terminal`
**解决方案**：
1. 确保 Theta Terminal 正在运行
2. 检查端口 25503 是否开放
3. 尝试手动启动：`java -jar ThetaTerminalv3.jar`

### 问题：字段数据仍然不正确
**解决方案**：
1. 确认已拉取最新代码
2. 重启 Python 解释器清除缓存
3. 运行测试脚本验证：`python scripts/test_theta_fix.py`

---

**修复日期**: 2025-11-20
