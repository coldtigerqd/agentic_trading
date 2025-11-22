#!/bin/bash
# 监控历史数据回填进度

LOG_FILE="logs/backfill_3years.log"

echo "========================================"
echo "历史数据回填监控"
echo "========================================"
echo

# 检查进程是否还在运行
if pgrep -f "backfill_historical_data.py" > /dev/null; then
    echo "✓ 回填进程正在运行"
else
    echo "○ 回填进程已完成或未启动"
fi

echo

# 显示日志文件尾部
if [ -f "$LOG_FILE" ]; then
    echo "最新日志（最后20行）："
    echo "----------------------------------------"
    tail -20 "$LOG_FILE"
    echo "----------------------------------------"
    echo

    # 统计进度
    TOTAL_DATES=$(grep -c "trading dates to fetch" "$LOG_FILE" 2>/dev/null || echo "0")
    COMPLETED=$(grep -c "bars inserted from" "$LOG_FILE" 2>/dev/null || echo "0")
    TOTAL_BARS=$(grep -oP "Total bars inserted: \K[0-9]+" "$LOG_FILE" | tail -1 || echo "0")

    echo "进度统计："
    echo "  已完成股票: $COMPLETED"
    echo "  已插入数据条数: $TOTAL_BARS"
else
    echo "⚠ 日志文件不存在: $LOG_FILE"
fi

echo
echo "========================================"
echo "使用 'tail -f $LOG_FILE' 实时查看日志"
echo "========================================"
