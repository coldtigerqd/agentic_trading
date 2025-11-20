"""
Snapshot storage manager for swarm decision logging.

Provides functions to save and load complete decision contexts for auditability.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from jinja2 import Undefined, StrictUndefined


SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"


def clean_undefined_objects(obj: Any) -> Any:
    """
    Recursively clean Jinja2 Undefined objects from data structures.

    This prevents JSON serialization errors when template variables are undefined.

    Args:
        obj: Object to clean (dict, list, or primitive)

    Returns:
        Cleaned object with Undefined replaced by "<undefined>"
    """
    # Check for Undefined types (both base Undefined and StrictUndefined)
    try:
        if isinstance(obj, (Undefined, StrictUndefined)):
            return "<undefined>"
    except:
        # If isinstance check itself fails, likely an Undefined object
        return "<undefined>"

    if isinstance(obj, dict):
        return {k: clean_undefined_objects(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_undefined_objects(item) for item in obj]
    else:
        return obj


def save_snapshot(
    instance_id: str,
    template_name: str,
    rendered_prompt: str,
    market_data: Dict[str, Any],
    agent_response: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None
) -> str:
    """
    Save a complete swarm execution snapshot.

    Args:
        instance_id: Swarm instance identifier
        template_name: Template file name used
        rendered_prompt: Complete rendered prompt sent to LLM
        market_data: Market data snapshot provided to agent
        agent_response: LLM response (if available, None during save-before-execution)
        timestamp: Override timestamp (ISO format, defaults to now)

    Returns:
        snapshot_id: Unique snapshot identifier (filename without extension)
    """
    # Ensure snapshots directory exists
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate timestamp and snapshot ID
    if timestamp is None:
        timestamp = datetime.now().isoformat()

    # Format: YYYYMMDDTHHMMSS_instance_id
    timestamp_short = timestamp.replace(":", "").replace("-", "").split(".")[0]
    snapshot_id = f"{timestamp_short}_{instance_id}"
    filename = f"{snapshot_id}.json"
    filepath = SNAPSHOTS_DIR / filename

    # Construct snapshot object
    snapshot = {
        "snapshot_id": snapshot_id,
        "timestamp": timestamp,
        "instance_id": instance_id,
        "template_name": template_name,
        "rendered_prompt": rendered_prompt,
        "market_data": market_data,
        "agent_response": agent_response
    }

    # Clean any Undefined objects before JSON serialization
    snapshot = clean_undefined_objects(snapshot)

    # Write snapshot to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    return snapshot_id


def update_snapshot_response(
    snapshot_id: str,
    agent_response: Dict[str, Any]
):
    """
    Update an existing snapshot with agent response.

    This is called after LLM execution completes to append the response
    to the snapshot that was saved before execution.

    Args:
        snapshot_id: Snapshot identifier
        agent_response: LLM response to append
    """
    filename = f"{snapshot_id}.json"
    filepath = SNAPSHOTS_DIR / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Snapshot not found: {snapshot_id}")

    # Load existing snapshot
    with open(filepath, 'r', encoding='utf-8') as f:
        snapshot = json.load(f)

    # Update with response (clean undefined objects)
    snapshot["agent_response"] = clean_undefined_objects(agent_response)

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)


def load_snapshot(snapshot_id: str) -> Dict[str, Any]:
    """
    Load a snapshot by ID.

    Args:
        snapshot_id: Snapshot identifier

    Returns:
        Snapshot dictionary

    Raises:
        FileNotFoundError: If snapshot doesn't exist
    """
    filename = f"{snapshot_id}.json"
    filepath = SNAPSHOTS_DIR / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Snapshot not found: {snapshot_id}")

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_snapshots(
    instance_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
) -> List[str]:
    """
    List snapshot IDs with optional filters.

    Args:
        instance_id: Filter by instance ID
        start_date: Filter by start date (YYYYMMDD format)
        end_date: Filter by end date (YYYYMMDD format)
        limit: Maximum number of results

    Returns:
        List of snapshot IDs (sorted by timestamp descending)
    """
    # Ensure directory exists
    if not SNAPSHOTS_DIR.exists():
        return []

    # Get all snapshot files
    snapshot_files = sorted(
        SNAPSHOTS_DIR.glob("*.json"),
        key=lambda p: p.stem,
        reverse=True  # Most recent first
    )

    snapshot_ids = []
    for filepath in snapshot_files:
        snapshot_id = filepath.stem

        # Extract timestamp and instance from filename
        # Format: YYYYMMDDTHHMMSS_instance_id
        parts = snapshot_id.split("_", 1)
        if len(parts) != 2:
            continue

        timestamp_part, file_instance_id = parts

        # Filter by instance_id
        if instance_id and file_instance_id != instance_id:
            continue

        # Filter by date range
        if start_date and timestamp_part[:8] < start_date.replace("-", ""):
            continue

        if end_date and timestamp_part[:8] > end_date.replace("-", ""):
            continue

        snapshot_ids.append(snapshot_id)

        if len(snapshot_ids) >= limit:
            break

    return snapshot_ids


def get_snapshot_stats() -> Dict[str, Any]:
    """
    Get statistics about stored snapshots.

    Returns:
        Dictionary with snapshot statistics
    """
    if not SNAPSHOTS_DIR.exists():
        return {
            "total_snapshots": 0,
            "total_size_bytes": 0,
            "instances": []
        }

    snapshot_files = list(SNAPSHOTS_DIR.glob("*.json"))

    # Calculate total size
    total_size = sum(f.stat().st_size for f in snapshot_files)

    # Count by instance
    instance_counts = {}
    for filepath in snapshot_files:
        parts = filepath.stem.split("_", 1)
        if len(parts) == 2:
            instance_id = parts[1]
            instance_counts[instance_id] = instance_counts.get(instance_id, 0) + 1

    return {
        "total_snapshots": len(snapshot_files),
        "total_size_bytes": total_size,
        "instances": [
            {"instance_id": k, "count": v}
            for k, v in sorted(instance_counts.items(), key=lambda x: x[1], reverse=True)
        ]
    }
