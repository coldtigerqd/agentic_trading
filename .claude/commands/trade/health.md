---
description: "市场健康检查 - 检查市场状态和数据质量"
---

# Trade Health Command

快速市场健康检查。

请运行以下脚本并解释结果：

```bash
python runtime/trade_health.py
```

此命令会检查：
- ✅ 市场开盘状态（CLOSED / PREMARKET / REGULAR / AFTERHOURS）
- ✅ 数据质量（GOOD / STALE / CRITICAL）
- ✅ 关键指数价格（SPY、QQQ）
- ✅ 数据年龄和新鲜度

运行完成后，请向用户总结：
- 当前市场状态
- 数据质量评估
- 是否适合进行交易分析
- 如果数据质量不佳，建议运行 `/trade:sync` 同步数据
