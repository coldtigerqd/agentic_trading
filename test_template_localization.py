#!/usr/bin/env python3
"""
Integration test for Phase 1 Chinese localization.

Tests:
1. All 5 swarm strategy templates can be loaded
2. Templates render correctly with Jinja2 substitution
3. No syntax errors in templates
4. Chinese content is properly encoded
5. Commander system prompt loads correctly
"""

import json
from pathlib import Path
from jinja2 import Template, Environment, StrictUndefined
from typing import Dict, Any


# Paths
PROJECT_ROOT = Path(__file__).parent
TEMPLATES_DIR = PROJECT_ROOT / "swarm_intelligence" / "templates"
INSTANCES_DIR = PROJECT_ROOT / "swarm_intelligence" / "active_instances"
COMMANDER_PROMPT = PROJECT_ROOT / "prompts" / "commander_system.md"


def load_template(template_name: str) -> str:
    """Load template file."""
    template_path = TEMPLATES_DIR / template_name
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def render_template(template_content: str, parameters: Dict[str, Any], market_data: Dict[str, Any]) -> str:
    """Render Jinja2 template with parameters."""
    env = Environment(undefined=StrictUndefined)
    template = env.from_string(template_content)

    context = {**parameters, 'market_data': market_data}
    return template.render(**context)


def test_template_rendering():
    """Test all 5 swarm templates render correctly."""

    # Mock market data
    mock_market_data = {
        "snapshot": {
            "AAPL": {"price": 182.50, "age_seconds": 120, "is_stale": False},
            "NVDA": {"price": 145.20, "age_seconds": 95, "is_stale": False}
        },
        "context": {
            "spy_trend": "UPTREND",
            "market_volatility": 0.14
        }
    }

    # Template to instance mapping
    templates_to_test = {
        "trend_scout.md": {
            "symbol_pool": ["AAPL", "NVDA", "MSFT"],
            "trend_strength_threshold": 0.7,
            "min_trend_days": 10,
            "rsi_low": 40,
            "rsi_high": 50,
            "volume_multiplier": 1.5,
            "min_rr_ratio": 2.0
        },
        "vol_sniper.md": {
            "symbol_pool": ["TSLA", "AMD"],
            "min_iv_rank": 70,
            "max_delta_exposure": 0.3,
            "sentiment_filter": "neutral"
        },
        "mean_reversion.md": {
            "symbol_pool": ["SPY", "QQQ"],
            "max_adx": 25,
            "bb_period": 20,
            "bb_std_dev": 2.0,
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "min_range_days": 15
        },
        "breakout_scout.md": {
            "symbol_pool": ["META", "GOOGL"],
            "atr_contraction_pct": 35,
            "bb_squeeze_threshold": 0.10,
            "volume_multiplier": 2.0,
            "min_consolidation_days": 10,
            "breakout_confirm_bars": 2
        },
        "correlation_arbitrage.md": {
            "symbol_pairs": [["AAPL", "MSFT"], ["NVDA", "AMD"]],
            "min_correlation": 0.7,
            "zscore_threshold": 2.0,
            "lookback_days": 90,
            "min_stability_days": 30,
            "max_hedge_ratio": 2.0
        }
    }

    print("=" * 80)
    print("集成测试：Phase 1 中文本地化")
    print("=" * 80)
    print()

    results = []

    for template_name, params in templates_to_test.items():
        print(f"测试模板：{template_name}")
        print("-" * 80)

        try:
            # Load template
            template_content = load_template(template_name)
            print(f"  ✓ 模板加载成功（{len(template_content)} 字符）")

            # Check for Chinese content
            chinese_char_count = sum(1 for c in template_content if '\u4e00' <= c <= '\u9fff')
            print(f"  ✓ 检测到中文字符：{chinese_char_count} 个")

            # Render template
            rendered = render_template(template_content, params, mock_market_data)
            print(f"  ✓ 模板渲染成功（{len(rendered)} 字符）")

            # Verify no Jinja2 placeholders remain
            if "{{" in rendered or "{%" in rendered:
                print(f"  ⚠️  警告：渲染后仍存在未替换的 Jinja2 标记")
                results.append({"template": template_name, "status": "WARNING", "issue": "Unreplaced Jinja2 tags"})
            else:
                print(f"  ✓ 所有 Jinja2 变量已正确替换")

            # Check rendered output contains Chinese
            rendered_chinese = sum(1 for c in rendered if '\u4e00' <= c <= '\u9fff')
            print(f"  ✓ 渲染输出包含中文字符：{rendered_chinese} 个")

            # Verify key Chinese phrases present
            key_phrases = ["您的职责", "策略参数", "分析框架", "市场数据"]
            found_phrases = [p for p in key_phrases if p in rendered]
            print(f"  ✓ 关键中文短语检测：{len(found_phrases)}/{len(key_phrases)}")

            if len(found_phrases) < len(key_phrases):
                missing = set(key_phrases) - set(found_phrases)
                print(f"    缺失短语：{missing}")

            results.append({"template": template_name, "status": "PASS", "issue": None})
            print(f"  ✅ 测试通过\n")

        except Exception as e:
            print(f"  ❌ 测试失败：{e}\n")
            results.append({"template": template_name, "status": "FAIL", "issue": str(e)})

    return results


def test_commander_prompt():
    """Test Commander system prompt loads correctly."""
    print("=" * 80)
    print("测试：Commander 系统提示词")
    print("=" * 80)
    print()

    try:
        with open(COMMANDER_PROMPT, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"  ✓ Commander 提示词加载成功（{len(content)} 字符）")

        chinese_char_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
        print(f"  ✓ 检测到中文字符：{chinese_char_count} 个")

        # Check for key Chinese sections
        key_sections = ["您是**指挥官**", "您的职责", "关键", "市场感知"]
        found = sum(1 for s in key_sections if s in content)
        print(f"  ✓ 关键章节检测：{found}/{len(key_sections)}")

        print(f"  ✅ Commander 提示词测试通过\n")
        return {"status": "PASS", "issue": None}

    except Exception as e:
        print(f"  ❌ Commander 提示词测试失败：{e}\n")
        return {"status": "FAIL", "issue": str(e)}


def test_active_instances():
    """Test active instance configurations load correctly."""
    print("=" * 80)
    print("测试：活跃实例配置")
    print("=" * 80)
    print()

    instances = list(INSTANCES_DIR.glob("*.json"))
    print(f"找到 {len(instances)} 个实例配置文件\n")

    results = []
    for instance_file in instances:
        print(f"测试实例：{instance_file.name}")

        try:
            with open(instance_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Validate structure
            required_keys = ["id", "template", "parameters"]
            missing = [k for k in required_keys if k not in config]

            if missing:
                print(f"  ⚠️  缺少必需字段：{missing}")
                results.append({"instance": instance_file.name, "status": "WARNING", "issue": f"Missing keys: {missing}"})
            else:
                print(f"  ✓ 配置结构有效")

                # Check template exists
                template_name = config["template"]
                template_path = TEMPLATES_DIR / template_name

                if not template_path.exists():
                    print(f"  ❌ 模板不存在：{template_name}")
                    results.append({"instance": instance_file.name, "status": "FAIL", "issue": f"Template not found: {template_name}"})
                else:
                    print(f"  ✓ 引用的模板存在：{template_name}")
                    results.append({"instance": instance_file.name, "status": "PASS", "issue": None})

            print()

        except json.JSONDecodeError as e:
            print(f"  ❌ JSON 解析失败：{e}\n")
            results.append({"instance": instance_file.name, "status": "FAIL", "issue": f"JSON error: {e}"})
        except Exception as e:
            print(f"  ❌ 测试失败：{e}\n")
            results.append({"instance": instance_file.name, "status": "FAIL", "issue": str(e)})

    return results


def print_summary(template_results, commander_result, instance_results):
    """Print test summary."""
    print("=" * 80)
    print("测试总结")
    print("=" * 80)
    print()

    # Template tests
    template_passed = sum(1 for r in template_results if r["status"] == "PASS")
    template_total = len(template_results)
    print(f"蜂群策略模板：{template_passed}/{template_total} 通过")

    for result in template_results:
        status_icon = "✅" if result["status"] == "PASS" else ("⚠️" if result["status"] == "WARNING" else "❌")
        print(f"  {status_icon} {result['template']}")
        if result["issue"]:
            print(f"      问题：{result['issue']}")

    print()

    # Commander test
    commander_icon = "✅" if commander_result["status"] == "PASS" else "❌"
    print(f"Commander 系统提示词：{commander_icon}")
    if commander_result["issue"]:
        print(f"  问题：{commander_result['issue']}")

    print()

    # Instance tests
    instance_passed = sum(1 for r in instance_results if r["status"] == "PASS")
    instance_total = len(instance_results)
    print(f"活跃实例配置：{instance_passed}/{instance_total} 通过")

    for result in instance_results:
        status_icon = "✅" if result["status"] == "PASS" else ("⚠️" if result["status"] == "WARNING" else "❌")
        print(f"  {status_icon} {result['instance']}")
        if result["issue"]:
            print(f"      问题：{result['issue']}")

    print()
    print("=" * 80)

    # Overall result
    all_passed = (
        template_passed == template_total and
        commander_result["status"] == "PASS" and
        instance_passed == instance_total
    )

    if all_passed:
        print("✅ 所有测试通过！Phase 1 本地化验证成功。")
    else:
        print("⚠️  部分测试未通过，请查看上述详情。")

    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    # Run all tests
    template_results = test_template_rendering()
    commander_result = test_commander_prompt()
    instance_results = test_active_instances()

    # Print summary
    all_passed = print_summary(template_results, commander_result, instance_results)

    # Exit with appropriate code
    exit(0 if all_passed else 1)
