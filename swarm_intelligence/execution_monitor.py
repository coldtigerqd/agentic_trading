"""
策略执行监控模块

用于跟踪策略执行历史、计算性能指标和维护统计信息。
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import os


@dataclass
class StrategyExecution:
    """策略执行记录"""
    strategy_id: str
    timestamp: str
    signals_generated: int
    high_confidence_signals: int
    execution_time: float
    success: bool
    errors: List[str]
    market_session: str
    data_quality: str


@dataclass
class PerformanceMetrics:
    """策略性能指标"""
    strategy_id: str
    total_executions: int
    avg_signals_per_execution: float
    high_confidence_rate: float
    avg_execution_time: float
    success_rate: float
    last_execution: str
    last_7_days_performance: Dict[str, Any]


class StrategyExecutionMonitor:
    """策略执行监控器"""

    def __init__(self, db_path: str = "data_lake/strategy_executions.db"):
        """
        初始化执行监控器

        Args:
            db_path: SQLite数据库路径
        """
        self.db_path = db_path
        self.execution_history: List[StrategyExecution] = []
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}
        self._ensure_database()
        self._load_history()

    def _ensure_database(self):
        """确保数据库和表存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS strategy_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    signals_generated INTEGER DEFAULT 0,
                    high_confidence_signals INTEGER DEFAULT 0,
                    execution_time REAL DEFAULT 0.0,
                    success BOOLEAN DEFAULT TRUE,
                    errors TEXT, -- JSON array of error strings
                    market_session TEXT,
                    data_quality TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建索引提高查询性能
            conn.execute("CREATE INDEX IF NOT EXISTS idx_strategy_id ON strategy_executions(strategy_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON strategy_executions(timestamp)")

    def _load_history(self):
        """从数据库加载历史记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM strategy_executions
                    ORDER BY timestamp DESC
                    LIMIT 1000
                """)

                for row in cursor.fetchall():
                    errors = json.loads(row['errors']) if row['errors'] else []
                    execution = StrategyExecution(
                        strategy_id=row['strategy_id'],
                        timestamp=row['timestamp'],
                        signals_generated=row['signals_generated'],
                        high_confidence_signals=row['high_confidence_signals'],
                        execution_time=row['execution_time'],
                        success=row['success'],
                        errors=errors,
                        market_session=row['market_session'],
                        data_quality=row['data_quality']
                    )
                    self.execution_history.append(execution)

            # 更新性能指标
            self._update_performance_metrics()

        except Exception as e:
            print(f"加载执行历史失败: {str(e)}")

    def log_execution(self, strategy_id: str, execution_result: Dict[str, Any]):
        """
        记录策略执行结果

        Args:
            strategy_id: 策略ID
            execution_result: 执行结果字典
        """
        try:
            # 创建执行记录
            execution = StrategyExecution(
                strategy_id=strategy_id,
                timestamp=datetime.now().isoformat(),
                signals_generated=len(execution_result.get('signals', [])),
                high_confidence_signals=len([
                    s for s in execution_result.get('signals', [])
                    if s.get('confidence', 0) >= 0.80
                ]),
                execution_time=execution_result.get('execution_time', 0.0),
                success=execution_result.get('success', True),
                errors=execution_result.get('errors', []),
                market_session=execution_result.get('market_session', 'UNKNOWN'),
                data_quality=execution_result.get('data_quality', 'UNKNOWN')
            )

            # 添加到内存记录
            self.execution_history.insert(0, execution)

            # 保存到数据库
            self._save_execution_to_db(execution)

            # 更新性能指标
            self._update_performance_metrics()

        except Exception as e:
            print(f"记录执行结果失败: {str(e)}")

    def _save_execution_to_db(self, execution: StrategyExecution):
        """将执行记录保存到数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO strategy_executions
                (strategy_id, timestamp, signals_generated, high_confidence_signals,
                 execution_time, success, errors, market_session, data_quality)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution.strategy_id,
                execution.timestamp,
                execution.signals_generated,
                execution.high_confidence_signals,
                execution.execution_time,
                execution.success,
                json.dumps(execution.errors),
                execution.market_session,
                execution.data_quality
            ))

    def _update_performance_metrics(self):
        """更新性能指标"""
        # 按策略分组统计
        strategy_stats = {}

        for execution in self.execution_history:
            strategy_id = execution.strategy_id
            if strategy_id not in strategy_stats:
                strategy_stats[strategy_id] = {
                    'executions': [],
                    'total_signals': 0,
                    'high_confidence_signals': 0,
                    'total_time': 0.0,
                    'successes': 0
                }

            stats = strategy_stats[strategy_id]
            stats['executions'].append(execution)
            stats['total_signals'] += execution.signals_generated
            stats['high_confidence_signals'] += execution.high_confidence_signals
            stats['total_time'] += execution.execution_time
            if execution.success:
                stats['successes'] += 1

        # 计算性能指标
        for strategy_id, stats in strategy_stats.items():
            executions = stats['executions']
            total_executions = len(executions)

            if total_executions > 0:
                # 基础指标
                avg_signals = stats['total_signals'] / total_executions
                high_conf_rate = stats['high_confidence_signals'] / max(stats['total_signals'], 1)
                avg_time = stats['total_time'] / total_executions
                success_rate = stats['successes'] / total_executions
                last_execution = executions[0].timestamp if executions else None

                # 最近7天表现
                last_7_days = self._get_last_7_days_performance(strategy_id, executions)

                self.performance_metrics[strategy_id] = PerformanceMetrics(
                    strategy_id=strategy_id,
                    total_executions=total_executions,
                    avg_signals_per_execution=round(avg_signals, 2),
                    high_confidence_rate=round(high_conf_rate, 3),
                    avg_execution_time=round(avg_time, 2),
                    success_rate=round(success_rate, 3),
                    last_execution=last_execution or "",
                    last_7_days_performance=last_7_days
                )

    def _get_last_7_days_performance(self, strategy_id: str, executions: List[StrategyExecution]) -> Dict[str, Any]:
        """计算最近7天的表现"""
        cutoff_date = datetime.now() - timedelta(days=7)
        recent_executions = [
            e for e in executions
            if datetime.fromisoformat(e.timestamp) >= cutoff_date
        ]

        if not recent_executions:
            return {
                'runs': 0,
                'signals': 0,
                'successes': 0,
                'avg_confidence': 0.0
            }

        total_signals = sum(e.signals_generated for e in recent_executions)
        total_high_conf = sum(e.high_confidence_signals for e in recent_executions)
        successes = sum(1 for e in recent_executions if e.success)

        return {
            'runs': len(recent_executions),
            'signals': total_signals,
            'successes': successes,
            'avg_confidence': round(total_high_conf / max(total_signals, 1), 3)
        }

    def get_performance_report(self, strategy_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取性能报告

        Args:
            strategy_id: 特定策略ID，None表示全部策略

        Returns:
            性能报告字典
        """
        if strategy_id:
            if strategy_id in self.performance_metrics:
                metrics = self.performance_metrics[strategy_id]
                return {
                    'strategy_id': strategy_id,
                    'metrics': asdict(metrics)
                }
            else:
                return {'error': f'策略 {strategy_id} 无性能数据'}
        else:
            # 全部策略的汇总报告
            total_executions = sum(m.total_executions for m in self.performance_metrics.values())
            total_signals = sum(m.avg_signals_per_execution * m.total_executions for m in self.performance_metrics.values())

            return {
                'summary': {
                    'total_strategies': len(self.performance_metrics),
                    'total_executions': total_executions,
                    'avg_signals_per_execution': round(total_signals / max(total_executions, 1), 2),
                    'overall_success_rate': round(
                        sum(m.success_rate * m.total_executions for m in self.performance_metrics.values())
                        / max(total_executions, 1), 3
                    ),
                    'avg_execution_time': round(
                        sum(m.avg_execution_time * m.total_executions for m in self.performance_metrics.values())
                        / max(total_executions, 1), 2
                    )
                },
                'strategies': {
                    sid: asdict(metrics) for sid, metrics in self.performance_metrics.items()
                }
            }

    def get_execution_history(self, strategy_id: Optional[str] = None,
                            limit: int = 100) -> List[StrategyExecution]:
        """
        获取执行历史

        Args:
            strategy_id: 特定策略ID
            limit: 返回记录数限制

        Returns:
            执行历史列表
        """
        history = self.execution_history

        if strategy_id:
            history = [e for e in history if e.strategy_id == strategy_id]

        return history[:limit]

    def get_strategy_health_status(self, strategy_id: str) -> Dict[str, Any]:
        """
        获取策略健康状态

        Args:
            strategy_id: 策略ID

        Returns:
            健康状态报告
        """
        if strategy_id not in self.performance_metrics:
            return {'status': 'UNKNOWN', 'message': '策略无执行记录'}

        metrics = self.performance_metrics[strategy_id]
        last_exec = datetime.fromisoformat(metrics.last_execution) if metrics.last_execution else None

        # 健康检查
        issues = []
        status = 'HEALTHY'

        # 检查最近执行时间
        if last_exec:
            days_since_last = (datetime.now() - last_exec).days
            if days_since_last > 7:
                issues.append(f'策略已{days_since_last}天未执行')
                if days_since_last > 30:
                    status = 'CRITICAL'
                elif days_since_last > 14:
                    status = 'WARNING'

        # 检查成功率
        if metrics.success_rate < 0.5:
            issues.append(f'成功率偏低 ({metrics.success_rate:.1%})')
            if metrics.success_rate < 0.3:
                status = 'CRITICAL'
            elif status != 'CRITICAL':
                status = 'WARNING'

        # 检查执行时间
        if metrics.avg_execution_time > 10.0:
            issues.append(f'平均执行时间过长 ({metrics.avg_execution_time:.1f}秒)')

        # 检查信号质量
        if metrics.high_confidence_rate < 0.3:
            issues.append(f'高置信度信号率偏低 ({metrics.high_confidence_rate:.1%})')

        return {
            'strategy_id': strategy_id,
            'status': status,
            'issues': issues,
            'last_execution': metrics.last_execution,
            'metrics': {
                'success_rate': metrics.success_rate,
                'avg_execution_time': metrics.avg_execution_time,
                'high_confidence_rate': metrics.high_confidence_rate,
                'total_executions': metrics.total_executions
            }
        }


def get_execution_monitor() -> StrategyExecutionMonitor:
    """获取全局执行监控器实例"""
    return StrategyExecutionMonitor()