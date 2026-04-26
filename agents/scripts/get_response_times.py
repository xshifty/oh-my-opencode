#!/usr/bin/env python3
"""Measure how fast the agent replies to user messages.

Groups response times into buckets (under 5s, 5-10s, etc.) for the dashboard.

Output JSON: buckets array, median_seconds, average_seconds, total_intervals

Usage:
  python3 get_response_times.py                    — find the database automatically
  python3 get_response_times.py /path/to/db.db     — use a specific database file
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

        # Get user messages sorted by time
        user_msgs = [dict(r) for r in conn.execute(
            "SELECT id, time_created FROM message WHERE json_extract(data, '$.role') = 'user' ORDER BY time_created"
        ).fetchall()]

        # Get assistant messages sorted by time
        assistant_msgs = [dict(r) for r in conn.execute(
            "SELECT id, time_created FROM message WHERE json_extract(data, '$.role') = 'assistant' ORDER BY time_created"
        ).fetchall()]

        # For each assistant reply, find the user message that came right before it
        user_times = [m["time_created"] for m in user_msgs]
        intervals = []

        for am in assistant_msgs:
            prev_time = None
            for t in reversed(user_times):
                if t < am["time_created"]:
                    prev_time = t
                    break
            if prev_time and prev_time > 0:
                interval_sec = (am["time_created"] - prev_time) / 1000
                intervals.append(interval_sec)

        # Sort intervals into buckets
        bucket_defs = [
            ("Under 5s", lambda x: x < 5),
            ("5-10s", lambda x: 5 <= x < 10),
            ("10-30s", lambda x: 10 <= x < 30),
            ("30s-1m", lambda x: 30 <= x < 60),
            ("1-2m", lambda x: 60 <= x < 120),
            ("2-5m", lambda x: 120 <= x < 300),
            ("5-15m", lambda x: 300 <= x < 900),
            (">15m", lambda x: x >= 900),
        ]

        bucket_counts = []
        for label, predicate in bucket_defs:
            count = sum(1 for x in intervals if predicate(x))
            bucket_counts.append({"bucket": label, "count": count})

        max_count = max((b["count"] for b in bucket_counts), default=1) or 1
        sorted_intervals = sorted(intervals) if intervals else [0]
        median_val = sorted_intervals[len(sorted_intervals) // 2]
        avg_val = sum(intervals) / len(intervals) if intervals else 0

        conn.close()

        result = {
            "buckets": [
                {**b, "width_percent": round((b["count"] / max_count) * 100, 2)}
                for b in bucket_counts
            ],
            "median_seconds": round(median_val, 1),
            "average_seconds": round(avg_val, 1),
            "total_intervals": len(intervals),
        }

    except Exception as e:
        result = {"error": str(e)}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
