"""
策略工厂模块

提供自然语言策略创建功能，包括概念提取、模板生成和参数建议。
"""

import re
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path


class TradingConceptExtractor:
    """交易概念提取器"""

    def __init__(self):
        """初始化概念提取器"""
        # 技术分析概念字典
        self.technical_concepts = {
            '缠论': ['笔', '线段', '中枢', '背驰', '分型', '顶底', '买卖点'],
            '均线': ['MA', 'EMA', '均线交叉', '金叉', '死叉', '均线支撑', '均线阻力'],
            'MACD': ['DIF', 'DEA', 'MACD柱', '金叉', '死叉', '背离', '零轴'],
            'RSI': ['超买', '超卖', '背离', '多空', '强弱指标'],
            '布林带': ['上轨', '下轨', '中轨', '突破', '回归', '宽度'],
            'K线': ['K线形态', '实体', '影线', '十字星', '锤头线', '黄昏星'],
            '成交量': ['放量', '缩量', '量价关系', '量能'],
            'ATR': ['真实波幅', '波动率', '止损']
        }

        # 策略类型字典
        self.strategy_types = {
            '趋势跟踪': ['趋势', '跟踪', '跟随', '趋势线', '通道'],
            '均值回归': ['均值', '回归', '反转', '震荡', '区间'],
            '突破': ['突破', '破位', '新高', '新低', '区间突破'],
            '波动率': ['波动率', 'IV', '隐含波动', '历史波动', '权利金'],
            '套利': ['套利', '价差', '配对', '相关性', '收敛'],
            '期权': ['期权', '看涨', '看跌', '认购', '认沽', '行权价', '到期日']
        }

        # 市场环境概念
        self.market_environments = {
            '上涨': ['上涨', '上升', '牛市', '多头', '上涨趋势'],
            '下跌': ['下跌', '下降', '熊市', '空头', '下跌趋势'],
            '震荡': ['震荡', '横盘', '整理', '区间', '平衡'],
            '高波动': ['高波动', '大涨大跌', '剧烈波动', 'VIX高'],
            '低波动': ['低波动', '平稳', '温和波动', 'VIX低']
        }

    def extract_concepts(self, description: str) -> Dict[str, List[str]]:
        """
        从描述中提取交易概念

        Args:
            description: 策略描述文本

        Returns:
            提取的概念字典
        """
        concepts = {
            'technical': [],
            'strategy': [],
            'environment': [],
            'symbols': [],
            'timeframe': []
        }

        # 技术分析概念提取
        for concept_type, keywords in self.technical_concepts.items():
            if any(keyword in description for keyword in keywords):
                concepts['technical'].append(concept_type)
                concepts['technical'].extend([kw for kw in keywords if kw in description])

        # 策略类型提取
        for strategy_type, keywords in self.strategy_types.items():
            if any(keyword in description for keyword in keywords):
                concepts['strategy'].append(strategy_type)

        # 市场环境提取
        for env_type, keywords in self.market_environments.items():
            if any(keyword in description for keyword in keywords):
                concepts['environment'].append(env_type)

        # 标的和板块提取
        symbol_patterns = [
            r'[A-Z]{2,5}',  # 股票代码
            '科技股', '大盘股', '小盘股',
            'TSLA', 'AAPL', 'NVDA', 'AMD', 'MSFT', 'GOOGL',
            'SPY', 'QQQ', 'IWM', 'DIA'
        ]

        for pattern in symbol_patterns:
            if pattern in description:
                concepts['symbols'].append(pattern)

        # 时间周期提取
        time_patterns = [
            (r'(\d+)天', 'days'),
            (r'(\d+)周', 'weeks'),
            (r'(\d+)月', 'months'),
            (r'(\d+)分钟', 'minutes'),
            (r'(\d+)小时', 'hours')
        ]

        for pattern, unit in time_patterns:
            matches = re.findall(pattern, description)
            if matches:
                for match in matches:
                    concepts['timeframe'].append(f"{match}{unit}")

        return concepts


class TemplateGenerator:
    """策略模板生成器"""

    def __init__(self):
        """初始化模板生成器"""
        self.template_base = """# {strategy_name}

{strategy_description}

## 策略参数

{parameters_section}

## 策略逻辑

### 1. 技术分析框架
{technical_analysis_section}

### 2. 信号生成逻辑
{signal_generation_section}

### 3. 风险控制
{risk_control_section}

## 执行指令

```python
from skills import (
    get_multi_timeframe_data,
    {skill_imports}
    # 更多技能导入...
)

# 获取市场数据
data = get_multi_timeframe_data(
    symbols={parameters['symbol_pool'] | tojson},
    intervals=["daily"],
    lookback_days={parameters.get('lookback_days', 30)}
)

# 应用策略分析
{strategy_analysis_code}

# 生成交易信号
signals = generate_trading_signals(
    analysis_result=analysis,
    min_confidence={parameters.get('min_confidence', 0.75)}
)

return signals
```

## 输出格式

返回标准的交易信号格式：
```json
{{
  "signal": "SHORT_PUT_SPREAD|SHORT_CALL_SPREAD|IRON_CONDOR|NO_TRADE",
  "target": "SYMBOL",
  "confidence": 0.80,
  "reasoning": "详细分析理由...",
  "params": {{
    "legs": [...],
    "max_risk": 400,
    "capital_required": 500
  }}
}}
```

## 市场数据

当前市场数据快照：
```json
{{{{ market_data|tojson(indent=2) }}}}
```
"""

    def generate_template(self, strategy_name: str, description: str,
                         concepts: Dict[str, List[str]], parameters: Dict) -> str:
        """
        生成策略模板

        Args:
            strategy_name: 策略名称
            description: 策略描述
            concepts: 提取的概念
            parameters: 建议的参数

        Returns:
            完整的策略模板内容
        """
        # 生成参数说明部分
        parameters_section = self._generate_parameters_section(parameters)

        # 生成技术分析部分
        technical_analysis_section = self._generate_technical_section(concepts)

        # 生成信号生成部分
        signal_generation_section = self._generate_signal_section(concepts)

        # 生成风险控制部分
        risk_control_section = self._generate_risk_section(concepts)

        # 生成技能导入
        skill_imports = self._generate_skill_imports(concepts)

        # 生成策略分析代码
        strategy_analysis_code = self._generate_analysis_code(concepts)

        return self.template_base.format(
            strategy_name=strategy_name,
            strategy_description=description,
            parameters_section=parameters_section,
            technical_analysis_section=technical_analysis_section,
            signal_generation_section=signal_generation_section,
            risk_control_section=risk_control_section,
            skill_imports=skill_imports,
            strategy_analysis_code=strategy_analysis_code,
            parameters=parameters
        )

    def _generate_parameters_section(self, parameters: Dict) -> str:
        """生成参数说明部分"""
        section_lines = ["- **{name}**: {value}".format(
            name=k.replace('_', ' ').title(),
            value=v if isinstance(v, (list, tuple)) else str(v)
        ) for k, v in parameters.items()]

        return '\n'.join(section_lines)

    def _generate_technical_section(self, concepts: Dict[str, List[str]]) -> str:
        """生成技术分析部分"""
        sections = []

        if '缠论' in concepts.get('technical', []):
            sections.append(self._generate_chanlun_analysis())
        if 'MACD' in concepts.get('technical', []):
            sections.append(self._generate_macd_analysis())
        if 'RSI' in concepts.get('technical', []):
            sections.append(self._generate_rsi_analysis())

        return '\n\n'.join(sections) if sections else "基于技术指标进行分析..."

    def _generate_chanlun_analysis(self) -> str:
        """生成缠论分析部分"""
        return """
#### 缠论分析
```python
from skills import (
    identify_chanlun_fractals,
    build_pen_segments,
    identify_zhongshu,
    detect_breakouts
)

# 识别顶底分型
fractals = identify_chanlun_fractals(bars=daily_bars)

# 构建笔段
pens = build_pen_segments(fractals, min_bars=5)

# 识别中枢
zhongshu = identify_zhongshu(pens)

# 检测突破
breakout_signals = detect_breakouts(pens, zhongshu)
```

- **分型识别**: 识别K线顶底分型结构
- **笔段构建**: 连接有效分型形成笔段
- **中枢分析**: 识别价格震荡中枢区间
- **突破检测**: 判断是否有效突破中枢边界"""

    def _generate_macd_analysis(self) -> str:
        """生成MACD分析部分"""
        return """
#### MACD指标确认
```python
from skills import calculate_macd

# 计算MACD指标
macd_result = calculate_macd(daily_bars, fast=12, slow=26, signal=9)

# 获取MACD信号
dif_line = macd_result['dif']
dea_line = macd_result['dea']
macd_histogram = macd_result['histogram']

# 检测金叉死叉
golden_cross = detect_macd_golden_cross(dif_line, dea_line)
death_cross = detect_macd_death_cross(dif_line, dea_line)
```

- **趋势确认**: 使用MACD金叉死叉确认趋势方向
- **背离检测**: 价格与MACD的背离信号
- **动量分析**: MACD柱状图的变化趋势
- **交叉信号**: DIF与DEA线的交叉买卖信号"""

    def _generate_rsi_analysis(self) -> str:
        """生成RSI分析部分"""
        return """
#### RSI超买超卖分析
```python
from skills import calculate_rsi

# 计算RSI指标
rsi_values = calculate_rsi(daily_bars, period=14)
current_rsi = rsi_values[-1]

# 超买超卖判断
overbought = current_rsi > 70
oversold = current_rsi < 30
```

- **超买区域**: RSI > 70，考虑卖出机会
- **超卖区域**: RSI < 30，考虑买入机会
- **背离信号**: 价格新高但RSI未新高（顶背离）
- **中性区域**: RSI 30-70，趋势延续概率高"""

    def _generate_signal_section(self, concepts: Dict[str, List[str]]) -> str:
        """生成信号生成部分"""
        return """
### 信号生成条件

#### 做多信号条件
- 技术分析确认上升趋势
- 多个指标给出积极信号
- 成交量放大确认
- 风险回报比合理

#### 做空信号条件
- 技术分析确认下降趋势
- 多个指标给出消极信号
- 成交量放大确认
- 风险回报比合理

#### 无信号条件
- 指标信号冲突
- 市场环境不确定
- 风险收益比不合理
- 数据质量问题"""

    def _generate_risk_section(self, concepts: Dict[str, List[str]]) -> str:
        """生成风险控制部分"""
        return """
### 风险控制机制

#### 仓位管理
- 单笔交易风险不超过总资金的2%
- 同时持仓不超过3个标的
- 集中度控制在30%以内

#### 止损设置
- 技术止损：跌破关键支撑位
- 时间止损：持仓超过15天无盈利
- 波动止损：异常波动自动平仓

#### 多元化原则
- 不同标的分散风险
- 不同策略类型互补
- 定期评估和调整"""

    def _generate_skill_imports(self, concepts: Dict[str, List[str]]) -> str:
        """生成技能导入"""
        imports = []

        # 基础技能
        imports.extend([
            'get_latest_price',
            'get_multi_timeframe_data'
        ])

        # 技术指标技能
        if 'MACD' in concepts.get('technical', []):
            imports.append('calculate_macd')
        if 'RSI' in concepts.get('technical', []):
            imports.append('calculate_rsi')
        if '布林带' in concepts.get('technical', []):
            imports.append('calculate_bollinger_bands')

        # 波动率技能
        if '波动率' in concepts.get('strategy', []):
            imports.extend([
                'calculate_historical_volatility',
                'calculate_implied_volatility'
            ])

        return ',\n    '.join(imports)

    def _generate_analysis_code(self, concepts: Dict[str, List[str]]) -> str:
        """生成策略分析代码"""
        return f"""
# 综合技术分析
analysis_result = {{}}

# 技术指标分析
{self._generate_indicator_analysis_code(concepts)}

# 市场背景分析
spy_data = get_multi_timeframe_data("SPY", intervals=["daily"], lookback_days=30)
market_trend = detect_trend(spy_data['timeframes']['daily']['bars'])

# 综合判断
if analysis_result['trend'] == 'UPWARD' and market_trend['direction'] == 'BULLISH':
    signals.append({{
        "signal": "SHORT_PUT_SPREAD",
        "confidence": calculate_confidence(analysis_result),
        "reasoning": "多重指标确认上升趋势"
    }})

return analysis_result"""

    def _generate_indicator_analysis_code(self, concepts: Dict[str, List[str]]) -> str:
        """生成指标分析代码"""
        code_parts = []

        if 'MACD' in concepts.get('technical', []):
            code_parts.append("""
# MACD分析
macd_result = calculate_macd(daily_bars)
analysis_result['macd_signal'] = 'BULLISH' if macd_result['dif'][-1] > macd_result['dea'][-1] else 'BEARISH'""")

        if 'RSI' in concepts.get('technical', []):
            code_parts.append("""
# RSI分析
rsi_result = calculate_rsi(daily_bars)
current_rsi = rsi_result[-1]
analysis_result['rsi_signal'] = 'OVERSOLD' if current_rsi < 30 else 'OVERBOUGHT' if current_rsi > 70 else 'NEUTRAL'""")

        return '\n'.join(code_parts) if code_parts else "# 基础技术分析"


class ParameterSuggester:
    """参数建议器"""

    def __init__(self):
        """初始化参数建议器"""
        self.base_parameters = {
            'lookback_days': {'default': 30, 'min': 5, 'max': 120, 'description': 'K线分析周期（天）'},
            'symbol_pool': {'default': ['SPY', 'QQQ', 'IWM'], 'description': '监控标的池'},
            'min_confidence': {'default': 0.75, 'min': 0.5, 'max': 0.95, 'description': '最低置信度要求'},
            'max_positions': {'default': 3, 'min': 1, 'max': 10, 'description': '最大同时持仓数'},
            'risk_per_trade': {'default': 0.02, 'min': 0.01, 'max': 0.05, 'description': '单笔交易风险比例'}
        }

        self.concept_specific_parameters = {
            '缠论': {
                'pen_threshold': {'default': 5, 'min': 3, 'max': 10, 'description': '笔的最小K线数'},
                'zhongshu_depth': {'default': 3, 'min': 2, 'max': 5, 'description': '中枢分析深度'},
                'breakout_threshold': {'default': 0.02, 'min': 0.01, 'max': 0.05, 'description': '突破确认阈值'}
            },
            'MACD': {
                'fast_period': {'default': 12, 'min': 5, 'max': 20, 'description': 'MACD快线周期'},
                'slow_period': {'default': 26, 'min': 15, 'max': 35, 'description': 'MACD慢线周期'},
                'signal_period': {'default': 9, 'min': 5, 'max': 15, 'description': 'MACD信号线周期'}
            },
            'RSI': {
                'period': {'default': 14, 'min': 7, 'max': 21, 'description': 'RSI计算周期'},
                'overbought': {'default': 70, 'min': 65, 'max': 80, 'description': 'RSI超买阈值'},
                'oversold': {'default': 30, 'min': 20, 'max': 35, 'description': 'RSI超卖阈值'}
            },
            '波动率': {
                'min_iv_rank': {'default': 50, 'min': 30, 'max': 90, 'description': '最小IV Rank要求'},
                'max_vega_exposure': {'default': 0.2, 'min': 0.1, 'max': 0.5, 'description': '最大Vega敞口'},
                'target_dte': {'default': 45, 'min': 7, 'max': 90, 'description': '目标到期天数'}
            }
        }

    def suggest_parameters(self, concepts: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        根据提取的概念建议参数

        Args:
            concepts: 提取的概念字典

        Returns:
            建议的参数字典
        """
        parameters = {}

        # 基础参数
        for key, value in self.base_parameters.items():
            parameters[key] = value['default']

        # 标的池建议
        symbols = concepts.get('symbols', [])
        if symbols:
            # 清理和标准化标的
            clean_symbols = []
            for symbol in symbols:
                if symbol.isupper() and 2 <= len(symbol) <= 5:
                    clean_symbols.append(symbol)
                elif '科技股' in symbol:
                    clean_symbols.extend(['AAPL', 'NVDA', 'AMD', 'MSFT', 'GOOGL'])
                elif '大盘股' in symbol:
                    clean_symbols.extend(['SPY', 'QQQ', 'IWM'])

            if clean_symbols:
                parameters['symbol_pool'] = list(set(clean_symbols))[:10]  # 最多10个

        # 概念特定参数
        for concept_type in concepts.get('technical', []):
            if concept_type in self.concept_specific_parameters:
                for key, value in self.concept_specific_parameters[concept_type].items():
                    parameters[key] = value['default']

        # 策略类型调整
        strategy_types = concepts.get('strategy', [])
        if '均值回归' in strategy_types:
            parameters['lookback_days'] = 20  # 均值回归用较短周期
        elif '趋势跟踪' in strategy_types:
            parameters['lookback_days'] = 60  # 趋势跟踪用较长周期

        # 市场环境调整
        environments = concepts.get('environment', [])
        if '高波动' in environments:
            parameters['min_confidence'] = 0.85  # 高波动环境下提高要求
        elif '低波动' in environments:
            parameters['min_confidence'] = 0.65  # 低波动环境下降低要求

        return parameters


class StrategyFactory:
    """策略工厂主类"""

    def __init__(self):
        """初始化策略工厂"""
        self.concept_extractor = TradingConceptExtractor()
        self.template_generator = TemplateGenerator()
        self.parameter_suggester = ParameterSuggester()

        # 确保目录存在
        os.makedirs('swarm_intelligence/templates', exist_ok=True)
        os.makedirs('swarm_intelligence/active_instances', exist_ok=True)

    def create_strategy_from_description(self, description: str,
                                        sector: str = "GENERAL",
                                        strategy_name: str = None) -> Dict[str, Any]:
        """
        从自然语言描述创建策略

        Args:
            description: 策略描述
            sector: 策略所属板块
            strategy_name: 策略名称

        Returns:
            创建结果字典
        """
        try:
            # 1. 概念提取
            concepts = self.concept_extractor.extract_concepts(description)

            # 2. 参数建议
            parameters = self.parameter_suggester.suggest_parameters(concepts)
            parameters['sector'] = sector

            # 3. 策略名称
            if not strategy_name:
                strategy_name = self._generate_strategy_name(concepts, description)

            # 4. 生成模板
            template_content = self.template_generator.generate_template(
                strategy_name, description, concepts, parameters
            )

            # 5. 创建配置
            config = {
                "id": strategy_name.lower().replace(' ', '_'),
                "sector": sector,
                "template": f"{strategy_name.lower().replace(' ', '_')}.md",
                "parameters": parameters,
                "evolution_history": {
                    "generation": 1,
                    "created": datetime.now().strftime("%Y-%m-%d"),
                    "last_mutated": None
                }
            }

            # 6. 保存文件
            template_path = f"swarm_intelligence/templates/{config['template']}"
            config_path = f"swarm_intelligence/active_instances/{config['id']}.json"

            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(template_content)

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            return {
                "status": "success",
                "strategy_name": strategy_name,
                "files_created": [template_path, config_path],
                "concepts": concepts,
                "parameters": parameters,
                "summary": self._generate_creation_summary(concepts, parameters)
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "策略创建失败，请检查描述或参数"
            }

    def _generate_strategy_name(self, concepts: Dict[str, List[str]], description: str) -> str:
        """生成策略名称"""
        # 尝试从描述中提取关键信息
        name_parts = []

        # 策略类型
        if '趋势跟踪' in concepts.get('strategy', []):
            name_parts.append("趋势跟踪")
        elif '均值回归' in concepts.get('strategy', []):
            name_parts.append("均值回归")
        elif '突破' in concepts.get('strategy', []):
            name_parts.append("突破")
        elif '波动率' in concepts.get('strategy', []):
            name_parts.append("波动率")

        # 技术分析类型
        if '缠论' in concepts.get('technical', []):
            name_parts.append("缠论")
        elif 'MACD' in concepts.get('technical', []):
            name_parts.append("MACD")
        elif 'RSI' in concepts.get('technical', []):
            name_parts.append("RSI")

        # 市场环境
        if '科技股' in description:
            name_parts.append("科技")
        elif '大盘股' in description:
            name_parts.append("大盘")

        # 如果没有提取到关键信息，使用时间戳
        if not name_parts:
            timestamp = datetime.now().strftime("%m%d")
            return f"策略_{timestamp}"

        return "_".join(name_parts[:3])  # 最多3个关键词

    def _generate_creation_summary(self, concepts: Dict[str, List[str]],
                                 parameters: Dict) -> Dict[str, Any]:
        """生成创建摘要"""
        return {
            "strategy_type": "技术分析策略" if concepts.get('technical') else "其他策略",
            "complexity": self._assess_complexity(concepts, parameters),
            "estimated_signals_per_run": "1-3",
            "target_sectors": [parameters.get('sector', 'GENERAL')],
            "technical_concepts": concepts.get('technical', []),
            "strategy_types": concepts.get('strategy', [])
        }

    def _assess_complexity(self, concepts: Dict[str, List[str]], parameters: Dict) -> str:
        """评估策略复杂度"""
        complexity_score = 0

        # 技术概念数量
        complexity_score += len(concepts.get('technical', [])) * 2

        # 参数数量
        complexity_score += len([k for k in parameters.keys() if not k.startswith('_')])

        # 特殊概念加分
        special_concepts = ['缠论', '套利', '对角价差']
        for concept in special_concepts:
            if concept in concepts.get('technical', []):
                complexity_score += 5

        if complexity_score < 10:
            return "简单"
        elif complexity_score < 20:
            return "中等"
        else:
            return "复杂"


def get_strategy_factory() -> StrategyFactory:
    """获取策略工厂实例"""
    return StrategyFactory()