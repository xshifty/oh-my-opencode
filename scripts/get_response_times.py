#!/usr/bin/env python3
"""Get response time distribution from parts data."""
import sqlite3, json, sys, math
from collections import Counter

db_path = sys.argv[1] if len(sys.argv) > 1 else ""
if db_path == "":
    print(json.dumps({"error": "No database path provided"}))
    sys.exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get parts ordered by session and time_created
cur.execute("""SELECT id, session_id, data FROM part WHERE data IS NOT NULL ORDER BY session_id, time_created""")

rows = cur.fetchall()
intervals = []
buckets = Counter({"0-5s": 0, "5-15s": 0, "15-30s": 0, "30-60s": 0, "1-3m": 0, "3-10m": 0, "10m+": 0})

prev_ts = {}
for pid, sid, data in rows:
    if not isinstance(data, str):
        continue
    
    try:
        obj = json.loads(data)
        
        # Look for step-start or tool calls with timing info
        ts = None
        if 'time' in obj and isinstance(obj['time'], dict):
            start_ms = obj['time'].get('start', 0)
            end_ms = obj['time'].get('end', 0)
            if start_ms > 0:
                ts = start_ms
        
        # Also check step-finish for timing
        if ts is None and 'time' in obj and isinstance(obj.get('time'), dict):
            pass
            
    except:
        continue

# Alternative approach: use message time_created as proxy
cur.execute("""SELECT session_id, time_created FROM message ORDER BY session_id, time_created""")
msg_rows = cur.fetchall()

prev_session = None
prev_msg_ts = 0
for sid, ts in msg_rows:
    if sid == prev_session and prev_msg_ts > 0:
        diff_ms = ts - prev_msg_ts
        diff_s = diff_ms / 1000.0
        
        if diff_s < 5: buckets["0-5s"] += 1
        elif diff_s < 15: buckets["5-15s"] += 1
        elif diff_s < 30: buckets["15-30s"] += 1
        elif diff_s < 60: buckets["30-60s"] += 1
        elif diff_s < 180: buckets["1-3m"] += 1
        elif diff_s < 600: buckets["3-10m"] += 1
        else: buckets["10m+"] += 1
    
    prev_session = sid
    prev_msg_ts = ts

# Calculate stats from buckets (approximate)
total_in_buckets = sum(buckets.values())
if total_in_buckets > 0:
    # Estimate median/average from bucket distribution
    sorted_intervals = []
    for bucket_name, count in buckets.items():
        if '0-5' in bucket_name: mid = 2.5
        elif '5-15' in bucket_name: mid = 10
        elif '15-30' in bucket_name: mid = 22.5
        elif '30-60' in bucket_name: mid = 45
        elif '1-3m' in bucket_name: mid = 120
        elif '3-10m' in bucket_name: mid = 450
        else: mid = 900
        
        sorted_intervals.extend([mid] * count)
    
    if sorted_intervals:
        sorted_intervals.sort()
        median = sorted_intervals[len(sorted_intervals) // 2]
        avg = sum(sorted_intervals) / len(sorted_intervals)
        p90_idx = int(len(sorted_intervals) * 0.9)
        p95_idx = int(len(sorted_intervals) * 0.95)
        p90 = sorted_intervals[min(p90_idx, len(sorted_intervals)-1)]
        p95 = sorted_intervals[min(p95_idx, len(sorted_intervals)-1)]
    else:
        median = avg = p90 = p95 = 0
else:
    median = avg = p90 = p95 = 0

conn.close()
print(json.dumps({
    "intervals_count": total_in_buckets,
    "median_seconds": round(median, 1),
    "average_seconds": round(avg, 1),
    "p90_seconds": round(p90, 1),
    "p95_seconds": round(p95, 1),
    "buckets": dict(buckets)
}, indent=2))
