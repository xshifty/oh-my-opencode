#!/usr/bin/env python3
"""Get activity by time of day."""
import sqlite3, json, sys
from collections import Counter

db_path = sys.argv[1] if len(sys.argv) > 1 else ""
if db_path == "":
    print(json.dumps({"error": "No database path provided"}))
    sys.exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get user messages (parts with type='text' from sessions)
cur.execute("""SELECT session_id, time_created FROM part WHERE data IS NOT NULL AND time_created IS NOT NULL""")

buckets = Counter({"Morning (6-12)": 0, "Afternoon (12-18)": 0, "Evening (18-24)": 0, "Night (0-6)": 0})
total_count = 0

for row in cur.fetchall():
    sid, ts_ms = row[0], row[1]
    if not isinstance(ts_ms, (int, float)) or ts_ms == 0:
        continue
    
    # Convert epoch ms to hour
    from datetime import datetime as dt
    t = dt.fromtimestamp(ts_ms / 1000)
    hour = t.hour
    
    total_count += 1
    
    if 6 <= hour < 12: buckets["Morning (6-12)"] += 1
    elif 12 <= hour < 18: buckets["Afternoon (12-18)"] += 1
    elif 18 <= hour < 24: buckets["Evening (18-24)"] += 1
    else: buckets["Night (0-6)"] += 1

conn.close()
print(json.dumps({"buckets": dict(buckets), "total_messages": total_count}, indent=2))
