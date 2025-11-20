"""
Swarm Intelligence Core - Concurrent agent orchestration.

This is the recursive intelligence engine that executes multiple strategy
instances concurrently and aggregates their signals.
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


# Paths
SWARM_BASE = Path(__file__).parent.parent / "swarm_intelligence"
TEMPLATES_DIR = SWARM_BASE / "templates"
INSTANCES_DIR = SWARM_BASE / "active_instances"


@dataclass
class Signal:
    """Trading signal from swarm instance."""
    instance_id: str
    template_used: str
    target: str
    signal: str  # e.g., "SHORT_PUT_SPREAD", "LONG_CALL", "NO_TRADE"
    params: Dict[str, Any]
    confidence: float  # 0.0 to 1.0
    reasoning: str


def load_instances(sector_filter: Optional[str] = None) -> List[Dict]:
    """
    Load active instance configurations from JSON files.

    Args:
        sector_filter: Filter by sector ("ALL", "TECH", "FINANCE", etc.)
                       "ALL" or None returns all instances

    Returns:
        List of instance configuration dictionaries
    """
    if not INSTANCES_DIR.exists():
        return []

    instances = []
    for json_file in INSTANCES_DIR.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                instance = json.load(f)

            # Apply sector filter
            if sector_filter and sector_filter != "ALL":
                instance_sector = instance.get("sector", "").upper()
                if instance_sector != sector_filter.upper():
                    continue

            instances.append(instance)

        except json.JSONDecodeError as e:
            print(f"Warning: Failed to load instance {json_file}: {e}")
            continue

    return instances


def load_template(template_name: str) -> str:
    """
    Load strategy template from file.

    Args:
        template_name: Template filename (e.g., "vol_sniper.md")

    Returns:
        Template content as string

    Raises:
        FileNotFoundError: If template doesn't exist
    """
    template_path = TEMPLATES_DIR / template_name

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_name}")

    with open(template_path, 'r') as f:
        return f.read()


def render_template(template_content: str, parameters: Dict[str, Any], market_data: Dict[str, Any] = None) -> str:
    """
    Render Jinja2 template with parameters and market data.

    Args:
        template_content: Template string with Jinja2 placeholders
        parameters: Dictionary of parameters to inject
        market_data: Market data snapshot to inject (optional)

    Returns:
        Rendered template string
    """
    # Use StrictUndefined to catch missing template variables early
    env = Environment(undefined=StrictUndefined)
    template = env.from_string(template_content)

    # Merge parameters and market_data for template context
    context = {**parameters}
    if market_data:
        context['market_data'] = market_data

    return template.render(**context)


async def execute_single_instance(
    instance: Dict,
    market_data: Dict[str, Any],
    timeout: int = 20
) -> Optional[Signal]:
    """
    Execute a single swarm instance (async).

    This function:
    1. Loads and renders template
    2. Saves input snapshot
    3. Calls LLM API
    4. Parses response into Signal
    5. Updates snapshot with response

    Args:
        instance: Instance configuration
        market_data: Market data snapshot
        timeout: Timeout in seconds

    Returns:
        Signal object or None if execution failed
    """
    instance_id = instance["id"]
    template_name = instance["template"]
    parameters = instance.get("parameters", {})

    try:
        # Load and render template
        template_content = load_template(template_name)
        print(f"[{instance_id}] Template loaded: {template_name}")

        rendered_prompt = render_template(template_content, parameters, market_data)
        print(f"[{instance_id}] Template rendered successfully")

        # Save input snapshot BEFORE LLM call
        timestamp = datetime.now().isoformat()
        print(f"[{instance_id}] Saving snapshot...")
        snapshot_id = save_snapshot(
            instance_id=instance_id,
            template_name=template_name,
            rendered_prompt=rendered_prompt,
            market_data=market_data,
            agent_response=None,  # Will update after LLM call
            timestamp=timestamp
        )
        print(f"[{instance_id}] Snapshot saved: {snapshot_id}")

        # Execute LLM API call (with timeout)
        # TODO: Replace with actual Anthropic API call
        # For now, simulate response
        try:
            response = await asyncio.wait_for(
                call_llm_api(rendered_prompt, market_data),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            print(f"Warning: Instance {instance_id} timed out after {timeout}s")
            return None

        # Parse response into Signal
        signal = parse_signal_response(response, instance_id, template_name)

        # Update snapshot with response
        update_snapshot_response(snapshot_id, {
            "raw_response": response,
            "parsed_signal": signal.__dict__ if signal else None
        })

        return signal

    except FileNotFoundError as e:
        print(f"Warning: {e}")
        return None
    except Exception as e:
        print(f"Error executing instance {instance_id}: {e}")
        return None


async def call_llm_api(prompt: str, market_data: Dict) -> Dict:
    """
    Call LLM API via OpenRouter to get trading signal.

    Uses Gemini 2.5 Flash for fast, cost-effective concurrent execution.

    Args:
        prompt: Rendered prompt
        market_data: Market data context

    Returns:
        LLM response dictionary (parsed from JSON response)
    """
    import os
    from openai import AsyncOpenAI

    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("Warning: OPENROUTER_API_KEY not set, using mock response")
        # Fallback to mock for testing
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
            "reasoning": "Elevated IV with neutral sentiment suggests premium selling opportunity."
        }

    try:
        # Initialize OpenRouter client (OpenAI-compatible)
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )

        # Call Gemini 2.0 Flash via OpenRouter
        completion = await client.chat.completions.create(
            model="google/gemini-2.5-flash",  # Free tier, very fast
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=1000,
            extra_headers={
                "HTTP-Referer": "https://github.com/agentic-alphahive",  # Optional
                "X-Title": "Agentic AlphaHive Runtime"  # Optional
            }
        )

        # Extract response content
        response_text = completion.choices[0].message.content

        # Strip markdown code blocks if present
        # Gemini often wraps JSON in ```json ... ```
        response_text = response_text.strip()
        if response_text.startswith("```"):
            # Remove opening ```json or ```
            lines = response_text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove closing ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines).strip()

        # Parse JSON response
        import json
        response_json = json.loads(response_text)

        return response_json

    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse LLM response as JSON: {e}")
        print(f"Raw response: {response_text[:200]}")
        return None

    except Exception as e:
        print(f"Error calling OpenRouter API: {e}")
        return None


def parse_signal_response(response: Dict, instance_id: str, template_name: str) -> Optional[Signal]:
    """
    Parse LLM response into Signal object.

    Args:
        response: LLM API response
        instance_id: Instance identifier
        template_name: Template used

    Returns:
        Signal object or None if parsing failed
    """
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
        print(f"Warning: Failed to parse signal from {instance_id}: {e}")
        return None


def deduplicate_signals(signals: List[Signal]) -> List[Signal]:
    """
    Remove duplicate signals targeting the same symbol with same strategy.

    When multiple instances produce the same signal, keep the one with
    highest confidence.

    Args:
        signals: List of Signal objects

    Returns:
        Deduplicated list of signals
    """
    # Group by (target, signal)
    signal_groups = {}
    for signal in signals:
        key = (signal.target, signal.signal)
        if key not in signal_groups:
            signal_groups[key] = []
        signal_groups[key].append(signal)

    # Keep highest confidence signal from each group
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
    Execute multiple swarm instances concurrently.

    Args:
        instances: List of instance configurations
        market_data: Market data snapshot
        max_concurrent: Maximum concurrent LLM API calls

    Returns:
        List of Signal objects from successful executions
    """
    # Create semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_concurrent)

    async def execute_with_semaphore(instance):
        async with semaphore:
            return await execute_single_instance(instance, market_data)

    # Execute all instances concurrently
    tasks = [execute_with_semaphore(inst) for inst in instances]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out None and exception results
    signals = []
    for result in results:
        if isinstance(result, Signal):
            signals.append(result)
        elif isinstance(result, Exception):
            print(f"Warning: Instance failed with exception: {result}")

    return signals


def consult_swarm(
    sector: str = "ALL",
    market_data: Optional[Dict] = None,
    max_concurrent: int = 50,
    skip_data_validation: bool = False
) -> List[Dict]:
    """
    Execute swarm intelligence analysis.

    This is the main entry point for Commander to invoke the swarm.

    Args:
        sector: Filter instances by sector ("ALL", "TECH", "FINANCE", etc.)
        market_data: Current market snapshot (if None, fetches fresh data)
        max_concurrent: Maximum concurrent LLM API calls
        skip_data_validation: Skip data quality validation (NOT RECOMMENDED)

    Returns:
        List of signal dictionaries with structure:
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

    Example:
        >>> signals = consult_swarm(sector="TECH")
        >>> print(f"Received {len(signals)} signals")
        Received 3 signals
    """
    # Load active instances
    instances = load_instances(sector_filter=sector)

    if not instances:
        print(f"Warning: No active instances found for sector '{sector}'")
        return []

    # Fetch market data if not provided
    if market_data is None:
        market_data = fetch_market_snapshot()

    # === DATA QUALITY PRE-FLIGHT CHECK ===
    if not skip_data_validation:
        from skills.data_quality import validate_data_quality, auto_trigger_backfill

        # Extract symbols from market_data snapshot
        symbols = []
        if market_data and 'snapshot' in market_data:
            symbols = list(market_data['snapshot'].keys())

        # Also collect symbols from instance symbol pools
        for instance in instances:
            symbol_pool = instance.get('parameters', {}).get('symbol_pool', [])
            symbols.extend(symbol_pool)

        # Remove duplicates
        symbols = list(set(symbols))

        if symbols:
            print(f"\n=== DATA QUALITY PRE-FLIGHT CHECK ===")
            print(f"Validating data for {len(symbols)} symbols...")

            # Validate data quality
            validation = validate_data_quality(
                symbols=symbols,
                min_daily_bars=20,  # Reduced from 30 for more lenient check
                min_hourly_bars=30,
                min_5min_bars=200,
                max_age_hours=8,  # Allow slightly stale data
                require_all_intervals=False  # Be lenient
            )

            if not validation['valid']:
                print(f"\n⚠️  DATA QUALITY VALIDATION FAILED")
                print(f"Summary: {validation['summary']}")
                print(f"\nIssues found:")

                # Group issues by severity
                critical_issues = [i for i in validation['issues'] if i['severity'] == 'CRITICAL']
                high_issues = [i for i in validation['issues'] if i['severity'] == 'HIGH']

                if critical_issues:
                    print(f"  CRITICAL ({len(critical_issues)}):")
                    for issue in critical_issues[:5]:  # Show first 5
                        print(f"    - {issue['symbol']}: {issue['issue']} ({issue['detail']})")

                if high_issues:
                    print(f"  HIGH ({len(high_issues)}):")
                    for issue in high_issues[:3]:  # Show first 3
                        print(f"    - {issue['symbol']}: {issue['issue']} ({issue['detail']})")

                print(f"\nRecommendations:")
                for rec in validation['recommendations']:
                    print(f"  → {rec}")

                # Return NO_TRADE signals with data quality explanation
                print(f"\n✗ ABORTING SWARM CONSULTATION - Data quality insufficient")
                print(f"  Returning NO_TRADE signals due to data quality issues\n")

                return [{
                    "instance_id": "DATA_QUALITY_CHECK",
                    "template_used": "N/A",
                    "target": "N/A",
                    "signal": "NO_TRADE",
                    "params": {},
                    "confidence": 0.0,
                    "reasoning": (
                        f"Data quality validation failed: {validation['summary']}. "
                        f"Found {len(critical_issues)} critical and {len(high_issues)} high severity issues. "
                        f"Recommendations: {'; '.join(validation['recommendations'])}"
                    )
                }]
            else:
                print(f"✓ Data quality validation PASSED")
                print(f"  {len(validation['symbols_passed'])}/{len(symbols)} symbols have sufficient data\n")
        else:
            print(f"⚠️  No symbols provided for data quality validation")
            print(f"  Proceeding with caution - swarm may fail due to missing data\n")

    # Execute swarm concurrently
    loop = asyncio.get_event_loop()
    signals = loop.run_until_complete(
        execute_swarm_concurrent(instances, market_data, max_concurrent)
    )

    # Deduplicate signals
    signals = deduplicate_signals(signals)

    # Convert Signal objects to dictionaries
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

    # Enrich signals with executable legs (if not already present)
    enriched_signals = []
    for sig in signal_dicts:
        enriched = enrich_signal(sig, market_data)

        # Validate enrichment
        if validate_enriched_signal(enriched):
            enriched_signals.append(enriched)
        else:
            print(f"Warning: Signal from {sig['instance_id']} failed validation after enrichment")
            # Still include it, but mark as incomplete
            enriched_signals.append(enriched)

    return enriched_signals


def fetch_market_snapshot() -> Dict[str, Any]:
    """
    Fetch current market data snapshot.

    TODO: Integrate with ThetaData MCP server to get real market data.

    Returns:
        Market data dictionary
    """
    # Placeholder for market data fetching
    # In production, call ThetaData MCP server:
    # - Get quotes for symbol pool
    # - Get options chains
    # - Calculate IV rank/percentile
    return {
        "timestamp": datetime.now().isoformat(),
        "symbols": ["AAPL", "NVDA", "AMD"],
        "quotes": {},
        "options_chains": {}
    }
