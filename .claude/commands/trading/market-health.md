---
name: 市场健康检查
description: 快速检查市场状态、数据质量和关键指数价格
category: 交易
tags: [market, health, check, quick]
---

# 市场健康检查命令

快速评估当前市场状态和数据质量，为交易决策提供基础环境判断。

## 命令语法
```bash
/market-health [选项]
```

## 实现方式
此命令使用稳定的Python脚本 `scripts/market_health.py` 来执行，避免了bash执行大段代码的不稳定性问题。

## 参数选项

### 显示选项
- `--verbose` - 显示详细信息 (默认: 表格格式)
- `--format <格式>` - 输出格式: table|json (默认: table)

### 帮助信息
- `--help` - 显示此帮助信息

## 支持的参数
脚本支持以下完整的参数列表：
```bash
python scripts/market_health.py [--format json|table] [--verbose] [--help]
```

## 使用示例

### 基础检查
```bash
# 快速健康检查
/market-health

# 详细模式
/market-health --verbose

# JSON格式输出
/market-health --format json

# 组合参数
/market-health --verbose --format json
```

## 检查内容

### 1. 市场交易状态
- 当前交易时段 (盘前、盘中、盘后)
- 市场开放状态
- 距离下次开盘时间

### 2. 数据质量评估
- 监控标的数据新鲜度
- 过期数据比例
- 数据覆盖范围

### 3. 关键指数状态
- SPY (标普500 ETF) 价格和延迟
- QQQ (纳斯达克100 ETF) 价格和延迟
- VIX (波动率指数) 如果可用

### 4. 系统连接状态
- IBKR 连接状态
- ThetaData 连接状态
- MCP服务器可用性

## 输出格式

### 简洁模式输出
```json
{
  "status": "健康",
  "market_open": true,
  "session": "盘中交易",
  "data_quality": "良好",
  "spy_price": 478.52,
  "spy_fresh": true,
  "qqq_price": 195.38,
  "qqq_fresh": true,
  "warnings": []
}
```

### 详细模式输出
```json
{
  "market_status": {
    "session": "REGULAR_TRADING",
    "market_open": true,
    "next_open": "2025-11-22 09:30:00",
    "time_to_close": "2小时15分"
  },
  "data_quality": {
    "total_symbols": 50,
    "fresh_symbols": 48,
    "stale_symbols": 2,
    "quality_score": "GOOD",
    "last_update": "2025-11-21 13:45:22"
  },
  "indices": {
    "SPY": {
      "price": 478.52,
      "change": "+1.23",
      "change_percent": "+0.26%",
      "age_seconds": 45,
      "fresh": true
    },
    "QQQ": {
      "price": 195.38,
      "change": "+0.89",
      "change_percent": "+0.46%",
      "age_seconds": 38,
      "fresh": true
    }
  },
  "connections": {
    "ibkr": "连接正常",
    "thetadata": "连接正常",
    "mcp_servers": "全部可用"
  },
  "warnings": [
    "2个标的数据可能过期"
  ],
  "recommendations": [
    "市场状态良好，适合交易分析",
    "建议更新过期标的数据"
  ],
  "timestamp": "2025-11-21 13:45:30"
}
```

### 数据质量重点输出
```json
{
  "data_quality_summary": {
    "overall_status": "STALE",
    "freshness_rate": "96%",
    "critical_issues": 0,
    "stale_symbols": [
      {
        "symbol": "AMD",
        "last_update": "2025-11-21 12:30:00",
        "age_minutes": 75
      },
      {
        "symbol": "TSLA",
        "last_update": "2025-11-21 12:45:00",
        "age_minutes": 60
      }
    ]
  },
  "action_required": "建议同步数据或跳过过期标的"
}
```

## 健康状态分类

### 🟢 健康 (GOOD)
- 市场正常开放
- 数据质量 > 90%
- 关键指数数据新鲜
- 无系统连接问题

### 🟡 警告 (STALE)
- 数据质量 70-90%
- 部分标的数据过期
- 系统连接基本正常

### 🔴 严重 (CRITICAL)
- 市场关闭或数据质量 < 70%
- 关键指数数据过期
- 系统连接问题

## 状态建议

### 市场开放 + 数据良好
> ✅ **建议**: 可以执行完整交易分析

### 市场开放 + 数据警告
> ⚠️ **建议**: 可以分析，但提高置信度要求，或跳过过期数据

### 市场关闭
> ⚠️ **建议**: 仅进行离线分析，使用 `--skip-sync` 参数

### 数据质量严重
> ❌ **建议**: 等待数据刷新，避免基于过期数据做决策

## 快速判断规则

此命令提供快速决策指导：
- 如果返回状态为"健康"，直接执行 `/trade-analysis`
- 如果有警告，使用 `--skip-sync` 或提高置信度要求
- 如果状态严重，等待市场数据改善

## 集成说明

此命令封装了以下技能和功能：
- `get_market_session_info()` - 市场时段信息
- `get_data_freshness_report()` - 数据新鲜度报告
- `get_latest_price()` - 最新价格获取
- `mcp__ibkr__health_check()` - IBKR连接检查

## 性能指标

- **响应时间**: < 1秒
- **数据获取**: < 2秒
- **状态评估**: < 0.5秒

---
*此命令提供快速的市场状态评估，帮助用户判断当前是否适合进行交易分析。*