#!/usr/bin/env python3
"""Group sessions by project directory and show tool usage for each area.

Output JSON: areas array with directory, session_count, dominant_tool, top_tools.

Usage:
  python3 get_project_areas.py                    — find the database automatically
  python3 get_project_areas.py /path/to/db.db     — use a specific database file
"""

import json
import sys
from collections import Counter

from shared import find_db_path, get_db


def main():
    db_path = None
    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    try:
        db_path = db_path or find_db_path()
        conn = get_db(db_path)

        # Get all sessions with directory info
        sessions = [dict(r) for r in conn.execute(
            "SELECT id, directory FROM session"
        ).fetchall()]

        if not sessions:
            conn.close()
            print(json.dumps({"areas": []}, indent=2))
            return

        # Group sessions by folder path
        dir_sessions = {}
        for s in sessions:
            directory = (s.get("directory") or "unknown").strip()
            if not directory:
                directory = "unknown"

            # Keep up to 5 path parts for useful grouping
            parts = [p for p in directory.split("/") if p]
            normalized = "/" + "/".join(parts[:5]) if len(parts) >= 1 else directory

            if normalized not in dir_sessions:
                dir_sessions[normalized] = []
            dir_sessions[normalized].append(s["id"])

        # For each area, find which tools were used
        areas = []
        for directory, session_ids in sorted(dir_sessions.items(), key=lambda x: -len(x[1]))[:10]:
            placeholders = ",".join("?" for _ in session_ids)
            msg_ids = [str(r["id"]) for r in conn.execute(
                f"SELECT id FROM message WHERE session_id IN ({placeholders})",
                session_ids,
            ).fetchall()]

            if not msg_ids:
                tool_counts = {}
            else:
                part_placeholders = ",".join("?" for _ in msg_ids)
                parts = [dict(r) for r in conn.execute(
                    f"SELECT data FROM part WHERE message_id IN ({part_placeholders})",
                    msg_ids,
                ).fetchall()]

                tool_counts = Counter()
                for p in parts:
                    data = json.loads(p["data"]) if isinstance(p["data"], str) else p["data"]
                    tool_name = (data.get("tool") or "").strip()
                    if tool_name:
                        tool_counts[tool_name] += 1

            top_tools = dict(tool_counts.most_common(5))
            dominant_tool = top_tools.popitem()[0] if top_tools else "none"

            areas.append({
                "directory": directory,
                "session_count": len(session_ids),
                "dominant_tool": dominant_tool,
                "top_tools": dict(tool_counts.most_common(5)),
            })

        conn.close()

    except Exception as e:
        areas = []

    print(json.dumps({"areas": areas}, indent=2))


if __name__ == "__main__":
    main()
