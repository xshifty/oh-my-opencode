#!/usr/bin/env python3
"""Get high-level session statistics from the OpenCode database.

Output JSON: total_sessions, total_messages, time_range (start/end dates, days),
total_parts, messages_per_session average.

Usage:
  python3 get_overall_stats.py                    — find the database automatically
  python3 get_overall_stats.py /path/to/db.db     — use a specific database file
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

        # Count total sessions
        total_sessions = conn.execute("SELECT COUNT(*) FROM session").fetchone()[0]

        # Count messages by role
        user_msgs = conn.execute(
            "SELECT COUNT(*) FROM message WHERE json_extract(data, '$.role') = 'user'"
        ).fetchone()[0]
        assistant_msgs = conn.execute(
            "SELECT COUNT(*) FROM message WHERE json_extract(data, '$.role') = 'assistant'"
        ).fetchone()[0]

        # Count total parts
        total_parts = conn.execute("SELECT COUNT(*) FROM part").fetchone()[0]

        # Find earliest and latest activity timestamps
        first_row = conn.execute(
            "SELECT MIN(time_created), MAX(time_updated) FROM session"
        ).fetchone()
        min_time, max_time = first_row[0], first_row[1]

        start_date = datetime.fromtimestamp(min_time / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        end_date = datetime.fromtimestamp(max_time / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        days_span = (
            datetime.fromtimestamp(max_time / 1000, tz=timezone.utc) -
            datetime.fromtimestamp(min_time / 1000, tz=timezone.utc)
        ).days + 1

        result = {
            "total_sessions": total_sessions,
            "total_messages": user_msgs + assistant_msgs,
            "user_messages": user_msgs,
            "assistant_messages": assistant_msgs,
            "total_parts": total_parts,
            "messages_per_session": round((user_msgs + assistant_msgs) / max(total_sessions, 1), 1),
            "time_range": {
                "start_date": start_date,
                "end_date": end_date,
                "days_span": days_span,
            },
        }

        conn.close()
    except Exception as e:
        result = {"error": str(e)}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
