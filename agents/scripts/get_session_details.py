#!/usr/bin/env python3
"""Get full details for every session, including duration and parent info.

Output JSON: sessions array (id, directory, time_created, time_updated,
duration_seconds, has_parent, files_changed, created_iso), total_sessions

Usage:
  python3 get_session_details.py                    — find the database automatically
  python3 get_session_details.py /path/to/db.db     — use a specific database file
"""

import json
import sys
from datetime import datetime, timezone

from shared import find_db_path, get_db


def main():
    db_path = None
    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    try:
        db_path = db_path or find_db_path()
        conn = get_db(db_path)

        sessions = [dict(r) for r in conn.execute(
            "SELECT id, directory, time_created, time_updated, parent_id, summary_files FROM session ORDER BY time_created DESC"
        ).fetchall()]

        enriched = []
        for s in sessions:
            created = datetime.fromtimestamp(s["time_created"] / 1000, tz=timezone.utc)
            updated = datetime.fromtimestamp(s["time_updated"] / 1000, tz=timezone.utc)
            duration_sec = (s["time_updated"] - s["time_created"]) / 1000

            enriched.append({
                "id": str(s["id"]),
                "directory": s.get("directory") or "unknown",
                "time_created": s["time_created"],
                "time_updated": s["time_updated"],
                "created_iso": created.isoformat(),
                "duration_seconds": round(duration_sec, 1),
                "has_parent": bool(s.get("parent_id")),
                "files_changed": s.get("summary_files", 0),
            })

        conn.close()

        result = {
            "sessions": enriched,
            "total_sessions": len(enriched),
        }

    except Exception as e:
        result = {"error": str(e)}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
