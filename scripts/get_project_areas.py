#!/usr/bin/env python3
"""Get activity by project directory with tool usage patterns."""
import sqlite3, json, sys

db_path = sys.argv[1] if len(sys.argv) > 1 else ""
if db_path == "":
    print(json.dumps({"error": "No database path provided"}))
    sys.exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get sessions grouped by directory (top 15)
cur.execute("""
    SELECT directory, COUNT(*) as session_count
    FROM session
    WHERE directory IS NOT NULL AND directory != ''
    GROUP BY directory
    ORDER BY session_count DESC
""")

dirs = cur.fetchall()

areas = []
for dir_name, count in dirs[:15]:  # top 15 directories
    # Get all session IDs for this directory
    cur.execute("SELECT id FROM session WHERE directory = ? LIMIT ?", (dir_name, count))
    sids = [r[0] for r in cur.fetchall()]
    
    tool_counts = {}
    read_count = 0
    write_count = 0
    bash_count = 0
    
    # Build a single query with all session IDs
    if not sids:
        areas.append({
            "directory": dir_name,
            "session_count": count,
            "tools": {},
            "pattern": "unknown",
            "read_heavy": 0,
            "write_heavy": 0,
            "bash_heheavy": 0
        })
        continue
    
    placeholders = ','.join(['?' for _ in sids])
    query = f"SELECT data FROM part WHERE session_id IN ({placeholders}) AND data IS NOT NULL"
    
    try:
        cur.execute(query, sids)
        
        for row in cur.fetchall():
            if not isinstance(row[0], str):
                continue
            try:
                obj = json.loads(row[0])
                if obj.get('type') == 'tool':
                    tool_name = obj.get('tool', '')
                    if tool_name:
                        tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
                        
                        # Categorize tools
                        t = tool_name.lower()
                        if t in ('read',): read_count += 1
                        elif t in ('write', 'Write'): write_count += 1
                        elif t in ('bash', 'Bash'): bash_count += 1
            except:
                continue
    except Exception as e:
        print(f"Warning: Error processing {dir_name}: {e}", file=sys.stderr)
    
    # Determine dominant pattern
    total = sum(tool_counts.values())
    if total == 0:
        pattern = "unknown"
    elif read_count > write_count and read_count > bash_count:
        pattern = "exploration"
    elif write_count + (total - read_count - bash_count) > bash_count:
        pattern = "implementation"
    else:
        pattern = "scripting"
    
    areas.append({
        "directory": dir_name,
        "session_count": count,
        "tools": {k: v for k, v in sorted(tool_counts.items(), key=lambda x: -x[1])[:5]},
        "pattern": pattern,
        "read_heavy": read_count,
        "write_heavy": write_count,
        "bash_heavy": bash_count
    })

conn.close()
print(json.dumps({"areas": areas}, indent=2))
