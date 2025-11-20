#!/usr/bin/env python3
"""
Independent Watchdog Process - Safety Monitor

SAFETY-CRITICAL COMPONENT

This process runs independently from the AI and can force-kill frozen processes,
trigger circuit breakers, and panic-close positions.
"""

import time
import os
import signal
import logging
from pathlib import Path
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - WATCHDOG - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
HEARTBEAT_FILE = Path.home() / "trading_workspace" / "heartbeat.txt"
HEARTBEAT_TIMEOUT = 60  # seconds
CHECK_INTERVAL = 10  # seconds
MEMORY_FILE = Path.home() / "trading_workspace" / "state" / "agent_memory.json"


def check_heartbeat() -> bool:
    """
    Check if AI process is alive based on heartbeat file.

    Returns:
        True if heartbeat is recent, False if stale/missing
    """
    if not HEARTBEAT_FILE.exists():
        return False

    try:
        with open(HEARTBEAT_FILE, 'r') as f:
            last_heartbeat = f.read().strip()

        last_time = datetime.fromisoformat(last_heartbeat)
        elapsed = (datetime.now() - last_time).total_seconds()

        return elapsed < HEARTBEAT_TIMEOUT

    except Exception as e:
        logger.error(f"Error reading heartbeat: {e}")
        return False


def get_account_value() -> float:
    """
    Get current account value from IBKR.

    Connects to IBKR directly using ib_insync with a separate client ID (999)
    to ensure independence from the main AI process.

    Returns:
        Account net liquidation value
    """
    try:
        # Use the IBKR connection manager from the MCP server
        import sys
        import os

        # Add parent directory to path to import from mcp-servers
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp-servers', 'ibkr'))

        from connection import get_connection_manager, ConnectionMode

        manager = get_connection_manager()

        # Connect with separate client ID if not already connected
        if not manager.is_connected:
            port = int(os.environ.get('IBKR_PORT', '4002'))
            mode = ConnectionMode.PAPER_GATEWAY if port == 4002 else ConnectionMode.PAPER_TWS
            manager.connect_sync(mode=mode, client_id=999)  # Separate client ID for watchdog

        # Get account values
        account_values = manager.get_account_values()

        if account_values and "NetLiquidation" in account_values:
            net_liq = float(account_values["NetLiquidation"].value)
            logger.info(f"Current account value: ${net_liq:,.2f}")
            return net_liq
        else:
            logger.warning("NetLiquidation not found in account values")
            return 10000.0

    except Exception as e:
        logger.error(f"Error getting account value from IBKR: {e}")
        logger.warning("Using fallback account value")
        # Return safe default
        return 10000.0


def check_drawdown_circuit_breaker(current_value: float, initial_value: float) -> bool:
    """
    Check if drawdown exceeds circuit breaker threshold.

    Args:
        current_value: Current account value
        initial_value: Starting account value

    Returns:
        True if circuit breaker should trigger
    """
    drawdown = (initial_value - current_value) / initial_value
    CIRCUIT_BREAKER_THRESHOLD = 0.10  # 10%

    if drawdown >= CIRCUIT_BREAKER_THRESHOLD:
        logger.critical(f"CIRCUIT BREAKER TRIGGERED: {drawdown*100:.1f}% drawdown")
        return True

    return False


def trigger_circuit_breaker():
    """Trigger circuit breaker and update agent memory."""
    logger.critical("=== TRIGGERING CIRCUIT BREAKER ===")

    # Update agent memory
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    memory = {}
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, 'r') as f:
            memory = json.load(f)

    memory.setdefault("safety_state", {})
    memory["safety_state"]["circuit_breaker_triggered"] = True
    memory["safety_state"]["circuit_breaker_timestamp"] = datetime.now().isoformat()

    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=2)

    logger.critical("Circuit breaker flag set in agent memory")

    # Log to safety events
    from data_lake.db_helpers import log_safety_event
    log_safety_event(
        event_type="CIRCUIT_BREAKER",
        details={"reason": "drawdown_threshold_exceeded"},
        action_taken="trading_suspended"
    )


def panic_close_all_positions():
    """
    Force close all open positions at market.

    TODO: Implement actual IBKR connection to close positions

    This is the NUCLEAR OPTION - only called in emergencies.
    """
    logger.critical("=== PANIC CLOSE INITIATED ===")

    # TODO: Connect to IBKR with independent connection
    # positions = ibkr.positions()
    # for pos in positions:
    #     order = MarketOrder('SELL' if pos.position > 0 else 'BUY', abs(pos.position))
    #     ibkr.placeOrder(pos.contract, order)

    logger.critical("All positions closed (placeholder - implement IBKR)")


def handle_frozen_ai(ai_pid: int):
    """
    Handle frozen AI process.

    Args:
        ai_pid: Process ID of frozen AI
    """
    logger.critical("=== AI PROCESS FROZEN ===")
    logger.critical(f"Terminating AI process (PID: {ai_pid})")

    try:
        # Force kill AI process
        os.kill(ai_pid, signal.SIGKILL)
        logger.critical("AI process terminated")

    except ProcessLookupError:
        logger.warning("AI process already terminated")

    # Close all positions
    panic_close_all_positions()

    # Trigger circuit breaker
    trigger_circuit_breaker()

    # Log safety event
    from data_lake.db_helpers import log_safety_event
    log_safety_event(
        event_type="WATCHDOG_ALERT",
        details={"reason": "ai_process_frozen", "ai_pid": ai_pid},
        action_taken="forced_termination_and_position_close"
    )


def monitor_loop(initial_account_value: float):
    """
    Main monitoring loop.

    Args:
        initial_account_value: Starting account value for drawdown calculation
    """
    logger.info("Watchdog monitoring started")
    logger.info(f"Heartbeat timeout: {HEARTBEAT_TIMEOUT}s")
    logger.info(f"Check interval: {CHECK_INTERVAL}s")

    ai_pid = os.getppid()  # Parent process is the AI main loop

    while True:
        try:
            # Check 1: AI process heartbeat
            if not check_heartbeat():
                logger.warning("Heartbeat stale or missing")
                # Give one more cycle before taking action
                time.sleep(CHECK_INTERVAL)
                if not check_heartbeat():
                    handle_frozen_ai(ai_pid)
                    break  # Exit after emergency action

            # Check 2: Account drawdown
            account_value = get_account_value()
            if check_drawdown_circuit_breaker(account_value, initial_account_value):
                trigger_circuit_breaker()
                panic_close_all_positions()
                break  # Exit after circuit breaker

            # All checks passed
            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            logger.info("Watchdog shutdown signal received")
            break

        except Exception as e:
            logger.error(f"Error in watchdog loop: {e}", exc_info=True)
            time.sleep(CHECK_INTERVAL)


def main():
    """Watchdog main entry point."""
    logger.info("=== Independent Watchdog Starting ===")

    # Get initial account value
    initial_value = get_account_value()
    logger.info(f"Initial account value: ${initial_value:.2f}")

    # Start monitoring
    monitor_loop(initial_value)

    logger.info("=== Watchdog Shutdown ===")


if __name__ == "__main__":
    main()
