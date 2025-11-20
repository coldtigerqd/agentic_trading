#!/usr/bin/env python3
"""
Main trading loop - schedules cycles and invokes Commander.

This is the entry point for the Agentic AlphaHive Runtime.
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import time
import logging
from datetime import datetime
import multiprocessing

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Heartbeat file for watchdog monitoring
HEARTBEAT_FILE = Path.home() / "trading_workspace" / "heartbeat.txt"
CYCLE_INTERVAL_SECONDS = 300  # 5 minutes


def send_heartbeat():
    """Write heartbeat timestamp for watchdog monitoring."""
    HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HEARTBEAT_FILE, 'w') as f:
        f.write(datetime.now().isoformat())


def is_circuit_breaker_triggered() -> bool:
    """
    Check if circuit breaker is active.

    Returns:
        True if trading should be suspended
    """
    # Check agent memory for circuit breaker flag
    memory_path = Path.home() / "trading_workspace" / "state" / "agent_memory.json"

    if not memory_path.exists():
        return False

    import json
    with open(memory_path, 'r') as f:
        memory = json.load(f)

    return memory.get("safety_state", {}).get("circuit_breaker_triggered", False)


def trading_cycle():
    """
    Execute one trading cycle.

    This function provides the scheduling framework.
    The actual trading decisions are made by Commander agent.
    """
    logger.info("=== Starting Trading Cycle ===")

    # Send heartbeat to watchdog
    send_heartbeat()

    # Check circuit breaker
    if is_circuit_breaker_triggered():
        logger.warning("Circuit breaker active - skipping cycle")
        return

    # Invoke Commander agent
    # In production, this would trigger Claude Code to execute
    # the Commander system prompt and make trading decisions
    logger.info("Invoking Commander agent...")

    try:
        invoke_commander_agent()
    except Exception as e:
        logger.error(f"Error in trading cycle: {e}", exc_info=True)

    # Send heartbeat after cycle
    send_heartbeat()
    logger.info("=== Cycle Complete ===\n")


def invoke_commander_agent():
    """
    Invoke Commander agent to make trading decisions.

    TODO: Integrate with Claude Code to actually execute Commander prompt.

    For now, this is a placeholder that demonstrates the cycle structure.
    """
    logger.info("Commander agent would execute here")
    logger.info("Commander workflow:")
    logger.info("  1. SENSE: Query account and market data")
    logger.info("  2. THINK: Consult swarm for signals")
    logger.info("  3. DECIDE: Evaluate signals and risk")
    logger.info("  4. ACT: Execute validated orders")


def main():
    """Main entry point."""
    logger.info("=== Agentic AlphaHive Runtime Starting ===")
    logger.info(f"Cycle interval: {CYCLE_INTERVAL_SECONDS} seconds")
    logger.info(f"Heartbeat file: {HEARTBEAT_FILE}")

    # Start watchdog in separate process
    from runtime import watchdog
    watchdog_process = multiprocessing.Process(
        target=watchdog.main,
        name="watchdog"
    )
    watchdog_process.start()
    logger.info(f"Watchdog process started (PID: {watchdog_process.pid})")

    try:
        while True:
            trading_cycle()
            time.sleep(CYCLE_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logger.info("Shutdown signal received")

    finally:
        logger.info("Shutting down gracefully...")
        watchdog_process.terminate()
        watchdog_process.join(timeout=5)
        logger.info("Shutdown complete")


if __name__ == "__main__":
    main()
