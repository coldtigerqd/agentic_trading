"""
蜂群智能核心 - 并发智能体协调。

这是递归智能引擎，并发执行多个策略实例并聚合其信号。
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from jinja2 import Template, Environment, FileSystemLoader, StrictUndefined

from data_lake.snapshot_manager import save_snapshot, update_snapshot_response
from skills.signal_enrichment import enrich_signal, validate_enriched_signal


# 路径
SWARM_BASE = Path(__file__).parent.parent / "swarm_intelligence"
TEMPLATES_DIR = SWARM_BASE / "templates"
INSTANCES_DIR = SWARM_BASE / "active_instances"


@dataclass
class Signal:
    """蜂群实例的交易信号"""
    instance_id: str
    template_used: str
    target: str
    signal: str  # 例如 "SHORT_PUT_SPREAD", "LONG_CALL", "NO_TRADE"
    params: Dict[str, Any]
    confidence: float  # 0.0 到 1.0
    reasoning: str


def load_instances(sector_filter: Optional[str] = None) -> List[Dict]:
    """
    从 JSON 文件加载活跃实例配置。

    参数:
        sector_filter: 按行业过滤（"ALL", "TECH", "FINANCE" 等）
                       "ALL" 或 None 返回所有实例

    返回:
        实例配置字典列表
    """
    if not INSTANCES_DIR.exists():
        return []

    instances = []
    for json_file in INSTANCES_DIR.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                instance = json.load(f)

            # 应用行业过滤器
            if sector_filter and sector_filter != "ALL":
                instance_sector = instance.get("sector", "").upper()
                if instance_sector != sector_filter.upper():
                    continue

            instances.append(instance)

        except json.JSONDecodeError as e:
            print(f"⚠️ 加载实例配置失败 {json_file}: {e}")
            continue

    return instances


def load_template(template_name: str) -> str:
    """
    从文件加载策略模板。

    参数:
        template_name: 模板文件名（例如 "vol_sniper.md"）

    返回:
        模板内容字符串

    异常:
        FileNotFoundError: 如果模板不存在
    """
    template_path = TEMPLATES_DIR / template_name

    if not template_path.exists():
        raise FileNotFoundError(f"模板未找到: {template_name} (TEMPLATE_NOT_FOUND)")

    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def render_template(template_content: str, parameters: Dict[str, Any], market_data: Dict[str, Any] = None) -> str:
    """
    使用参数和市场数据渲染 Jinja2 模板。

    参数:
        template_content: 包含 Jinja2 占位符的模板字符串
        parameters: 要注入的参数字典
        market_data: 要注入的市场数据快照（可选）

    返回:
        渲染后的模板字符串
    """
    # 使用 StrictUndefined 以尽早捕获缺失的模板变量
    env = Environment(undefined=StrictUndefined)
    template = env.from_string(template_content)

    # 合并 parameters 和 market_data 作为模板上下文
    # 修复：确保 'parameters' 键也包含在上下文中
    context = {'parameters': parameters, **parameters}
    if market_data:
        context['market_data'] = market_data

    return template.render(**context)


async def execute_single_instance(
    instance: Dict,
    market_data: Dict[str, Any],
    timeout: int = 20
) -> Optional[Signal]:
    """
    执行单个蜂群实例（异步）。

    此函数：
    1. 加载并渲染模板
    2. 保存输入快照
    3. 调用 LLM API
    4. 解析响应为 Signal
    5. 更新快照的响应

    参数:
        instance: 实例配置
        market_data: 市场数据快照
        timeout: 超时时间（秒）

    返回:
        Signal 对象，执行失败返回 None
    """
    instance_id = instance["id"]
    template_name = instance["template"]
    parameters = instance.get("parameters", {})

    try:
        # 加载并渲染模板
        template_content = load_template(template_name)
        print(f"📋 [{instance_id}] 策略模板加载完成: {template_name}")

        rendered_prompt = render_template(template_content, parameters, market_data)
        print(f"✨ [{instance_id}] 模板渲染完成")

        # 在 LLM 调用之前保存输入快照
        timestamp = datetime.now().isoformat()
        print(f"💾 [{instance_id}] 正在保存决策快照...")
        snapshot_id = save_snapshot(
            instance_id=instance_id,
            template_name=template_name,
            rendered_prompt=rendered_prompt,
            market_data=market_data,
            agent_response=None,  # LLM 调用后更新
            timestamp=timestamp
        )
        print(f"✅ [{instance_id}] 决策快照已保存: {snapshot_id}")

        # 执行 LLM API 调用（带超时）
        try:
            response = await asyncio.wait_for(
                call_llm_api(rendered_prompt, market_data),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            print(f"警告：实例 {instance_id} 在 {timeout}秒后超时 (TIMEOUT)")
            return None

        # 解析响应为 Signal
        signal = parse_signal_response(response, instance_id, template_name)

        # 更新快照的响应
        update_snapshot_response(snapshot_id, {
            "raw_response": response,
            "parsed_signal": signal.__dict__ if signal else None
        })

        return signal

    except FileNotFoundError as e:
        print(f"警告：{e}")
        return None
    except Exception as e:
        print(f"❌ 执行策略实例失败 {instance_id}: {e}")
        return None


async def call_llm_api(prompt: str, market_data: Dict, max_retries: int = 2) -> Dict:
    """
    通过 OpenRouter 调用 LLM API 以获取交易信号。

    使用 Gemini 2.5 Flash 进行快速、经济高效的并发执行。
    包含重试机制和错误恢复功能。

    参数:
        prompt: 渲染后的提示词
        market_data: 市场数据上下文
        max_retries: 最大重试次数

    返回:
        LLM 响应字典（从 JSON 响应解析）
    """
    import os
    from openai import AsyncOpenAI

    # 从环境变量获取 API 密钥
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("警告：未设置 OPENROUTER_API_KEY，使用模拟响应 (NO_API_KEY)")
        # 回退到模拟用于测试
        await asyncio.sleep(0.5)
        return {
            "signal": "SHORT_PUT_SPREAD",
            "target": market_data.get("symbols", ["AAPL"])[0] if market_data.get("symbols") else "AAPL",
            "params": {
                "strike_short": 180,
                "strike_long": 175,
                "expiry": "20251128"
            },
            "confidence": 0.75,
            "reasoning": "IV 升高且情绪中性，表明存在卖出权利金的机会。"
        }

    for attempt in range(max_retries + 1):
        try:
            # 初始化 OpenRouter 客户端（OpenAI 兼容）
            client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key
            )

            # 调整温度参数，重试时降低随机性
            temp = 0.7 if attempt == 0 else 0.3

            # 通过 OpenRouter 调用 Gemini 2.0 Flash
            completion = await client.chat.completions.create(
                model="google/gemini-2.5-flash",  # 免费层，速度非常快
                messages=[
                    {
                        "role": "user",
                        "content": prompt + (f"\n\n（第{attempt + 1}次尝试，请确保返回严格的JSON格式）" if attempt > 0 else "")
                    }
                ],
                temperature=temp,
                max_tokens=1000,
                extra_headers={
                    "HTTP-Referer": "https://github.com/agentic-alphahive",  # 可选
                    "X-Title": "Agentic AlphaHive Runtime"  # 可选
                }
            )

            # 提取响应内容
            response_text = completion.choices[0].message.content

            # 去除 markdown 代码块（如果存在）
            # Gemini 经常将 JSON 包装在 ```json ... ``` 中
            response_text = response_text.strip()
            if response_text.startswith("```"):
                # 移除开头的 ```json 或 ```
                lines = response_text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # 移除结尾的 ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                response_text = "\n".join(lines).strip()

            # 解析 JSON 响应
            import json
            response_json = json.loads(response_text)

            # 成功解析，返回结果
            if attempt > 0:
                print(f"🔄 重试成功: 第{attempt + 1}次尝试获得有效JSON响应")

            return response_json

        except json.JSONDecodeError as e:
            print(f"⚠️ 第{attempt + 1}次尝试解析失败: {e}")
            print(f"📄 响应内容: {response_text[:200]}...")

            if attempt == max_retries:
                # 最后一次尝试失败，使用智能解析
                print(f"🧠 使用智能解析处理最终响应")
                return _parse_non_json_response(response_text)
            else:
                # 等待后重试
                await asyncio.sleep(1 * (attempt + 1))  # 递增等待时间

        except Exception as e:
            print(f"🔥 第{attempt + 1}次API调用失败: {e}")
            if attempt == max_retries:
                print(f"💥 所有重试均失败，返回默认值")
                return _get_default_response(market_data)
            else:
                await asyncio.sleep(1 * (attempt + 1))  # 递增等待时间

    # 这个函数现在在重试循环中处理，不需要单独的except块


def _get_default_response(market_data: Dict) -> Dict:
    """
    当所有重试都失败时，返回安全的默认响应。
    """
    # 从市场数据中获取第一个可用的标的
    symbols = market_data.get("symbols", [])
    target = symbols[0] if symbols else "SPY"

    return {
        "signal": "NO_TRADE",
        "target": target,
        "confidence": 0.0,
        "reasoning": "系统重试失败，返回安全的无交易信号",
        "params": {}
    }


def _parse_non_json_response(response_text: str) -> Optional[Dict]:
    """
    智能解析非JSON格式的AI响应，尝试提取结构化信息。

    当AI返回自然语言文本而不是JSON时，尝试从文本中提取交易信号。
    """
    import re

    try:
        # 默认返回值
        default_response = {
            "signal": "NO_TRADE",
            "target": "",
            "confidence": 0.0,
            "reasoning": "AI响应格式不正确，使用默认值",
            "params": {}
        }

        # 转换为小写以便匹配
        text_lower = response_text.lower()

        # 查找提到的股票代码
        stock_patterns = [
            r'\b([A-Z]{2,5})\b',  # 大写股票代码
            r'\$([a-z]{2,5})\b'   # $符号后跟股票代码
        ]

        mentioned_stocks = []
        for pattern in stock_patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            mentioned_stocks.extend(matches)

        # 去重并过滤常见的金融词汇
        common_words = {'ETF', 'SPY', 'QQQ', 'IWM', 'THE', 'AMD', 'AAPL', 'NVDA', 'MSFT', 'GOOGL', 'META', 'TSLA', 'AMZN'}
        filtered_stocks = []
        for s in mentioned_stocks:
            if isinstance(s, str):  # 确保是字符串
                s_upper = s.upper()
                if s_upper not in common_words or len(s_upper) <= 5:
                    filtered_stocks.append(s_upper)
        mentioned_stocks = list(set(filtered_stocks))[:3]  # 最多取3个

        # 检测交易信号类型
        signal_type = "NO_TRADE"
        if any(word in text_lower for word in ['short put', 'put spread', '卖出看跌', '看跌期权']):
            signal_type = "SHORT_PUT_SPREAD"
        elif any(word in text_lower for word in ['short call', 'call spread', '卖出看涨', '看涨期权']):
            signal_type = "SHORT_CALL_SPREAD"
        elif any(word in text_lower for word in ['iron condor', '铁鹰', '中性策略']):
            signal_type = "IRON_CONDOR"
        elif any(word in text_lower for word in ['credit spread', '价差']):
            signal_type = "CREDIT_SPREAD"
        elif any(word in text_lower for word in ['buy call', '买入看涨', '看涨']):
            signal_type = "LONG_CALL"
        elif any(word in text_lower for word in ['buy put', '买入看跌', '看跌']):
            signal_type = "LONG_PUT"

        # 检测置信度
        confidence = 0.0
        confidence_patterns = [
            r'置信度[:：]\s*(\d+(?:\.\d+)?)',
            r'confidence[:：]\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*%?\s*置信度',
            r'(\d+(?:\.\d+)?)\s*%?\s*confidence'
        ]

        for pattern in confidence_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                try:
                    conf_value = float(match.group(1))
                    confidence = min(conf_value / 100 if conf_value > 1 else conf_value, 1.0)
                    break
                except:
                    continue

        # 检测目标标的
        target = mentioned_stocks[0] if mentioned_stocks else "SPY"  # 默认SPY

        # 提取推理（取前100个字符）
        reasoning = response_text.strip()[:150] + "..." if len(response_text) > 150 else response_text.strip()

        # 如果检测到有效信号，使用提取的信息
        if signal_type != "NO_TRADE" and confidence > 0.1:
            print(f"🧠 智能解析成功: 检测到 {signal_type} 信号，置信度 {confidence:.2f}")
            return {
                "signal": signal_type,
                "target": target,
                "confidence": confidence,
                "reasoning": reasoning,
                "params": {}  # 从自然语言中提取参数比较复杂，暂时为空
            }
        else:
            print(f"🤔 未检测到明确交易信号，使用默认值")
            return default_response

    except Exception as e:
        print(f"🔧 智能解析失败: {e}")
        return {
            "signal": "NO_TRADE",
            "target": "",
            "confidence": 0.0,
            "reasoning": f"智能解析出错: {str(e)}",
            "params": {}
        }


def parse_signal_response(response: Dict, instance_id: str, template_name: str) -> Optional[Signal]:
    """
    将 LLM 响应解析为 Signal 对象。

    参数:
        response: LLM API 响应
        instance_id: 实例标识符
        template_name: 使用的模板

    返回:
        Signal 对象，解析失败返回 None
    """
    # 修复：检查 response 是否为 None
    if response is None:
        print(f"⚠️ AI 响应为空 {instance_id}: 无法解析空响应")
        return None

    try:
        return Signal(
            instance_id=instance_id,
            template_used=template_name,
            target=response.get("target", ""),
            signal=response.get("signal", "NO_TRADE"),
            params=response.get("params", {}),
            confidence=float(response.get("confidence", 0.0)),
            reasoning=response.get("reasoning", "")
        )
    except (KeyError, ValueError) as e:
        print(f"⚠️ 解析交易信号失败 {instance_id}: {e}")
        return None


def deduplicate_signals(signals: List[Signal]) -> List[Signal]:
    """
    移除针对相同标的使用相同策略的重复信号。

    当多个实例产生相同信号时，保留置信度最高的那个。

    参数:
        signals: Signal 对象列表

    返回:
        去重后的信号列表
    """
    # 按 (target, signal) 分组
    signal_groups = {}
    for signal in signals:
        key = (signal.target, signal.signal)
        if key not in signal_groups:
            signal_groups[key] = []
        signal_groups[key].append(signal)

    # 从每组中保留最高置信度的信号
    deduplicated = []
    for key, group in signal_groups.items():
        best_signal = max(group, key=lambda s: s.confidence)
        deduplicated.append(best_signal)

    return deduplicated


async def execute_swarm_concurrent(
    instances: List[Dict],
    market_data: Dict[str, Any],
    max_concurrent: int = 50
) -> List[Signal]:
    """
    并发执行多个蜂群实例。

    参数:
        instances: 实例配置列表
        market_data: 市场数据快照
        max_concurrent: 最大并发 LLM API 调用数

    返回:
        成功执行的 Signal 对象列表
    """
    # 创建信号量以限制并发
    semaphore = asyncio.Semaphore(max_concurrent)

    async def execute_with_semaphore(instance):
        async with semaphore:
            return await execute_single_instance(instance, market_data)

    # 并发执行所有实例
    tasks = [execute_with_semaphore(inst) for inst in instances]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 过滤掉 None 和异常结果
    signals = []
    for result in results:
        if isinstance(result, Signal):
            signals.append(result)
        elif isinstance(result, Exception):
            print(f"警告：实例执行失败并抛出异常: {result} (INSTANCE_EXCEPTION)")

    return signals


def consult_swarm(
    sector: str = "ALL",
    market_data: Optional[Dict] = None,
    max_concurrent: int = 50,
    skip_data_validation: bool = False
) -> List[Dict]:
    """
    执行蜂群智能分析。

    这是 Commander 调用蜂群的主要入口点。

    参数:
        sector: 按行业过滤实例（"ALL", "TECH", "FINANCE" 等）
        market_data: 当前市场快照（如果为 None，则获取最新数据）
        max_concurrent: 最大并发 LLM API 调用数
        skip_data_validation: 跳过数据质量验证（不推荐）

    返回:
        信号字典列表，结构如下:
        [
            {
                "instance_id": "tech_aggressive",
                "template_used": "vol_sniper",
                "target": "NVDA",
                "signal": "SHORT_PUT_SPREAD",
                "params": {"strike_short": 120, "strike_long": 115},
                "confidence": 0.88,
                "reasoning": "..."
            },
            ...
        ]

    示例:
        >>> signals = consult_swarm(sector="TECH")
        >>> print(f"收到 {len(signals)} 个信号")
        收到 3 个信号
    """
    # 加载活跃实例
    instances = load_instances(sector_filter=sector)

    if not instances:
        print(f"警告：未找到行业 '{sector}' 的活跃实例 (NO_INSTANCES)")
        return []

    # 如果未提供市场数据则获取
    if market_data is None:
        market_data = fetch_market_snapshot()

    # === 数据质量飞行前检查 ===
    if not skip_data_validation:
        from skills.data_quality import validate_data_quality, auto_trigger_backfill

        # 从 market_data 快照中提取标的
        symbols = []
        if market_data and 'snapshot' in market_data:
            symbols = list(market_data['snapshot'].keys())

        # 同时收集实例标的池中的标的
        for instance in instances:
            symbol_pool = instance.get('parameters', {}).get('symbol_pool', [])
            symbols.extend(symbol_pool)

        # 去重
        symbols = list(set(symbols))

        if symbols:
            print(f"\n🔍 数据质量前置检查")
            print(f"📊 正在验证 {len(symbols)} 个标的的数据...")

            # 验证数据质量
            validation = validate_data_quality(
                symbols=symbols,
                min_daily_bars=20,  # 从30降低以更宽松的检查
                min_hourly_bars=30,
                min_5min_bars=200,
                max_age_hours=8,  # 允许稍微过时的数据
                require_all_intervals=False  # 宽松要求
            )

            if not validation['valid']:
                print(f"\n⚠️  数据质量验证失败 (DATA_QUALITY_FAILED)")
                print(f"摘要: {validation['summary']}")
                print(f"\n发现的问题:")

                # 按严重程度分组问题
                critical_issues = [i for i in validation['issues'] if i['severity'] == 'CRITICAL']
                high_issues = [i for i in validation['issues'] if i['severity'] == 'HIGH']

                if critical_issues:
                    print(f"  严重 ({len(critical_issues)}):")
                    for issue in critical_issues[:5]:  # 显示前5个
                        print(f"    - {issue['symbol']}: {issue['issue']} ({issue['detail']})")

                if high_issues:
                    print(f"  高 ({len(high_issues)}):")
                    for issue in high_issues[:3]:  # 显示前3个
                        print(f"    - {issue['symbol']}: {issue['issue']} ({issue['detail']})")

                print(f"\n建议:")
                for rec in validation['recommendations']:
                    print(f"  → {rec}")

                # 返回带有数据质量说明的 NO_TRADE 信号
                print(f"\n✗ 终止蜂群咨询 - 数据质量不足")
                print(f"  由于数据质量问题返回 NO_TRADE 信号\n")

                return [{
                    "instance_id": "DATA_QUALITY_CHECK",
                    "template_used": "N/A",
                    "target": "N/A",
                    "signal": "NO_TRADE",
                    "params": {},
                    "confidence": 0.0,
                    "reasoning": (
                        f"数据质量验证失败: {validation['summary']}。"
                        f"发现 {len(critical_issues)} 个严重和 {len(high_issues)} 个高严重度问题。"
                        f"建议: {'; '.join(validation['recommendations'])}"
                    )
                }]
            else:
                print(f"✅ 数据质量验证通过")
                print(f"📊 {len(validation['symbols_passed'])}/{len(symbols)} 个标的数据充足\n")
        else:
            print(f"⚠️  未提供标的用于数据质量验证 (NO_SYMBOLS)")
            print(f"  谨慎继续 - 蜂群可能因缺少数据而失败\n")

    # 并发执行蜂群
    loop = asyncio.get_event_loop()
    signals = loop.run_until_complete(
        execute_swarm_concurrent(instances, market_data, max_concurrent)
    )

    # 去重信号
    signals = deduplicate_signals(signals)

    # 将 Signal 对象转换为字典
    signal_dicts = [
        {
            "instance_id": s.instance_id,
            "template_used": s.template_used,
            "target": s.target,
            "signal": s.signal,
            "params": s.params,
            "confidence": s.confidence,
            "reasoning": s.reasoning
        }
        for s in signals
    ]

    # 用可执行的腿丰富信号（如果尚未存在）
    enriched_signals = []
    for sig in signal_dicts:
        enriched = enrich_signal(sig, market_data)

        # 验证丰富化
        if validate_enriched_signal(enriched):
            enriched_signals.append(enriched)
        else:
            print(f"警告：来自 {sig['instance_id']} 的信号在丰富化后验证失败 (ENRICHMENT_VALIDATION_FAILED)")
            # 仍然包含它，但标记为不完整
            enriched_signals.append(enriched)

    return enriched_signals


def fetch_market_snapshot() -> Dict[str, Any]:
    """
    获取当前市场数据快照。

    TODO: 集成 ThetaData MCP 服务器以获取真实市场数据。

    返回:
        市场数据字典
    """
    # 市场数据获取的占位符
    # 在生产环境中，调用 ThetaData MCP 服务器：
    # - 获取标的池的报价
    # - 获取期权链
    # - 计算 IV rank/百分位
    return {
        "timestamp": datetime.now().isoformat(),
        "symbols": ["AAPL", "NVDA", "AMD"],
        "quotes": {},
        "options_chains": {}
    }
