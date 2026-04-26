#!/usr/bin/env python3
"""Get model usage counts from messages."""
import sqlite3, json, sys

db_path = sys.argv[1] if len(sys.argv) > 1 else ""
if db_path == "":
    print(json.dumps({"error": "No database path provided"}))
    sys.exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Extract model usage from message data
cur.execute("""SELECT id, session_id, data FROM message WHERE data IS NOT NULL""")

model_counts = {}
total_model_calls = 0

for row in cur.fetchall():
    mid, sid, data = row
    if not isinstance(data, str):
        continue
    
    try:
        obj = json.loads(data)
        
        # Get model from various possible fields
        model = obj.get('model', '') or obj.get('modelID', '') or ''
        
        if model and isinstance(model, str):
            total_model_calls += 1
            model_counts[model] = model_counts.get(model, 0) + 1
            
    except:
        continue

# Build results sorted by count descending
models = []
for name, count in sorted(model_counts.items(), key=lambda x: -x[1]):
    models.append({
        "name": name,
        "count": count,
        "percentage": round(count / total_model_calls * 100, 1) if total_model_calls > 0 else 0
    })

# Get top models by percentage for chart display
top_models = sorted(models, key=lambda x: -x["count"])[:15]

result = {
    "total_model_calls": total_model_calls,
    "unique_models": len(model_counts),
    "models": models,
    "top_models": top_models
}

conn.close()
print(json.dumps(result))
