# Trade Sync Command

手动触发数据同步。

请运行以下脚本并解释结果：

```bash
python runtime/data_sync_daemon.py --once
```

此命令会：
- ✅ 检查市场状态和交易时段
- ✅ 同步观察列表中所有标的的最新数据
- ✅ 增量更新（只获取新数据，自动去重）
- ✅ 显示同步统计（成功/失败/耗时）

**数据来源**: ThetaData v3 API（venue='utp_cta'）
**数据延迟**: 免费计划有15分钟延迟（正常现象）

运行完成后，请向用户总结：
- 同步的标的数量
- 新增的数据条数
- 数据新鲜度
- 任何错误或警告

**后台运行选项**:
如果用户需要定期自动同步，建议：
```bash
# 每10分钟同步一次
python runtime/data_sync_daemon.py --interval 10
```
