#!/usr/bin/env python3
"""Get overall session statistics."""
import sqlite3, json, sys
from datetime import datetime

db_path = sys.argv[1] if len(sys.argv) > 1 else ""
if db_path == "":
    print(json.dumps({"error": "No database path provided"}))
    sys.exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get sessions count and date range (time_created is epoch ms)
cur.execute("""
    SELECT COUNT(*), MIN(time_created), MAX(time_created)
    FROM session WHERE time_created IS NOT NULL
""")
row = cur.fetchone()
total_sessions = row[0] or 0
min_ts = row[1] if row[1] else 0
max_ts = row[2] if row[2] else 0

# Calculate days span from epoch ms
days_span = 1
if min_ts > 0 and max_ts > 0:
    d1 = datetime.fromtimestamp(min_ts / 1000)
    d2 = datetime.fromtimestamp(max_ts / 1000)
    days_span = max(1, (d2 - d1).days)

# Get total messages
cur.execute("SELECT COUNT(*) FROM message")
total_messages = cur.fetchone()[0] or 0



# Get unique directories
cur.execute("""
    SELECT COUNT(DISTINCT directory) FROM session WHERE directory IS NOT NULL AND directory != ''
""")
unique_dirs = cur.fetchone()[0] or 0

result = {
    "total_sessions": total_sessions,
    "total_messages": total_messages,
    "min_date": datetime.fromtimestamp(min_ts / 1000).strftime("%Y-%m-%d") if min_ts > 0 else "",
    "max_date": datetime.fromtimestamp(max_ts / 1000).strftime("%Y-%m-%d") if max_ts > 0 else "",
    "days_span": days_span,
    "unique_directories": unique_dirs,
    "messages_per_day": round(total_messages / days_span) if total_messages > 0 and days_span > 0 else 0
}

conn.close()
print(json.dumps(result))
