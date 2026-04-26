#!/usr/bin/env python3
"""Count how many times each tool was used and how many errors each had.

Output JSON: usage (top 20 tools by count), errors (top 10 tools by error count)

Usage:
  python3 get_tool_usage.py                    — find the database automatically
  python3 get_tool_usage.py /path/to/db.db     — use a specific database file
"""

import json
import sys
from collections import Counter

from shared import find_db_path, get_db, parse_part_data


def main():
    db_path = None
    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    try:
        db_path = db_path or find_db_path()
        conn = get_db(db_path)

        # Get all tool-related parts
        parts = [dict(r) for r in conn.execute(
            "SELECT id, data FROM part WHERE json_extract(data, '$.type') = 'tool'"
        ).fetchall()]

        usage_counts = Counter()
        error_counts = Counter()

        for p in parts:
            data = parse_part_data(p)
            tool_name = (data.get("tool") or "").strip()
            status = (data.get("state", {}).get("status") if isinstance(data.get("state"), dict) else "") or ""

            if tool_name:
                usage_counts[tool_name] += 1
                # Check if the tool call had an error
                if "error" in str(status).lower():
                    error_counts[tool_name] += 1

        conn.close()

        result = {
            "usage": dict(usage_counts.most_common(20)),
            "errors": dict(error_counts.most_common(10)),
        }

    except Exception as e:
        result = {"error": str(e)}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
