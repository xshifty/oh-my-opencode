#!/usr/bin/env python3
"""Get model usage stats from the OpenCode database.

Shows which AI models were used and how many times.

Usage:
  python3 get_model_usage.py <db_path>       — use a specific database file
"""

import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared import get_db, fetch_rows


def get_model_usage(db_path: str):
    """Count how many times each AI model was used across all sessions."""
    conn = get_db(db_path)
    rows = fetch_rows(conn, "SELECT data FROM message")

    model_counter = Counter()
    for row in rows:
        data = json.loads(row["data"]) if isinstance(row["data"], str) else row["data"]
        # Only look at assistant messages (they have model info)
        if data.get("role") != "assistant":
            continue
        model = data.get("model", {})
        if isinstance(model, dict):
            model_id = model.get("modelID", "")
            provider_id = model.get("providerID", "")
        else:
            continue
        if not model_id:
            continue
        key = f"{provider_id}/{model_id}" if provider_id else model_id
        model_counter[key] += 1

    total = sum(model_counter.values())
    top_models = model_counter.most_common(10)

    result = {
        "total_calls": total,
        "unique_models": len(model_counter),
        "top_models": [
            {"model": m, "count": c, "percentage": round(c / total * 100, 1)}
            for m, c in top_models
        ],
        "all_models": dict(model_counter.most_common())
    }

    print(json.dumps(result, indent=2))
    conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: get_model_usage.py <db_path>")
        sys.exit(1)
    get_model_usage(sys.argv[1])
