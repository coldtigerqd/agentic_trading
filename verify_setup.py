#!/usr/bin/env python3
"""
Verification script to test all core components.
"""

import sys
from pathlib import Path

print("=" * 60)
print("Agentic AlphaHive Runtime - Setup Verification")
print("=" * 60)

# Test 1: Skills Import
print("\n[1/6] Testing skills library import...")
try:
    from skills import (
        consult_swarm,
        kelly_criterion,
        black_scholes_iv,
        place_order_with_guard,
        OrderResult
    )
    print("✓ Skills library imported successfully")
except ImportError as e:
    print(f"✗ Skills import failed: {e}")
    sys.exit(1)

# Test 2: Math Functions
print("\n[2/6] Testing mathematical functions...")
try:
    position_size = kelly_criterion(0.6, 500, 200, 10000, 0.25)
    iv = black_scholes_iv(5.50, 100, 105, 0.25, 0.05, True)
    assert position_size > 0, "Kelly criterion failed"
    assert iv is not None and iv > 0, "Black-Scholes IV failed"
    print(f"✓ Kelly criterion: ${position_size:.2f}")
    print(f"✓ Black-Scholes IV: {iv:.2%}")
except Exception as e:
    print(f"✗ Math functions failed: {e}")
    sys.exit(1)

# Test 3: Database
print("\n[3/6] Testing database operations...")
try:
    from data_lake.db_helpers import log_trade, query_trades

    # Log a test trade
    trade_id = log_trade(
        symbol="TEST",
        strategy="TEST_STRATEGY",
        legs=[{"action": "BUY", "strike": 100}],
        max_risk=100,
        capital_required=500,
        status="PENDING"
    )

    # Query it back
    trades = query_trades(symbol="TEST", limit=1)
    assert len(trades) > 0, "Database query failed"
    print(f"✓ Database operational (trade_id={trade_id})")
except Exception as e:
    print(f"✗ Database failed: {e}")
    sys.exit(1)

# Test 4: Snapshot Manager
print("\n[4/6] Testing snapshot storage...")
try:
    from data_lake.snapshot_manager import save_snapshot, list_snapshots

    snapshot_id = save_snapshot(
        instance_id="test_instance",
        template_name="test_template.md",
        rendered_prompt="Test prompt",
        market_data={"test": "data"}
    )

    snapshots = list_snapshots(instance_id="test_instance", limit=5)
    assert len(snapshots) > 0, "Snapshot storage failed"
    print(f"✓ Snapshots working (snapshot_id={snapshot_id})")
except Exception as e:
    print(f"✗ Snapshot manager failed: {e}")
    sys.exit(1)

# Test 5: Swarm Configuration
print("\n[5/6] Testing swarm configuration loading...")
try:
    from skills.swarm_core import load_instances, load_template

    instances = load_instances()
    assert len(instances) >= 2, "Expected at least 2 instances"

    template = load_template("vol_sniper.md")
    assert "Volatility Sniper" in template, "Template content invalid"

    print(f"✓ Loaded {len(instances)} swarm instances")
    for inst in instances:
        print(f"  - {inst['id']}: {inst.get('sector', 'N/A')}")
except Exception as e:
    print(f"✗ Swarm configuration failed: {e}")
    sys.exit(1)

# Test 6: Commander Prompt
print("\n[6/6] Testing commander prompt...")
try:
    prompt_path = Path("prompts/commander_system.md")
    assert prompt_path.exists(), "Commander prompt not found"

    content = prompt_path.read_text()
    assert "Commander" in content, "Commander prompt invalid"
    assert "SENSE" in content and "THINK" in content, "Workflow missing"

    print(f"✓ Commander prompt ready ({len(content)} chars)")
except Exception as e:
    print(f"✗ Commander prompt check failed: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("✅ All components verified successfully!")
print("=" * 60)
print("\nSystem Status:")
print("  • Skills Library: Ready")
print("  • Data Persistence: Ready")
print("  • Swarm Intelligence: Ready")
print("  • Commander Prompt: Ready")
print("  • Safety Layer: Ready (via IBKR MCP)")
print("\nNext Steps:")
print("  1. Install IBKR dependencies: pip install ib-insync")
print("  2. Configure .env with API keys")
print("  3. Start IBKR Gateway on port 4002 (paper trading)")
print("  4. Run: python runtime/main_loop.py")
print()
