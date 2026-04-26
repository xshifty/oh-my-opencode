#!/usr/bin/env python3
"""OpenCode Session Analyzer — reads the OpenCode database and gives back stats about your sessions.

Can output full analysis or just recent prompts. Results are JSON.

Usage:
  python3 session_analyzer.py                        — full analysis
  python3 session_analyzer.py --recent               — just recent prompts
  python3 session_analyzer.py /path/to/db.db         — specific database
  python3 session_analyzer.py --recent /path/to/db.db
"""

import json
import os
import sqlite3
import sys
from collections import defaultdict, Counter
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def find_db_path() -> str:
    """Find the OpenCode database file by checking common install locations."""
    candidates = [
        os.path.expanduser("~/.local/share/opencode/opencode.db"),
        os.path.join(os.environ.get("HOME", ""), ".local/share/opencode/opencode.db"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("OpenCode database not found. Check ~/.local/share/opencode/")


def get_db(db_path: str) -> sqlite3.Connection:
    """Open a connection to the OpenCode database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def fetch_sessions(conn: sqlite3.Connection, limit: int = 0) -> list[dict]:
    """Get all sessions from the database."""
    query = "SELECT * FROM session"
    if limit > 0:
        query += f" ORDER BY time_created DESC LIMIT {limit}"
    else:
        query += " ORDER BY time_created DESC"
    rows = conn.execute(query).fetchall()
    return [dict(r) for r in rows]


def fetch_messages(conn: sqlite3.Connection, session_ids: list[str]) -> list[dict]:
    """Get all messages for the given sessions."""
    if not session_ids:
        return []
    placeholders = ",".join("?" for _ in session_ids)
    query = f"""SELECT * FROM message WHERE session_id IN ({placeholders}) ORDER BY time_created"""
    rows = conn.execute(query, session_ids).fetchall()
    return [dict(r) for r in rows]


def fetch_parts(conn: sqlite3.Connection, message_ids: list[str]) -> list[dict]:
    """Get all parts (tool calls, text) for the given messages."""
    if not message_ids:
        return []
    placeholders = ",".join("?" for _ in message_ids)
    query = f"""SELECT * FROM part WHERE message_id IN ({placeholders}) ORDER BY time_created"""
    rows = conn.execute(query, message_ids).fetchall()
    return [dict(r) for r in rows]


def fetch_tool_parts(conn: sqlite3.Connection, message_ids: list[str]) -> list[dict]:
    """Get only tool-related parts for the given messages."""
    if not message_ids:
        return []
    placeholders = ",".join("?" for _ in message_ids)
    query = f"""SELECT * FROM part WHERE message_id IN ({placeholders}) AND json_extract(data, '$.type') = 'tool' ORDER BY time_created"""
    rows = conn.execute(query, message_ids).fetchall()
    return [dict(r) for r in rows]


def fetch_user_prompts(conn: sqlite3.Connection, session_ids: list[str]) -> list[dict]:
    """Get user messages with their text content for the given sessions."""
    if not session_ids:
        return []

    # Get user message IDs
    placeholders = ",".join("?" for _ in session_ids)
    msg_query = f"""SELECT id, session_id, time_created FROM message 
                    WHERE json_extract(data, '$.role') = 'user' AND session_id IN ({placeholders})
                    ORDER BY time_created"""
    user_msgs = conn.execute(msg_query, session_ids).fetchall()

    # Get text content for each message
    msg_ids = [str(r["id"]) for r in user_msgs]
    if not msg_ids:
        return []

    part_placeholders = ",".join("?" for _ in msg_ids)
    part_query = f"""SELECT * FROM part WHERE message_id IN ({part_placeholders}) AND json_extract(data, '$.type') = 'text'"""
    parts = conn.execute(part_query, msg_ids).fetchall()

    # Group parts by message ID
    prompts_by_msg = defaultdict(list)
    for p in parts:
        prompts_by_msg[str(p["message_id"])].append(dict(p))

    # Build the result list
    results = []
    for msg in user_msgs:
        msg_dict = dict(msg)
        msg_dict["content_parts"] = prompts_by_msg.get(str(msg["id"]), [])
        results.append(msg_dict)

    return results


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def analyze_sessions(conn: sqlite3.Connection, db_path: str | None = None) -> dict[str, Any]:
    """Run the full analysis and return all stats in one dict."""
    sessions = fetch_sessions(conn)
    if not sessions:
        return {"error": "No sessions found"}

    session_ids = [str(s["id"]) for s in sessions]
    messages = fetch_messages(conn, session_ids)
    message_ids = [str(m["id"]) for m in messages]
    parts = fetch_parts(conn, message_ids)
    tool_parts = fetch_tool_parts(conn, message_ids)
    user_prompts = fetch_user_prompts(conn, session_ids)

    analysis = {
        "db_path": db_path or find_db_path(),
        "total_sessions": len(sessions),
        "total_messages": len(messages),
        "total_parts": len(parts),
        "time_range": _calc_time_range(sessions),
        "sessions_by_directory": _group_by_directory(sessions),
        "tool_usage": _analyze_tools(tool_parts),
        "tool_errors": _analyze_tool_errors(tool_parts),
        "response_times": _analyze_response_times(messages, tool_parts),
        "multi_clauding": _detect_parallel_sessions(sessions),
        "time_of_day": _analyze_time_of_day(user_prompts),
        "user_prompts": user_prompts,
        "recent_prompt_analysis": analyze_recent_prompts(conn, 10),
        "session_details": [_enrich_session(s) for s in sessions],
    }

    return analysis


def _calc_time_range(sessions: list[dict]) -> dict:
    """Figure out the date range covered by the sessions."""
    if not sessions:
        return {}

    first = min(s["time_created"] for s in sessions) / 1000
    last = max(s["time_updated"] for s in sessions) / 1000

    start_date = datetime.fromtimestamp(first, tz=timezone.utc).strftime("%Y-%m-%d")
    end_date = datetime.fromtimestamp(last, tz=timezone.utc).strftime("%Y-%m-%d")

    days_span = (datetime.fromtimestamp(last, tz=timezone.utc) -
                 datetime.fromtimestamp(first, tz=timezone.utc)).days + 1

    return {
        "start_date": start_date,
        "end_date": end_date,
        "days_span": days_span,
    }


def _group_by_directory(sessions: list[dict]) -> dict[str, int]:
    """Count how many sessions were in each project folder."""
    counts = Counter()
    for s in sessions:
        directory = s.get("directory", "unknown") or "unknown"
        # Keep just the first 2 path parts for cleaner grouping
        if directory.startswith("/"):
            parts = directory.strip("/").split("/")[:2]
            if len(parts) > 0:
                directory = "/" + "/".join(parts)
        counts[directory] += 1

    return dict(counts.most_common(10))


def _analyze_tools(parts: list[dict]) -> dict[str, int]:
    """Count how many times each tool was used."""
    counts = Counter()
    for p in parts:
        data = json.loads(p["data"]) if isinstance(p["data"], str) else p["data"]
        tool_name = (data.get("tool") or "").strip()
        if tool_name:
            counts[tool_name] += 1

    return dict(counts.most_common(20))


def _analyze_tool_errors(parts: list[dict]) -> dict[str, int]:
    """Count how many errors each tool had."""
    counts = Counter()
    for p in parts:
        data = json.loads(p["data"]) if isinstance(p["data"], str) else p["data"]
        tool_name = (data.get("tool") or "").strip()
        state = data.get("state", {}) or {}
        status = (state.get("status") if isinstance(state, dict) else "") or ""
        if "error" in str(status).lower() and tool_name:
            counts[tool_name] += 1

    return dict(counts.most_common(10))


def _analyze_response_times(messages: list[dict], tool_parts: list[dict]) -> dict:
    """Measure how long the agent takes to reply to user messages."""
    user_times = []
    assistant_times = []

    for m in messages:
        data = json.loads(m["data"]) if isinstance(m["data"], str) else m["data"]
        role = data.get("role", "") or ""
        if role == "user":
            user_times.append(m["time_created"])
        elif role == "assistant":
            assistant_times.append(m["time_created"])

    user_times.sort()
    assistant_times.sort()

    # For each assistant reply, find the last user message before it
    intervals = []
    for at in assistant_times:
        prev_time = None
        for ut in reversed(user_times):
            if ut < at:
                prev_time = ut
                break
        if prev_time and prev_time > 0:
            interval_sec = (at - prev_time) / 1000
            intervals.append(interval_sec)

    # Sort into time buckets
    buckets = [
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
    for label, predicate in buckets:
        count = sum(1 for x in intervals if predicate(x))
        bucket_counts.append({"bucket": label, "count": count})

    max_count = max((b["count"] for b in bucket_counts), default=1) or 1
    sorted_intervals = sorted(intervals) if intervals else [0]
    median_val = sorted_intervals[len(sorted_intervals) // 2] if intervals else 0
    avg_val = sum(intervals) / len(intervals) if intervals else 0

    return {
        "buckets": [
            {**b, "width_percent": round((b["count"] / max_count) * 100, 2)}
            for b in bucket_counts
        ],
        "median_seconds": round(median_val, 1),
        "average_seconds": round(avg_val, 1),
        "total_intervals": len(intervals),
    }


def _detect_parallel_sessions(sessions: list[dict]) -> dict:
    """Find sessions that launched sub-agents (parallel sessions)."""
    child_count = 0
    parent_ids = set()

    for s in sessions:
        if s.get("parent_id"):
            child_count += 1
            parent_ids.add(s["parent_id"])

    # Sessions with children are parallel session parents
    parallel_parents = len(parent_ids)

    return {
        "total_parallel_events": child_count,
        "sessions_with_children": parallel_parents,
        "description": f"Found {child_count} sub-agent sessions from {parallel_parents} parent sessions",
    }


def _analyze_time_of_day(user_prompts: list[dict]) -> dict:
    """Check what time of day the user sends messages."""
    if not user_prompts:
        return {"periods": [], "median_hour": None}

    periods = {
        "Morning (6-12)": 0,
        "Afternoon (12-18)": 0,
        "Evening (18-24)": 0,
        "Night (0-6)": 0,
    }

    for prompt in user_prompts:
        hour = datetime.fromtimestamp(prompt["time_created"] / 1000, tz=timezone.utc).hour
        if 6 <= hour < 12:
            periods["Morning (6-12)"] += 1
        elif 12 <= hour < 18:
            periods["Afternoon (12-18)"] += 1
        elif 18 <= hour < 24:
            periods["Evening (18-24)"] += 1
        else:
            periods["Night (0-6)"] += 1

    total = sum(periods.values()) or 1
    max_count = max(periods.values()) or 1

    return {
        "periods": [
            {
                "label": label,
                "count": count,
                "width_percent": round((count / max_count) * 100, 2),
            }
            for label, count in periods.items()
        ],
        "total_messages": total,
    }


def _enrich_session(session: dict) -> dict:
    """Add computed fields (duration, date string, etc.) to a session."""
    created = datetime.fromtimestamp(session["time_created"] / 1000, tz=timezone.utc)
    updated = datetime.fromtimestamp(session["time_updated"] / 1000, tz=timezone.utc)

    duration_sec = (session["time_updated"] - session["time_created"]) / 1000

    return {
        **session,
        "created_iso": created.isoformat(),
        "duration_seconds": round(duration_sec, 1),
        "has_parent": bool(session.get("parent_id")),
        "files_changed": session.get("summary_files", 0),
    }


# ---------------------------------------------------------------------------
# Recent prompts
# ---------------------------------------------------------------------------

def fetch_recent_prompts(conn: sqlite3.Connection, limit: int = 10) -> list[dict]:
    """Get user prompts from the most recent N sessions with full text."""
    # Get the last N session IDs
    cur = conn.cursor()
    cur.execute("SELECT id FROM session ORDER BY time_created DESC LIMIT ?", (limit,))
    recent_session_ids = [row["id"] for row in cur.fetchall()]

    if not recent_session_ids:
        return []

    # Get user messages from those sessions
    placeholders = ",".join("?" for _ in recent_session_ids)
    msg_query = f"""SELECT id, session_id, time_created FROM message 
                    WHERE json_extract(data, '$.role') = 'user' AND session_id IN ({placeholders})
                    ORDER BY time_created ASC"""

    user_msgs = conn.execute(msg_query, recent_session_ids).fetchall()

    # Get text content for each message
    msg_ids = [str(r["id"]) for r in user_msgs]
    if not msg_ids:
        return []

    part_placeholders = ",".join("?" for _ in msg_ids)
    part_query = f"""SELECT * FROM part WHERE message_id IN ({part_placeholders}) AND json_extract(data, '$.type') = 'text'"""
    parts = conn.execute(part_query, msg_ids).fetchall()

    # Group parts by message ID
    prompts_by_msg = defaultdict(list)
    for p in parts:
        prompts_by_msg[str(p["message_id"])].append(dict(p))

    # Build the full prompt text for each message
    results = []
    for msg in user_msgs:
        msg_dict = dict(msg)

        text_content = ""
        for part_item in prompts_by_msg.get(str(msg["id"]), []):
            data = json.loads(part_item["data"]) if isinstance(part_item["data"], str) else part_item["data"]
            text_content += data.get("text", "")

        msg_dict["prompt_text"] = text_content.strip()
        msg_dict["prompt_length"] = len(text_content.strip())
        results.append(msg_dict)

    return results


def analyze_recent_prompts(conn: sqlite3.Connection, limit: int = 10) -> dict:
    """Look at prompts from recent sessions and find patterns (types, lengths)."""
    prompts = fetch_recent_prompts(conn, limit)

    if not prompts:
        return {"recent_sessions": [], "prompt_count": 0}

    # Get session IDs for reference
    cur = conn.cursor()
    cur.execute("SELECT id FROM session ORDER BY time_created DESC LIMIT ?", (limit,))
    recent_session_ids = [row["id"] for row in cur.fetchall()]

    # Set up categories and keywords
    categories = {
        "question": 0,
        "task": 0,
        "debugging": 0,
        "code_review": 0,
        "planning": 0,
        "other": 0,
    }

    keywords = {
        "question": ["what", "why", "how", "explain", "describe", "difference", "compare"],
        "task": ["create", "implement", "build", "add", "update", "modify", "generate", "write"],
        "debugging": ["fix", "error", "bug", "issue", "problem", "not working", "crash", "fail"],
        "code_review": ["review", "check", "analyze", "feedback", "improve", "refactor"],
        "planning": ["plan", "design", "architecture", "structure", "approach", "strategy"],
    }

    # Categorize each prompt
    for prompt in prompts:
        text = prompt.get("prompt_text", "").lower()

        matched = False
        for cat, words in keywords.items():
            if any(word in text for word in words):
                categories[cat] += 1
                matched = True
                break

        if not matched:
            categories["other"] += 1

    # Calculate statistics
    lengths = [p.get("prompt_length", 0) for p in prompts]
    avg_length = sum(lengths) / len(lengths) if lengths else 0

    longest = max(prompts, key=lambda p: p.get("prompt_length", 0)) if prompts else None
    shortest = min(prompts, key=lambda p: p.get("prompt_length", 0)) if prompts else None

    return {
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


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    """Run the analyzer from the command line."""
    db_path = None
    recent_only = False

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--recent":
            recent_only = True
        else:
            db_path = arg

    try:
        db_path = db_path or find_db_path()
        conn = get_db(db_path)

        if recent_only:
            result = analyze_recent_prompts(conn, 10)
        else:
            result = analyze_sessions(conn, db_path)

        print(json.dumps(result, indent=2, default=str))

        conn.close()
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
