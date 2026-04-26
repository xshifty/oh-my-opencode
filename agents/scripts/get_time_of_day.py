#!/usr/bin/env python3
"""See when the user sends messages — morning, afternoon, evening, or night.

Output JSON: periods array (label, count, width_percent), total_messages, peak_hour

Usage:
  python3 get_time_of_day.py                    — find the database automatically
  python3 get_time_of_day.py /path/to/db.db     — use a specific database file
"""

import json
import sys
from collections import Counter
from datetime import datetime, timezone

from shared import find_db_path, get_db


def main():
    db_path = None
    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    try:
        db_path = db_path or find_db_path()
        conn = get_db(db_path)

        # Get all user messages with their timestamps
        user_msgs = [dict(r) for r in conn.execute(
            "SELECT id, time_created FROM message WHERE json_extract(data, '$.role') = 'user' ORDER BY time_created"
        ).fetchall()]

        if not user_msgs:
            conn.close()
            print(json.dumps({"periods": [], "total_messages": 0}, indent=2))
            return

        # Group messages into time periods
        periods = {
            "Morning (6-12)": 0,
            "Afternoon (12-18)": 0,
            "Evening (18-24)": 0,
            "Night (0-6)": 0,
        }
        hourly_counts = Counter()

        for m in user_msgs:
            hour = datetime.fromtimestamp(m["time_created"] / 1000, tz=timezone.utc).hour
            if 6 <= hour < 12:
                periods["Morning (6-12)"] += 1
            elif 12 <= hour < 18:
                periods["Afternoon (12-18)"] += 1
            elif 18 <= hour < 24:
                periods["Evening (18-24)"] += 1
            else:
                periods["Night (0-6)"] += 1

            hourly_counts[hour] += 1

        total = sum(periods.values()) or 1
        max_count = max(periods.values()) or 1
        peak_hour = hourly_counts.most_common(1)[0][0] if hourly_counts else None

        conn.close()

        result = {
            "periods": [
                {"label": label, "count": count, "width_percent": round((count / max_count) * 100, 2)}
                for label, count in periods.items()
            ],
            "total_messages": total,
            "peak_hour": peak_hour,
        }

    except Exception as e:
        result = {"error": str(e)}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
