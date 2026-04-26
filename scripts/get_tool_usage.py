#!/usr/bin/env python3
"""Get tool usage counts and error rates from parts data."""
import sqlite3, json, sys

db_path = sys.argv[1] if len(sys.argv) > 1 else ""
if db_path == "":
    print(json.dumps({"error": "No database path provided"}))
    sys.exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Extract tool calls from parts JSON data
cur.execute("""SELECT id, session_id, data FROM part WHERE data IS NOT NULL""")

tool_counts = {}
error_counts = {}
total_calls = 0

for row in cur.fetchall():
    sid, data = row[1], row[2]
    if not isinstance(data, str):
        continue
    
    try:
        obj = json.loads(data)
        
        # Check for tool calls (type='tool')
        if obj.get('type') == 'tool':
            tool_name = obj.get('tool', '')
            state = obj.get('state', {})
            
            if tool_name:
                total_calls += 1
                tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
                
                # Check for errors
                status = state.get('status', '')
                if status == 'error':
                    error_counts[tool_name] = error_counts.get(tool_name, 0) + 1
                    
        # Also check for step-finish with tool-calls reason (contains multiple tools)
        elif obj.get('type') == 'step-finish' and obj.get('reason') == 'tool-calls':
            pass
            
    except:
        continue

# Build results
tools = []
for name, count in sorted(tool_counts.items(), key=lambda x: -x[1]):
    errors = error_counts.get(name, 0)
    tools.append({
        "name": name,
        "count": count,
        "errors": errors,
        "error_rate": round(errors / count * 100, 1) if count > 0 else 0
    })

result = {
    "total_tool_calls": total_calls,
    "tools": tools[:20],
    "top_tools_by_count": [t["name"] for t in sorted(tools, key=lambda x: -x["count"])[:10]],
    "highest_error_rates": sorted(
        [t for t in tools if t["errors"] > 0],
        key=lambda x: -x["error_rate"]
    )[:5]
}

conn.close()
print(json.dumps(result))
