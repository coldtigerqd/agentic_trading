# 架构教训和学习记录 - 2025-11-21

## 关键错误：嵌入式大脚本的陷阱

### 错误模式识别
**日期**: 2025-11-21  
**上下文**: `/trading:trade-analysis` 命令执行  
**错误**: 使用巨大的内联Python脚本而非模块化技能调用

#### 具体错误表现
```python
# ❌ 错误做法：我刚才的实际代码
python_script = f'''
import sys
sys.path.append('/home/adt/project/agentic_trading')
from datetime import datetime
import json

# 大段的内联Python代码（超过100行）
complex_analysis = {{ ... }}
nested_logic = {{ ... }}

print(json.dumps(result, indent=2))
'''

bash(f'python3 -c "{python_script}"')
```

**问题症状**:
- f-string语法错误（未闭合的引号和括号）
- 字符串转义地狱
- 调试困难，错误信息模糊
- 代码维护性极差

### 正确做法
```python
# ✅ 正确做法：使用模块化技能
health = run_market_health_check()
if health.get('market_open') and health.get('data_quality') != 'CRITICAL':
    return run_full_trading_analysis()
else:
    return {"status": "skipped", "reason": "market_closed_or_data_issues"}
```

## 核心架构原则（必须遵守）

### 1. 绝不使用嵌入式大脚本
- 🚫 **红线**: 任何超过50行的内联代码都是错误的
- 🚫 **禁止**: `bash(f'python3 -c "{huge_script}"')`
- ✅ **应该**: 调用封装好的技能函数

### 2. 使用技能层抽象
- 🚫 **禁止**: 直接调用MCP工具或编写复杂逻辑
- ✅ **应该**: 使用设计文档中预定义的技能
- 📋 **技能清单**: `run_market_health_check()`, `run_full_trading_analysis()`, `run_position_risk_analysis()`, `place_order_with_guard()`

### 3. 数据流单向性
```
数据采集 → 技能处理 → 结果输出
```
- 避免复杂的字符串拼接
- 每个步骤有明确的输入输出接口

## 强制检查清单

### 编码前的自我审查问题
在编写任何代码前，必须回答：

1. **架构检查**
   - ☐ 我是否在使用设计文档中预定义的技能函数？
   - ☐ 这个任务是否可以通过组合现有技能完成？
   - ☐ 我是否试图重新实现已有的功能？

2. **实现方式检查**
   - ☐ 我的代码是否会产生超过100行的字符串？
   - ☐ 我是否使用了复杂的f-string嵌套？
   - ☐ 是否有更简单的模块化方法？

3. **稳定性检查**
   - ☐ 这个代码是否容易产生语法错误？
   - ☐ 如果出现错误，我能否快速定位问题？
   - ☐ 这种方式是否便于测试和调试？

### 错误模式识别和立即停止信号

| 错误模式 | 触发条件 | 立即停止信号 |
|---------|----------|-------------|
| **字符串拼接地狱** | 代码中出现多层f-string嵌套 | `f'{f"..."}'` |
| **大脚本综合症** | bash命令中包含超过50行Python | `python3 -c "巨量代码"` |
| **重新发明轮子** | 直接调用MCP工具而非技能 | `mcp__ibkr__*` 直接调用 |
| **复杂内联逻辑** | 在字符串中编写条件循环 | 复杂的`if-else`嵌套在f-string中 |

## 标准执行模板

### 正确的思维模式
遇到任务时，按以下顺序思考：

1. **第一层：是否存在预定义技能？**
   - 查看 `prompts/commander_system.md` 中的技能清单
   - 检查是否有直接的解决方案

2. **第二层：能否组合现有技能？**
   - 将任务分解为子步骤
   - 每个步骤对应一个技能函数

3. **第三层：是否需要新技能？**
   - 如果需要，先定义技能接口
   - 实现技能，然后使用技能

4. **第四层：拒绝直接实现**
   - 绝不在使用层直接实现复杂逻辑
   - 保持抽象层的完整性

### 标准模板
```python
# 模式1：简单任务
def simple_task():
    result = skill_function()
    return result

# 模式2：组合任务
def complex_task():
    health = run_market_health_check()
    if health['market_open']:
        analysis = run_full_trading_analysis()
        return analysis
    else:
        return {"status": "market_closed"}

# 模式3：错误处理
def robust_task():
    try:
        result = skill_function()
        if result.get('success'):
            return process_result(result)
        else:
            return handle_error(result)
    except Exception as e:
        return {"error": str(e)}
```

## 错误恢复协议

### 如果意识到犯了架构错误：
1. **立即停止**当前操作
2. **识别错误类型**（字符串拼接？重新发明轮子？）
3. **回到设计文档**查找正确的技能
4. **重构为模块化调用**
5. **记录错误模式**到学习笔记

### 相关文档位置
- **技能清单**: `prompts/commander_system.md` 第288-331行
- **命令文档**: `.claude/commands/trading/trade-analysis.md`
- **架构设计**: `openspec/specs/slash-command-integration/`

## 心理提醒机制

### 触发条件
当遇到以下情况时，必须提醒自己这个教训：
- 任务看起来"复杂，需要一次性处理"
- 试图编写超过20行的内联代码
- 想要绕过现有技能直接实现
- 遇到字符串处理和转义问题

### 正确反应
1. **停止当前实现**
2. **重读技能清单**
3. **分解任务为小步骤**
4. **使用组合式调用**

## 学习要点

1. **复杂度陷阱**: 试图一次性解决所有问题往往导致更复杂的实现
2. **抽象的价值**: 技能层抽象不是为了限制，而是为了稳定性
3. **模块化的力量**: 简单的模块化调用比复杂的单体实现更可靠
4. **文档的重要性**: 设计文档中已经定义了解决方案，不需要重新发明

---

**教训总结**: 系统设计中的技能层抽象是经过深思熟虑的架构决策，绕过这些抽象层看似"快速"，实际上会导致稳定性、维护性和调试的噩梦。永远使用预定义的技能组合，而不是重新实现现有功能。

**关键原则**: 简单、模块化、可预测。