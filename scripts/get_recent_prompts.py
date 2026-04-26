#!/usr/bin/env python3
"""Get recent sessions' user prompts for analysis."""
import sqlite3, json, sys

db_path = ""
count = 10

# Parse args: support both --count N and positional
args = sys.argv[1:]
i = 0
while i < len(args):
    if args[i] == '--count' and i + 1 < len(args):
        count = int(args[i+1])
        i += 2
    elif not args[i].startswith('--') and db_path == "":
        db_path = args[i]
        i += 1
    else:
        i += 1

if db_path == "":
    print(json.dumps({"error": "No database path provided"}))
    sys.exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get recent sessions with their user prompts (parts of type='text')
cur.execute("""
    SELECT id, directory, slug, time_created FROM session 
    WHERE time_created IS NOT NULL
    ORDER BY time_created DESC LIMIT ?
""", (count,))

sessions = cur.fetchall()
prompts_data = []

for sid, directory, slug, start_time in sessions:
    # Get text parts for this session (user messages are type='text')
    cur.execute("""SELECT data FROM part WHERE session_id = ? AND data IS NOT NULL ORDER BY time_created ASC""", (sid,))
    
    user_msgs = []
    total_user_chars = 0
    
    for row in cur.fetchall():
        if not isinstance(row[0], str):
            continue
        try:
            obj = json.loads(row[0])
            if obj.get('type') == 'text':
                text = obj.get('text', '')
                if len(text) > 10:  # Skip very short messages
                    total_user_chars += len(text)
                    preview = text[:200].replace('\n', ' ').strip()
                    user_msgs.append({
                        "preview": preview,
                        "length": len(text)
                    })
        except:
            continue
    
    prompts_data.append({
        "session_id": sid[:8],
        "slug": slug or "",
        "directory": directory or "",
        "start_time": start_time if isinstance(start_time, int) else 0,
        "messages": user_msgs[:5],  # top 5 messages per session
        "avg_prompt_length": round(total_user_chars / max(len(user_msgs), 1)),
        "total_prompts": len(user_msgs)
    })

conn.close()
print(json.dumps({"sessions": prompts_data}, indent=2))
