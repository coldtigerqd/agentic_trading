# ThetaData API 修复文档

## 问题描述

原有的 `thetadata_client.py` 实现中存在两个关键问题：

1. **CSV 响应解析的字段顺序错误** - 字段顺序与 ThetaData 官方 API 文档不匹配，导致所有字段数据错位
2. **使用了错误的 HTTP 客户端** - 使用 `requests.Session()` 而非推荐的 `httpx.stream()`

## 修复内容

### 0. 迁移到 httpx.stream()

**问题**：原代码使用 `requests.Session()` 进行流式读取，但 ThetaData 官方推荐使用 `httpx.stream()`

**修复前**：
```python
import requests

self.session = requests.Session()
response = self.session.get(url, params=params, timeout=10, stream=True)
for line in response.iter_lines():
    ...
```

**修复后**：
```python
import httpx

with httpx.stream("GET", url, params=params, timeout=60) as response:
    response.raise_for_status()
    for line in response.iter_lines():
        ...
```

**优势**：
- 更好的流式处理性能
- 与 ThetaData 官方示例代码一致
- 更现代的异步支持（未来扩展）
- 自动资源管理（上下文管理器）

### 1. `get_ohlc_snapshot()` 方法

**错误的假设**（修复前）：
```python
# CSV 格式：Open,High,Low,Close,Volume
data_row[0] = open   # ❌ 实际是 timestamp
data_row[1] = high   # ❌ 实际是 symbol
data_row[2] = low    # ❌ 实际是 open
data_row[3] = close  # ❌ 实际是 high
data_row[4] = volume # ❌ 实际是 low
```

**正确的格式**（修复后）：
```python
# CSV 格式（根据 ThetaData API 文档）：
# timestamp, symbol, open, high, low, close, volume, count
data_row[0] = timestamp
data_row[1] = symbol
data_row[2] = open
data_row[3] = high
data_row[4] = low
data_row[5] = close
data_row[6] = volume
data_row[7] = count
```

**参考文档**: https://docs.thetadata.us/operations/stock_snapshot_ohlc.html

---

### 2. `get_quote_snapshot()` 方法

**错误的假设**（修复前）：
```python
# CSV 格式：Bid,Bid Size,Ask,Ask Size,Mid,Volume
data_row[0] = bid      # ❌ 实际是 timestamp
data_row[1] = bid_size # ❌ 实际是 symbol
data_row[2] = ask      # ❌ 实际是 bid_size
data_row[3] = ask_size # ❌ 实际是 bid_exchange
data_row[4] = mid      # ❌ 实际是 bid
data_row[5] = volume   # ❌ 实际是 bid_condition
```

**正确的格式**（修复后）：
```python
# CSV 格式（根据 ThetaData API 文档）：
# timestamp, symbol, bid_size, bid_exchange, bid, bid_condition,
# ask_size, ask_exchange, ask, ask_condition
data_row[0] = timestamp
data_row[1] = symbol
data_row[2] = bid_size
data_row[3] = bid_exchange
data_row[4] = bid
data_row[5] = bid_condition
data_row[6] = ask_size
data_row[7] = ask_exchange
data_row[8] = ask
data_row[9] = ask_condition

# Mid price 计算（不在 API 响应中）
mid = (bid + ask) / 2
```

**参考文档**: https://docs.thetadata.us/operations/stock_snapshot_quote.html

---

### 3. `fetch_snapshot_with_rest()` 便捷函数

**修复的问题**：
- 移除对不存在的 `quote['last']` 字段的引用
- 使用 `quote['mid']` 替代
- 移除对不存在的 `quote['volume']` 字段的引用
- Quote 快照不包含 volume 数据，fallback 时设为 0

---

## 测试

运行测试脚本验证修复：

```bash
# 1. 安装依赖（包括 httpx）
pip install -r requirements.txt

# 2. 确保 Theta Terminal 正在运行
java -jar ThetaTerminalv3.jar

# 3. 运行测试
python scripts/test_theta_fix.py
```

测试脚本会验证：
1. Quote Snapshot 解析是否正确
2. OHLC Snapshot 解析是否正确
3. 便捷函数是否正常工作

---

## 影响范围

此修复影响以下模块：
- `skills/thetadata_client.py` - 核心 API 客户端
- `requirements.txt` - 新增 `httpx` 依赖
- 任何使用 `ThetaDataClient` 的下游代码
- 数据同步守护进程（如果使用）

**向后兼容性**：
- ⚠️ **返回数据结构已更改**
  - 新增字段：`timestamp`, `symbol`, `count`, `bid_exchange`, `ask_exchange` 等
  - 下游代码可能需要适配新的字段名

- ⚠️ **依赖变更**
  - 从 `requests` 迁移到 `httpx`
  - 需要运行 `pip install -r requirements.txt` 安装新依赖
  - `requests` 库不再被 ThetaData 客户端使用（但 MCP 服务器可能仍在使用）

---

## 代码审查检查清单

- [x] 迁移到 `httpx.stream()` 替代 `requests.Session()`
- [x] CSV 字段顺序与官方文档匹配
- [x] 添加了边界检查（`len(data_row) > N`）
- [x] 正确处理空值情况
- [x] 更新了 docstring 说明返回结构
- [x] 修复了便捷函数的字段引用
- [x] 更新了异常处理（`httpx.*` 异常）
- [x] 添加了 `httpx` 和 `pytz` 到 requirements.txt
- [x] 创建了测试脚本验证修复

---

## 相关文档

- [ThetaData API - Stock Snapshot OHLC](https://docs.thetadata.us/operations/stock_snapshot_ohlc.html)
- [ThetaData API - Stock Snapshot Quote](https://docs.thetadata.us/operations/stock_snapshot_quote.html)
- [ThetaData Terminal Setup](./THETA_TERMINAL_SETUP.md)

---

**修复日期**: 2025-11-20
**修复者**: Claude Code (via user request)
