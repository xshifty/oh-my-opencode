#!/usr/bin/env python3
"""Look at prompts from recent sessions and find patterns.

Groups prompts by type (question, task, debugging, etc.) and shows
length stats. Useful for seeing how the user talks to the agent.

Output JSON: categories, avg_length, longest_prompt, shortest_prompt, prompts_sample

Usage:
  python3 get_prompt_analysis.py                        — last 10 sessions
  python3 get_prompt_analysis.py /path/to/db.db         — specific database
  python3 get_prompt_analysis.py --count 5              — last 5 sessions
"""

import json
import sys
from collections import defaultdict

from shared import find_db_path, get_db


# These are the categories we sort prompts into
CATEGORIES = {
    "question": 0,
    "task": 0,
    "debugging": 0,
    "code_review": 0,
    "planning": 0,
    "other": 0,
}

# Keywords that tell us what type of prompt it is
KEYWORDS = {
    "question": ["what", "why", "how", "explain", "describe", "difference", "compare"],
    "task": ["create", "implement", "build", "add", "update", "modify", "generate", "write"],
    "debugging": ["fix", "error", "bug", "issue", "problem", "not working", "crash", "fail"],
    "code_review": ["review", "check", "analyze", "feedback", "improve", "refactor"],
    "planning": ["plan", "design", "architecture", "structure", "approach", "strategy"],
}


def parse_args():
    """Read command line arguments. Returns (db_path, session_limit)."""
    db_path = None
    limit = 10
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.startswith("--count"):
            if "=" in arg:
                try:
                    limit = int(arg.split("=")[1])
                except (IndexError, ValueError):
                    limit = 10
            elif i + 1 < len(sys.argv):
                try:
                    limit = int(sys.argv[i + 1])
                    i += 1
                except (IndexError, ValueError):
                    limit = 10
        elif arg.startswith("--"):
            pass
        elif db_path is None:
            db_path = arg
        i += 1
    return db_path, limit


def main():
    db_path, limit = parse_args()

    try:
        db_path = db_path or find_db_path()
        conn = get_db(db_path)

        # Get the most recent N session IDs
        cur = conn.cursor()
        cur.execute("SELECT id FROM session ORDER BY time_created DESC LIMIT ?", (limit,))
        recent_session_ids = [row["id"] for row in cur.fetchall()]

        if not recent_session_ids:
            conn.close()
            print(json.dumps({"categories": CATEGORIES, "prompt_count": 0}, indent=2))
            return

        # Get user messages from those sessions
        placeholders = ",".join("?" for _ in recent_session_ids)
        msg_query = f"""SELECT id, session_id, time_created FROM message
                        WHERE json_extract(data, '$.role') = 'user' AND session_id IN ({placeholders})
                        ORDER BY time_created ASC"""
        user_msgs = conn.execute(msg_query, recent_session_ids).fetchall()

        if not user_msgs:
            conn.close()
            print(json.dumps({"categories": CATEGORIES, "prompt_count": 0}, indent=2))
            return

        # Get the text content of each user message
        msg_ids = [str(r["id"]) for r in user_msgs]
        part_placeholders = ",".join("?" for _ in msg_ids)
        part_query = f"""SELECT * FROM part WHERE message_id IN ({part_placeholders}) AND json_extract(data, '$.type') = 'text'"""
        parts = conn.execute(part_query, msg_ids).fetchall()

        # Group parts by message ID
        prompts_by_msg = defaultdict(list)
        for p in parts:
            prompts_by_msg[str(p["message_id"])].append(dict(p))

        # Build a list of prompts with their text content
        prompts = []
        for msg in user_msgs:
            msg_dict = dict(msg)
            text_content = ""
            for part_item in prompts_by_msg.get(str(msg["id"]), []):
                data = json.loads(part_item["data"]) if isinstance(part_item["data"], str) else part_item["data"]
                text_content += data.get("text", "")

            msg_dict["prompt_text"] = text_content.strip()
            msg_dict["prompt_length"] = len(text_content.strip())
            prompts.append(msg_dict)

        # Sort each prompt into a category
        categories = dict(CATEGORIES)
        for prompt in prompts:
            text = prompt.get("prompt_text", "").lower()
            matched = False
            for cat, words in KEYWORDS.items():
                if any(word in text for word in words):
                    categories[cat] += 1
                    matched = True
                    break
            if not matched:
                categories["other"] += 1

        # Calculate length stats
        lengths = [p.get("prompt_length", 0) for p in prompts]
        avg_length = sum(lengths) / len(lengths) if lengths else 0
        longest = max(prompts, key=lambda p: p.get("prompt_length", 0)) if prompts else None
        shortest = min(prompts, key=lambda p: p.get("prompt_length", 0)) if prompts else None

        conn.close()

        result = {
            "recent_sessions": recent_session_ids[:limit],
            "prompt_count": len(prompts),
            "categories": categories,
            "avg_prompt_length": round(avg_length, 1),
            "longest_prompt": {
                "text": longest.get("prompt_text", "")[:200] if longest else "",
                "length": longest.get("prompt_length", 0) if longest else 0,
            },
            "shortest_prompt": {
                "text": shortest.get("prompt_text", "")[:100] if shortest else "",
                "length": shortest.get("prompt_length", 0) if shortest else 0,
            },
            "prompts_sample": [
                {
                    "session_id": p["session_id"],
                    "time_created": p["time_created"],
                    "text_preview": p.get("prompt_text", "")[:150],
                }
                for p in prompts[:20]
            ],
        }

    except Exception as e:
        result = {"error": str(e)}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
