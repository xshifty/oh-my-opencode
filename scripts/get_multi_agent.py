#!/usr/bin/env python3
"""Detect multi-agent (parallel subagent) sessions."""
import sqlite3, json, sys

db_path = sys.argv[1] if len(sys.argv) > 1 else ""
if db_path == "":
    print(json.dumps({"error": "No database path provided"}))
    sys.exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Look for sessions with parent_id (subagent sessions) or title containing @
cur.execute("""SELECT id, slug, directory, title, time_created FROM session WHERE parent_id IS NOT NULL OR title LIKE '%@%'""")

sessions = []
total_subagents = 0
for row in cur.fetchall():
    sid, slug, directory, title, ts = row
    
    # Check if it's a subagent (has parent) or a parent that spawned agents
    is_parent = '@' in str(title or '')
    
    sessions.append({
        "session_id": sid[:8],
        "slug": slug,
        "title": title[:50] if title else "",
        "is_parent": is_parent,
        "has_parent": bool(parent_id) if (parent_id := row[4]) else False  # wrong index
    })

# Better approach: count sessions with parent_id != null as subagents
cur.execute("SELECT COUNT(*) FROM session WHERE parent_id IS NOT NULL")
subagent_count = cur.fetchone()[0] or 0

# Count parent sessions (sessions that have children)
cur.execute("""SELECT COUNT(DISTINCT parent_id) FROM session WHERE parent_id IS NOT NULL""")
parent_count = cur.fetchone()[0] or 0

# Also check for task/agent tool calls in parts
cur.execute("SELECT data FROM part WHERE data IS NOT NULL")
task_calls = 0
for row in cur.fetchall():
    if isinstance(row[0], str):
        try:
            obj = json.loads(row[0])
            if obj.get('type') == 'tool' and obj.get('tool') in ('task', 'Task'):
                task_calls += 1
        except:
            pass

# Get total sessions for percentage
cur.execute("SELECT COUNT(*) FROM session")
total = cur.fetchone()[0] or 1

result = {
    "total_parallel_events": subagent_count,
    "parent_sessions_count": parent_count,
    "task_tool_calls": task_calls,
    "sessions_percentage": round(parent_count / max(total, 1) * 100, 1),
    "subagent_count": subagent_count
}

conn.close()
print(json.dumps(result))
