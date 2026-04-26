#!/usr/bin/env python3
"""Find sessions that used multiple agents running at the same time.

Checks for parent-child session relationships. When the main agent
launches sub-agents, those child sessions have a parent_id.

Output JSON: total_parallel_events, sessions_with_children, parent_sessions, child_sessions

Usage:
  python3 get_multi_agent.py                    — find the database automatically
  python3 get_multi_agent.py /path/to/db.db     — use a specific database file
"""

import json
import sys

from shared import find_db_path, get_db


def main():
    db_path = None
    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    try:
        db_path = db_path or find_db_path()
        conn = get_db(db_path)

        # Get all sessions with parent_id info
        sessions = [dict(r) for r in conn.execute(
            "SELECT id, parent_id, time_created FROM session"
        ).fetchall()]

        child_sessions = []
        parent_ids = set()

        for s in sessions:
            if s.get("parent_id"):
                child_sessions.append({
                    "id": str(s["id"]),
                    "parent_id": s["parent_id"],
                    "time_created": s["time_created"],
                })
                parent_ids.add(s["parent_id"])

        # Get message counts for parent sessions
        if parent_ids:
            placeholders = ",".join("?" for _ in parent_ids)
            parents_data = conn.execute(
                f"SELECT id, COUNT(*) as msg_count FROM message WHERE session_id IN ({placeholders}) GROUP BY session_id",
                list(parent_ids),
            ).fetchall()
            parent_sessions = [{"id": str(r["id"]), "message_count": r["msg_count"]} for r in parents_data]
        else:
            parent_sessions = []

        conn.close()

        result = {
            "total_parallel_events": len(child_sessions),
            "sessions_with_children": len(parent_ids),
            "parent_sessions": sorted(parent_sessions, key=lambda x: -x["message_count"]),
            "child_sessions": child_sessions[:50],  # limit output to 50 entries
        }

    except Exception as e:
        result = {"error": str(e)}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
