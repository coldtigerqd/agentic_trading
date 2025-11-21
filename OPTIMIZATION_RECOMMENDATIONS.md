# Agentic AlphaHive 交易系统优化建议

**生成时间**: 2025-11-21
**分析基于**: 完整交易流程性能追踪与错误分析

---

## 📊 执行性能摘要

### 时间分析
- **总执行时间**: 0.29秒 ✅
- **性能瓶颈**:
  - 市场日历检查: 0.27秒 (93%)
  - 其他所有步骤: <0.02秒 (7%)

### 发现的问题
- ❌ **1个错误**: 技术指标计算失败
- ⚠️ **3个警告**: 市场日历、数据验证、监控列表不一致
- 🔄 **数据不一致**: 监控列表返回0个标的，但新鲜度报告显示12个标的

---

## 🐛 错误与警告详细分析

### 1. 技术指标计算错误 (严重)

**错误信息**:
```
index -1 is out of bounds for axis 0 with size 0
```

**根本原因**:
- `calculate_sma()` 等函数返回空数组
- 后续代码尝试访问 `result[-1]` 时失败
- 数据验证警告："字段 'close' 中存在无效数据"

**影响**:
- 技术分析步骤完全失败
- 无法计算 SMA、RSI、MACD 等关键指标
- 导致蜂群智能无法获得技术指标输入

**优化方案**:
```python
# 当前代码 (skills/technical_indicators.py)
def calculate_sma(data, period=20):
    # ... 验证后返回空数组
    return np.array([])  # ❌ 问题：没有明确告知调用者

# 优化后代码
def calculate_sma(data, period=20):
    result = _calculate_sma_internal(data, period)

    if len(result) == 0:
        raise ValueError(f"SMA计算失败: 数据不足或无效 (需要{period}个有效数据点)")

    return result

# 调用侧增加防御性检查
try:
    sma_20 = calculate_sma(closes, period=20)
    latest_sma = sma_20[-1]
except ValueError as e:
    print(f"⚠️ SMA计算跳过: {e}")
    latest_sma = None
```

---

### 2. 市场日历警告 (中等)

**警告信息**:
```
未能在 10 天内找到下次市场开盘时间 (NO_MARKET_OPEN_FOUND)
```

**根本原因**:
- 市场日历数据可能不完整或过期
- 硬编码的 10 天查找窗口可能不够（节假日、周末）

**影响**:
- 无法准确预测下次开盘时间
- 用户体验降低（不知道何时重新运行分析）

**优化方案**:
```python
# skills/market_calendar.py

def get_market_session_info():
    # 当前: 硬编码 10 天
    max_days_ahead = 10

    # 优化: 扩展到 30 天并支持假期数据
    max_days_ahead = 30

    # 如果仍未找到，返回预估值而非 None
    if not next_open:
        # 假设下周一开盘（最坏情况）
        next_monday = current_time + timedelta(days=(7 - current_time.weekday()))
        next_open_estimate = next_monday.replace(hour=9, minute=30, second=0)

        return {
            "next_market_open": next_open_estimate.isoformat(),
            "is_estimate": True,  # 标记为估算值
            "warning": "使用估算的开盘时间，建议更新市场日历数据"
        }
```

---

### 3. 监控列表数据不一致 (严重)

**观察到的不一致**:
- `get_watchlist()`: 返回 0 个标的
- `get_data_freshness_report()`: 返回 12 个标的
- `sync_watchlist_incremental()`: 报告监控 0 个标的

**根本原因**:
- `get_watchlist()` 依赖 `get_current_watchlist()` (来自 watchlist_manager.py)
- `get_data_freshness_report()` 直接查询 `data_lake/trades.db`
- 两个数据源不同步

**影响**:
- 关键：无法正确构建市场快照
- 蜂群智能无法获得完整的标的列表
- 数据同步逻辑失效

**优化方案**:

#### 方案 A: 统一数据源 (推荐)
```python
# skills/watchlist_manager.py

def get_current_watchlist() -> List[Dict]:
    """
    从 trades.db 的 ohlcv_cache 表中获取当前监控列表。

    统一数据源：基于实际有数据的标的，而非单独的 watchlist 表。
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 查询实际有缓存数据的标的
    query = """
    SELECT DISTINCT symbol,
           MAX(timestamp) as latest_timestamp,
           COUNT(*) as bar_count
    FROM ohlcv_cache
    GROUP BY symbol
    ORDER BY latest_timestamp DESC
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    watchlist = []
    for row in rows:
        watchlist.append({
            "symbol": row[0],
            "priority": 5,  # 默认优先级
            "latest_timestamp": row[1],
            "bar_count": row[2],
            "notes": "自动发现自缓存数据"
        })

    return watchlist
```

#### 方案 B: 创建独立的 watchlist 表 (长期方案)
```sql
-- 在 data_lake/trades.db 中创建专门的监控列表表
CREATE TABLE IF NOT EXISTS watchlist (
    symbol TEXT PRIMARY KEY,
    priority INTEGER DEFAULT 5,
    sector TEXT,
    notes TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- 初始化：从现有数据迁移
INSERT OR IGNORE INTO watchlist (symbol, priority)
SELECT DISTINCT symbol, 5 FROM ohlcv_cache;
```

---

### 4. 数据字段验证警告 (中等)

**警告信息**:
```
字段 'close' 中存在无效数据，返回空数组 (INVALID_FIELD_DATA)
```

**根本原因**:
- `technical_indicators.py` 的数据验证过于严格
- 可能将有效的 0 值或小数值误判为无效

**优化方案**:
```python
# skills/technical_indicators.py

def _validate_field(bars: List[Dict], field: str) -> np.ndarray:
    """验证并提取字段数据"""

    try:
        values = np.array([bar[field] for bar in bars], dtype=np.float64)

        # 当前: 过于严格的检查
        # if not np.all(np.isfinite(values)):
        #     return np.array([])

        # 优化: 更细粒度的检查
        invalid_mask = ~np.isfinite(values)
        invalid_count = np.sum(invalid_mask)

        if invalid_count > 0:
            # 如果无效数据<10%，插值填充
            if invalid_count / len(values) < 0.1:
                values = _interpolate_invalid(values, invalid_mask)
                warnings.warn(
                    f"字段 '{field}' 中有 {invalid_count} 个无效值，已插值填充 (INTERPOLATED)"
                )
            else:
                # 无效数据太多，返回空数组
                warnings.warn(
                    f"字段 '{field}' 中存在过多无效数据 ({invalid_count}/{len(values)})，"
                    f"返回空数组 (INVALID_FIELD_DATA)"
                )
                return np.array([])

        return values

    except (KeyError, TypeError, ValueError) as e:
        warnings.warn(f"字段 '{field}' 提取失败: {e} (FIELD_EXTRACTION_ERROR)")
        return np.array([])

def _interpolate_invalid(values: np.ndarray, invalid_mask: np.ndarray) -> np.ndarray:
    """线性插值填充无效值"""
    from scipy.interpolate import interp1d

    valid_indices = np.where(~invalid_mask)[0]
    invalid_indices = np.where(invalid_mask)[0]

    if len(valid_indices) < 2:
        return values  # 无法插值

    interpolator = interp1d(
        valid_indices,
        values[valid_indices],
        kind='linear',
        fill_value='extrapolate'
    )

    values[invalid_indices] = interpolator(invalid_indices)
    return values
```

---

## 🚀 架构优化建议

### 1. MCP 调用集成优化 (高优先级)

**当前问题**:
- Python 脚本无法直接调用 MCP 工具
- 需要在 Commander 层手动协调 Python 技能和 MCP 工具

**优化方案**:

创建统一的数据获取层：

```python
# skills/unified_data_layer.py

from typing import Dict, List, Optional
import json
import subprocess

class UnifiedDataLayer:
    """
    统一数据获取层：封装 MCP 调用和本地数据查询。

    通过 subprocess 调用 Claude Code CLI 来访问 MCP 工具。
    """

    def get_account_info(self) -> Dict:
        """获取账户信息（通过 MCP）"""
        try:
            # 调用 Claude Code CLI（假设已安装）
            result = subprocess.run(
                ['claude-code', 'mcp', 'call', 'ibkr', 'get_account'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                raise RuntimeError(f"MCP调用失败: {result.stderr}")

        except Exception as e:
            # 降级：返回模拟数据或缓存数据
            print(f"⚠️ 账户信息获取失败，使用缓存: {e}")
            return self._get_cached_account_info()

    def get_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """获取持仓（通过 MCP）"""
        # 类似实现...
        pass

    def get_market_snapshot(self, symbol: str) -> Dict:
        """
        获取市场快照：优先使用 MCP 实时数据，降级到缓存数据。
        """
        try:
            # 尝试 MCP 实时数据
            return self._fetch_mcp_snapshot(symbol)
        except Exception as e:
            # 降级到本地缓存
            print(f"⚠️ 实时数据获取失败，使用缓存: {e}")
            return self._get_cached_snapshot(symbol)
```

**优点**:
- 统一接口，简化调用
- 自动降级机制，提高鲁棒性
- 便于测试和模拟

---

### 2. 数据同步逻辑优化 (高优先级)

**当前问题**:
- 市场关闭时直接跳过同步
- 无法在盘前/盘后获取最新数据
- 数据新鲜度依赖硬编码的 15 分钟阈值

**优化方案**:

```python
# skills/data_sync.py

def sync_watchlist_incremental(
    skip_if_market_closed: bool = False,  # 改为 False
    force_sync: bool = False,
    max_staleness_minutes: int = 15  # 可配置阈值
) -> Dict:
    """
    增量同步监控列表数据。

    优化：
    1. 支持盘前/盘后数据同步
    2. 可配置的数据新鲜度阈值
    3. 强制同步选项
    """

    session_info = get_market_session_info()

    # 优化：区分盘中、盘前、盘后、周末
    if session_info['session'] == 'WEEKEND' and not force_sync:
        return {
            'should_sync': False,
            'message': '周末市场关闭，建议周一开盘前同步'
        }

    if session_info['session'] in ['PRE_MARKET', 'AFTER_HOURS']:
        # 盘前/盘后：使用更宽松的新鲜度阈值
        max_staleness_minutes = 60  # 1小时
        print(f"ℹ️ {session_info['session']}: 使用放宽的新鲜度阈值 ({max_staleness_minutes}分钟)")

    # 获取需要同步的标的
    symbols_to_sync = _get_stale_symbols(max_staleness_minutes)

    if not symbols_to_sync and not force_sync:
        return {
            'should_sync': False,
            'message': f'所有数据新鲜度 < {max_staleness_minutes} 分钟'
        }

    # 执行同步...
    return {
        'should_sync': True,
        'symbols_to_sync': symbols_to_sync,
        'total_symbols': len(symbols_to_sync)
    }
```

---

### 3. 错误处理与降级策略 (中优先级)

**当前问题**:
- 单点失败：一个技能失败导致整个流程中断
- 缺乏降级机制

**优化方案**:

创建容错的 Commander 工作流：

```python
# skills/commander_workflow.py

from typing import Dict, Any, Optional
from dataclasses import dataclass
import traceback

@dataclass
class WorkflowStep:
    name: str
    function: callable
    required: bool = True  # 是否必需
    fallback: Optional[callable] = None  # 降级函数
    timeout: int = 30  # 超时时间（秒）

class CommanderWorkflow:
    """
    容错的 Commander 工作流引擎。

    特性：
    - 可选步骤：失败后继续执行
    - 降级机制：失败时调用备用函数
    - 超时保护：防止步骤卡死
    - 详细日志：记录每步的成功/失败
    """

    def __init__(self):
        self.results = {}
        self.errors = {}

    def execute(self, steps: List[WorkflowStep]) -> Dict[str, Any]:
        """执行工作流"""

        for step in steps:
            step_name = step.name

            try:
                print(f"\n▶ 执行: {step_name}")

                # 执行步骤（带超时）
                result = self._execute_with_timeout(
                    step.function,
                    timeout=step.timeout
                )

                self.results[step_name] = result
                print(f"✅ 成功: {step_name}")

            except Exception as e:
                error_msg = str(e)
                self.errors[step_name] = error_msg

                print(f"❌ 失败: {step_name} - {error_msg}")

                # 尝试降级函数
                if step.fallback:
                    try:
                        print(f"  ↳ 尝试降级方案...")
                        fallback_result = step.fallback()
                        self.results[step_name] = fallback_result
                        print(f"  ✅ 降级成功")
                        continue
                    except Exception as fallback_error:
                        print(f"  ❌ 降级失败: {fallback_error}")

                # 必需步骤失败 → 终止工作流
                if step.required:
                    print(f"\n⚠️ 必需步骤失败，终止工作流")
                    break
                else:
                    print(f"  ↳ 可选步骤，继续执行")

        return {
            'results': self.results,
            'errors': self.errors,
            'success': len(self.errors) == 0
        }

    def _execute_with_timeout(self, func, timeout):
        """带超时的函数执行"""
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError(f"步骤超时 ({timeout}秒)")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

        try:
            result = func()
            signal.alarm(0)  # 取消超时
            return result
        except TimeoutError:
            signal.alarm(0)
            raise

# 使用示例
def run_trading_analysis():
    workflow = CommanderWorkflow()

    steps = [
        WorkflowStep(
            name="市场状态检查",
            function=lambda: get_market_session_info(),
            required=True
        ),
        WorkflowStep(
            name="账户信息获取",
            function=lambda: mcp_get_account(),
            required=True,
            fallback=lambda: get_cached_account_info()  # 降级到缓存
        ),
        WorkflowStep(
            name="数据同步",
            function=lambda: sync_watchlist_incremental(),
            required=False,  # 可选：数据同步失败不影响后续分析
            timeout=60
        ),
        WorkflowStep(
            name="技术指标计算",
            function=lambda: calculate_all_indicators(),
            required=False,
            fallback=lambda: {}  # 降级：返回空字典
        ),
        WorkflowStep(
            name="蜂群智能咨询",
            function=lambda: consult_swarm(sector="ALL"),
            required=True  # 必需：蜂群是核心功能
        )
    ]

    return workflow.execute(steps)
```

---

## 📈 性能优化建议

### 1. 数据库查询优化 (中优先级)

**当前问题**:
- `get_historical_bars()` 每次查询都扫描全表
- 缺少索引

**优化方案**:

```sql
-- data_lake/trades.db

-- 为常用查询字段添加索引
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_timestamp
ON ohlcv_cache(symbol, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_ohlcv_interval
ON ohlcv_cache(interval, symbol, timestamp DESC);

-- 复合索引优化多时间周期查询
CREATE INDEX IF NOT EXISTS idx_ohlcv_mtf
ON ohlcv_cache(symbol, interval, timestamp DESC);
```

**预期效果**:
- 查询速度提升 5-10 倍
- 特别优化 `get_multi_timeframe_data()` 性能

---

### 2. 缓存策略优化 (低优先级)

**当前问题**:
- 每次都重新计算技术指标
- 无缓存机制

**优化方案**:

```python
# skills/indicator_cache.py

import hashlib
from functools import lru_cache
from typing import List, Dict

class IndicatorCache:
    """技术指标计算缓存"""

    @staticmethod
    def _compute_hash(symbol: str, interval: str, lookback: int) -> str:
        """计算数据指纹"""
        key = f"{symbol}:{interval}:{lookback}"
        return hashlib.md5(key.encode()).hexdigest()

    @lru_cache(maxsize=128)
    def get_indicators(
        self,
        symbol: str,
        interval: str,
        lookback: int
    ) -> Dict:
        """
        获取缓存的技术指标。

        LRU缓存：最多缓存128个标的的指标计算结果。
        """
        # 获取数据
        bars = get_historical_bars(symbol, interval, lookback)

        # 计算指标
        closes = [bar['close'] for bar in bars['bars']]

        return {
            'sma_20': calculate_sma(closes, period=20),
            'rsi_14': calculate_rsi(closes, period=14),
            'macd': calculate_macd(closes),
            # ...
        }
```

---

## 🏗️ 架构重构建议 (长期)

### 1. 事件驱动架构

**当前架构**:
```
Commander (手动循环)
  → Skills (同步调用)
    → MCP Tools (阻塞调用)
```

**优化后架构**:
```
Event Bus (消息队列)
  ├─ Market Data Events (实时推送)
  ├─ Account Events (持仓变化)
  ├─ Signal Events (蜂群信号)
  └─ Order Events (订单状态)

Commander (事件订阅者)
  ↓ 响应事件
  ↓ 发布命令
  ↓
Skills (事件处理器)
```

**优点**:
- 解耦组件
- 支持实时响应
- 易于扩展

---

### 2. 配置驱动的策略系统

**当前问题**:
- 硬编码的阈值和参数
- 修改策略需要改代码

**优化方案**:

```yaml
# config/strategy_config.yaml

trading_strategy:
  name: "AlphaHive v1.0"

  risk_management:
    max_trade_risk: 500  # 单笔最大风险
    max_capital_per_trade: 2000
    daily_loss_limit: 1000
    circuit_breaker_drawdown: 0.10  # 10%

  signal_filtering:
    min_confidence: 0.70
    preferred_confidence: 0.80
    max_positions: 10
    max_sector_concentration: 0.30

  data_quality:
    max_staleness_minutes: 15
    min_bars_for_analysis: 20
    market_sessions:
      - REGULAR  # 只在正常交易时段交易
      # - PRE_MARKET  # 可选：盘前交易
      # - AFTER_HOURS  # 可选：盘后交易

  swarm_intelligence:
    max_concurrent: 50
    timeout_seconds: 30
    sectors:
      - ALL
      - TECH
      - FINANCE
```

**加载配置**:
```python
# skills/config_loader.py

import yaml
from pathlib import Path

class StrategyConfig:
    def __init__(self, config_path: str = "config/strategy_config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

    @property
    def max_trade_risk(self) -> float:
        return self.config['trading_strategy']['risk_management']['max_trade_risk']

    @property
    def min_confidence(self) -> float:
        return self.config['trading_strategy']['signal_filtering']['min_confidence']

    # ...其他配置属性

# 全局单例
CONFIG = StrategyConfig()
```

---

## 📋 优先级总结

### 🔴 高优先级（立即修复）

1. **技术指标计算错误** → 添加防御性检查和异常处理
2. **监控列表数据不一致** → 统一数据源
3. **MCP 调用集成** → 创建统一数据层

### 🟡 中优先级（本周完成）

4. **市场日历优化** → 扩展查找窗口，支持估算值
5. **数据字段验证** → 支持插值填充
6. **容错工作流** → 实现降级策略
7. **数据库索引** → 优化查询性能

### 🟢 低优先级（长期规划）

8. **指标缓存** → LRU 缓存机制
9. **事件驱动架构** → 重构为事件总线
10. **配置驱动策略** → YAML 配置系统

---

## 🧪 测试建议

### 1. 单元测试覆盖

**当前状态**: 缺少测试

**建议**:
```python
# tests/test_technical_indicators.py

import pytest
from skills import calculate_sma, calculate_rsi

def test_sma_valid_data():
    """测试 SMA 正常数据"""
    data = [100, 101, 102, 103, 104, 105]
    result = calculate_sma(data, period=3)

    assert len(result) == 4  # 6 - 3 + 1 = 4
    assert result[-1] == pytest.approx(104.0, rel=1e-2)

def test_sma_insufficient_data():
    """测试 SMA 数据不足"""
    data = [100, 101]

    with pytest.raises(ValueError, match="数据不足"):
        calculate_sma(data, period=3)

def test_sma_invalid_data():
    """测试 SMA 无效数据"""
    data = [100, float('nan'), 102, None, 104]

    # 应该过滤/插值无效值
    result = calculate_sma(data, period=3)
    assert len(result) > 0  # 应该返回有效结果
```

### 2. 集成测试

```python
# tests/test_trading_workflow.py

def test_full_trading_analysis_market_closed():
    """测试市场关闭时的完整分析流程"""

    # 模拟市场关闭
    with mock_market_session(session='CLOSED'):
        result = run_trading_analysis()

    # 验证：数据同步被跳过
    assert result['steps']['数据同步']['skipped'] == True

    # 验证：仍能获取账户信息（从缓存）
    assert 'account_info' in result['results']

    # 验证：蜂群咨询被跳过（数据过期）
    assert result['steps']['蜂群咨询']['skipped'] == True

def test_full_trading_analysis_market_open():
    """测试市场开盘时的完整分析流程"""

    with mock_market_session(session='REGULAR'):
        result = run_trading_analysis()

    # 验证：所有步骤都执行
    assert result['steps']['数据同步']['completed'] == True
    assert result['steps']['蜂群咨询']['completed'] == True

    # 验证：获得交易信号
    assert len(result['signals']) > 0
```

---

## 📝 文档改进建议

### 1. API 文档

为所有 skills 函数添加详细的文档字符串：

```python
def get_historical_bars(
    symbol: str,
    interval: str = "5min",
    lookback_days: int = 30
) -> Dict:
    """
    查询标的的历史 OHLCV K线数据。

    Args:
        symbol: 股票代码（例如 "AAPL"）
        interval: K线周期
            - "5min": 5分钟K线
            - "15min": 15分钟K线
            - "1h": 1小时K线
            - "daily": 日线
        lookback_days: 回溯天数（默认30天）

    Returns:
        Dict: {
            "bars": List[Dict],  # K线数据列表
            "bar_count": int,    # K线数量
            "cache_hit": bool,   # 是否缓存命中
            "query_time_ms": float  # 查询耗时（毫秒）
        }

    Raises:
        ValueError: symbol 为空或无效
        DatabaseError: 数据库查询失败

    Examples:
        >>> result = get_historical_bars("AAPL", interval="5min", lookback_days=7)
        >>> print(f"获取 {result['bar_count']} 根K线")
        >>> latest_close = result['bars'][-1]['close']
        >>> print(f"最新收盘价: ${latest_close:.2f}")

    Notes:
        - 如果请求的数据不在缓存中，返回 cache_hit=False
        - 5分钟K线会聚合为更大周期（15min, 1h, daily）
        - 查询性能: ~5-10ms (有索引)
    """
```

### 2. 错误代码参考

创建错误代码查找表：

```markdown
# docs/ERROR_CODES.md

## 错误代码参考

### 数据质量错误

| 代码 | 描述 | 解决方案 |
|------|------|----------|
| `INSUFFICIENT_DATA` | 数据点不足以计算指标 | 增加 `lookback_days` 参数 |
| `INVALID_FIELD_DATA` | 字段包含无效值（NaN/Null） | 检查数据源，考虑使用插值 |
| `STALE_DATA` | 数据过期 (>15分钟) | 运行 `sync_watchlist_incremental()` |

### 市场状态错误

| 代码 | 描述 | 解决方案 |
|------|------|----------|
| `MARKET_CLOSED` | 市场已关闭 | 等待市场开盘或使用历史数据分析 |
| `NO_MARKET_OPEN_FOUND` | 未找到下次开盘时间 | 更新市场日历数据 |
```

---

## 🎯 总结

### 关键发现
1. ✅ **性能优秀**: 0.29秒完成完整流程
2. ❌ **错误处理不足**: 技术指标计算失败导致分析中断
3. ⚠️ **数据不一致**: 监控列表数据源混乱
4. 📊 **架构限制**: MCP 调用需要在 Python 外部协调

### 快速改进方案 (本周可完成)
1. 修复技术指标计算的错误处理
2. 统一监控列表数据源
3. 添加容错工作流引擎
4. 创建数据库索引

### 长期演进方向
1. 事件驱动架构
2. 配置驱动策略系统
3. 完善测试覆盖
4. 改进文档质量

---

**生成工具**: Agentic AlphaHive Commander
**版本**: v1.0.0
**最后更新**: 2025-11-21
