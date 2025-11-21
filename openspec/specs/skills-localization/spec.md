# skills-localization Specification

## Purpose
TBD - created by archiving change localize-to-chinese. Update Purpose after archive.
## Requirements
### Requirement: Print Statements in Chinese

All user-facing print statements in skill modules MUST be translated to Chinese while preserving structured data output.

**Rationale**: Print statements are visible to operators during runtime. Chinese messages improve operator comprehension and debugging speed.

#### Scenario: Data sync status messages in Chinese

**Given** the `sync_watchlist_incremental()` skill is invoked
**When** the function prints status messages during data synchronization
**Then**:
- Progress messages MUST be in Chinese (e.g., "📡 正在同步 50 个标的...")
- Symbol names and timestamps MUST remain in original format
- Success indicators (✅, ⚠️, ❌) MUST be preserved
- Structured data keys MUST remain in English

**Example Transformation**:
```python
# Before
print(f"📡 Syncing {sync_info['total_symbols']} symbols...")
print(f"  ✅ {symbol}: Fresh data @ {result['timestamp']}")
print(f"  ⏭️  {symbol}: Already cached")

# After
print(f"📡 正在同步 {sync_info['total_symbols']} 个标的...")
print(f"  ✅ {symbol}: 新鲜数据 @ {result['timestamp']}")
print(f"  ⏭️  {symbol}: 已缓存")
```

**Validation**:
- Execute `sync_watchlist_incremental()` in test environment
- Verify Chinese output displays correctly in terminal
- Confirm no encoding errors (UnicodeEncodeError)

---

### Requirement: Logger Messages in Chinese

All logger calls (`logger.info()`, `logger.error()`, `logger.warning()`) MUST be translated to Chinese with English error codes preserved.

**Rationale**: Log files are reviewed by operators for troubleshooting. Chinese messages reduce cognitive load while English error codes enable grep-based analysis.

#### Scenario: ThetaData client error logging in Chinese

**Given** the `fetch_snapshot_with_rest()` function encounters an HTTP error
**When** the error is logged via `logger.error()`
**Then**:
- The error message MUST be in Chinese
- The exception details MUST include English error class name
- The symbol and endpoint MUST be preserved
- Log level MUST remain unchanged

**Example Transformation**:
```python
# Before
logger.error(f"Cannot connect to Theta Terminal. Is it running?")
logger.error(f"Failed to fetch {symbol}: {e}")

# After
logger.error(f"无法连接到 Theta Terminal，程序是否正在运行？")
logger.error(f"获取数据失败 {symbol}: {e}")
```

**Validation**:
- Trigger error scenario (e.g., disconnect ThetaData)
- Verify Chinese error message in log file
- Confirm `grep "获取数据失败"` finds relevant logs

---

### Requirement: Function Docstrings in Chinese

All public skill function docstrings MUST be translated to Chinese while keeping parameter names and return types in English.

**Rationale**: Docstrings appear in IDE tooltips and auto-generated documentation. Chinese docstrings improve developer experience for Chinese-speaking contributors.

#### Scenario: Skill function docstring displays in IDE

**Given** a skill function with Chinese docstring (e.g., `place_order_with_guard()`)
**When** a developer hovers over the function in VS Code or PyCharm
**Then**:
- The function description MUST be in Chinese
- The `Args:` section MUST use English parameter names with Chinese descriptions
- The `Returns:` section MUST describe return value in Chinese
- Type hints MUST remain in English

**Example Transformation**:
```python
# Before
def place_order_with_guard(symbol: str, strategy: str) -> OrderResult:
    """
    Place order with safety validation.

    Args:
        symbol: Underlying ticker (e.g., "AAPL")
        strategy: Strategy name (e.g., "PUT_SPREAD")

    Returns:
        OrderResult with status, trade_id, and error message
    """

# After
def place_order_with_guard(symbol: str, strategy: str) -> OrderResult:
    """
    通过安全验证层提交订单。

    Args:
        symbol: 标的代码（例如 "AAPL"）
        strategy: 策略名称（例如 "PUT_SPREAD"）

    Returns:
        OrderResult 包含状态、交易ID和错误信息
    """
```

**Validation**:
- Open skill file in IDE with IntelliSense enabled
- Hover over function call
- Verify Chinese docstring displays correctly

---

### Requirement: Preserve Code Structure and Variable Names

All variable names, function names, class names, and module names MUST remain in English after translation.

**Rationale**: English names maintain codebase consistency, enable international collaboration, and avoid encoding issues in version control.

#### Scenario: Code review shows consistent naming

**Given** a skill module is translated to Chinese
**When** the code is reviewed in a pull request
**Then**:
- All function names MUST remain in English (e.g., `sync_watchlist_incremental`)
- All variable names MUST remain in English (e.g., `market_snapshot`)
- All class names MUST remain in English (e.g., `OrderResult`)
- All module imports MUST remain unchanged

**Example (Correct)**:
```python
def sync_watchlist_incremental(skip_if_market_closed: bool = True):
    """增量同步监控列表中的市场数据"""
    sync_info = get_sync_status()  # Variable name in English
    print(f"正在同步 {len(symbols)} 个标的...")  # Print in Chinese
    return {"success": True, "message": "同步完成"}
```

**Example (Incorrect - DO NOT DO THIS)**:
```python
def 增量同步监控列表(如果市场关闭则跳过: bool = True):  # ❌ Function name translated
    同步信息 = 获取同步状态()  # ❌ Variable name translated
    print(f"正在同步 {len(标的)} 个标的...")  # ❌ Variable name translated
    return {"成功": True, "消息": "同步完成"}  # ❌ Dict keys translated
```

**Validation**:
- Run `pylint skills/` to check naming conventions
- Verify no non-ASCII identifiers in code
- Confirm all imports resolve correctly

---

