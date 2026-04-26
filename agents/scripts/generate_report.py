#!/usr/bin/env python3
"""Generate the OpenCode insights report — a complete HTML dashboard.

This is the main script. It:
- Collects all session data from the database
- Creates text summaries from your usage patterns
- Fills the insights.html template
- Saves the dashboard file

Usage:
  python3 generate_report.py                          — find the database automatically
  python3 generate_report.py /path/to/db.db           — use a specific database file
  python3 generate_report.py --out /path/to/output.html
"""

import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared import find_db_path, get_db, parse_part_data, build_placeholders


# ---------------------------------------------------------------------------
# Data collection functions
# ---------------------------------------------------------------------------

def get_overall_stats(conn):
    """Get high-level numbers — total sessions, messages, date range, etc."""
    total_sessions = conn.execute("SELECT COUNT(*) FROM session").fetchone()[0]
    user_msgs = conn.execute(
        "SELECT COUNT(*) FROM message WHERE json_extract(data, '$.role') = 'user'"
    ).fetchone()[0]
    assistant_msgs = conn.execute(
        "SELECT COUNT(*) FROM message WHERE json_extract(data, '$.role') = 'assistant'"
    ).fetchone()[0]
    total_msgs = user_msgs + assistant_msgs
    row = conn.execute("SELECT MIN(time_created), MAX(time_updated) FROM session").fetchone()
    min_t, max_t = row[0], row[1]
    start = datetime.fromtimestamp(min_t / 1000, tz=timezone.utc)
    end = datetime.fromtimestamp(max_t / 1000, tz=timezone.utc)
    days = (end - start).days + 1
    return {
        "total_sessions": total_sessions,
        "total_messages": total_msgs,
        "user_messages": user_msgs,
        "assistant_messages": assistant_msgs,
        "start_date": start.strftime("%b %d, %Y"),
        "end_date": end.strftime("%b %d, %Y"),
        "days_span": days,
        "msgs_per_session": round(total_msgs / max(total_sessions, 1), 1),
        "msgs_per_day": round(total_msgs / max(days, 1)),
    }


def get_tool_usage(conn):
    """Count tool usage and errors from the part table."""
    parts = conn.execute(
        "SELECT data FROM part WHERE json_extract(data, '$.type') = 'tool'"
    ).fetchall()
    usage = Counter()
    errors = Counter()
    for p in parts:
        data = parse_part_data(p)
        tool = (data.get("tool") or "").strip()
        status = (data.get("state", {}).get("status") if isinstance(data.get("state"), dict) else "") or ""
        if tool:
            usage[tool] += 1
            if "error" in str(status).lower():
                errors[tool] += 1
    return {
        "usage": dict(usage.most_common(20)),
        "errors": dict(errors.most_common(10)),
    }


def get_response_times(conn):
    """Measure how fast the agent replies by looking at time between user and assistant messages."""
    user_times = [r["time_created"] for r in conn.execute(
        "SELECT time_created FROM message WHERE json_extract(data, '$.role') = 'user' ORDER BY time_created"
    ).fetchall()]
    assistant_times = [r["time_created"] for r in conn.execute(
        "SELECT time_created FROM message WHERE json_extract(data, '$.role') = 'assistant' ORDER BY time_created"
    ).fetchall()]
    intervals = []
    for at in assistant_times:
        prev = None
        for ut in reversed(user_times):
            if ut < at:
                prev = ut
                break
        if prev and prev > 0:
            intervals.append((at - prev) / 1000)
    bucket_defs = [
        ("< 5s", lambda x: x < 5),
        ("5-10s", lambda x: 5 <= x < 10),
        ("10-30s", lambda x: 10 <= x < 30),
        ("30-60s", lambda x: 30 <= x < 60),
        ("1-2min", lambda x: 60 <= x < 120),
        ("2-5min", lambda x: 120 <= x < 300),
        ("5-10min", lambda x: 300 <= x < 600),
        ("> 10min", lambda x: x >= 600),
    ]
    buckets = []
    for label, pred in bucket_defs:
        buckets.append({"range": label, "count": sum(1 for x in intervals if pred(x))})
    sorted_i = sorted(intervals) if intervals else [0]
    return {
        "buckets": buckets,
        "median_seconds": round(sorted_i[len(sorted_i) // 2], 1),
        "average_seconds": round(sum(intervals) / len(intervals), 1) if intervals else 0,
    }


def get_multi_agent(conn):
    """Check how many sessions used sub-agents (parallel execution)."""
    sessions = [dict(r) for r in conn.execute("SELECT id, parent_id FROM session").fetchall()]
    child_count = 0
    parent_ids = set()
    for s in sessions:
        if s.get("parent_id"):
            child_count += 1
            parent_ids.add(str(s["parent_id"]))
    return {
        "parallel_events": child_count,
        "parent_sessions": len(parent_ids),
        "total_sessions": len(sessions),
    }


def get_project_areas(conn):
    """Group sessions by project folder and find which tools were used in each."""
    sessions = [dict(r) for r in conn.execute("SELECT id, directory FROM session").fetchall()]
    dir_map = defaultdict(list)
    for s in sessions:
        d = (s.get("directory") or "unknown").strip()
        parts = [p for p in d.split("/") if p]
        normalized = "/" + "/".join(parts[:5]) if parts else d
        dir_map[normalized].append(s["id"])
    areas = []
    for directory, sids in sorted(dir_map.items(), key=lambda x: -len(x[1]))[:10]:
        ph, params = build_placeholders(sids)
        msg_ids = [str(r["id"]) for r in conn.execute(
            f"SELECT id FROM message WHERE session_id IN ({ph})", params
        ).fetchall()]
        tools = Counter()
        if msg_ids:
            mph, mparams = build_placeholders(msg_ids)
            for p in conn.execute(f"SELECT data FROM part WHERE message_id IN ({mph})", mparams).fetchall():
                data = parse_part_data(p)
                t = (data.get("tool") or "").strip()
                if t:
                    tools[t] += 1
        top5 = dict(tools.most_common(5))
        dominant = next(iter(top5)) if top5 else "none"
        areas.append({
            "directory": directory,
            "sessions": len(sids),
            "tools": top5,
            "dominant": dominant,
        })
    return areas


def get_time_of_day(conn):
    """Sort user messages by time of day period."""
    msgs = conn.execute(
        "SELECT time_created FROM message WHERE json_extract(data, '$.role') = 'user'"
    ).fetchall()
    periods = {"Night (0-6)": 0, "Morning (6-12)": 0, "Afternoon (12-18)": 0, "Evening (18-24)": 0}
    for m in msgs:
        h = datetime.fromtimestamp(m["time_created"] / 1000, tz=timezone.utc).hour
        if 6 <= h < 12:
            periods["Morning (6-12)"] += 1
        elif 12 <= h < 18:
            periods["Afternoon (12-18)"] += 1
        elif 18 <= h < 24:
            periods["Evening (18-24)"] += 1
        else:
            periods["Night (0-6)"] += 1
    return [{"period": k, "count": v} for k, v in periods.items()]


def get_prompt_analysis(conn, limit=10):
    """Look at the most recent prompts and sort them by type and length."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM session ORDER BY time_created DESC LIMIT ?", (limit,))
    sids = [row["id"] for row in cur.fetchall()]
    if not sids:
        return {"prompt_count": 0, "avg_length": 0, "categories": {}}
    ph, params = build_placeholders(sids)
    user_msgs = conn.execute(
        f"SELECT id, session_id, time_created FROM message WHERE json_extract(data, '$.role') = 'user' AND session_id IN ({ph}) ORDER BY time_created",
        params,
    ).fetchall()
    if not user_msgs:
        return {"prompt_count": 0, "avg_length": 0, "categories": {}}
    msg_ids = [str(r["id"]) for r in user_msgs]
    mph, mparams = build_placeholders(msg_ids)
    parts = conn.execute(
        f"SELECT message_id, data FROM part WHERE message_id IN ({mph}) AND json_extract(data, '$.type') = 'text'",
        mparams,
    ).fetchall()
    prompts_by_msg = defaultdict(list)
    for p in parts:
        data = parse_part_data(p)
        prompts_by_msg[str(p["message_id"])].append(data.get("text", ""))
    prompts = []
    for msg in user_msgs:
        text = "".join(prompts_by_msg.get(str(msg["id"]), [])).strip()
        prompts.append({"session_id": str(msg["session_id"]), "text": text, "length": len(text)})
    categories = Counter()
    keywords = {
        "Implementation": ["create", "implement", "build", "add", "update", "modify", "generate", "write"],
        "Debugging": ["fix", "error", "bug", "issue", "problem", "not working", "crash", "fail"],
        "Exploration": ["what", "why", "how", "explain", "describe", "find", "search", "look", "show"],
        "Refactoring": ["refactor", "improve", "clean", "restructure", "reorganize"],
        "Documentation": ["document", "readme", "comment", "docstring", "docs"],
    }
    for p in prompts:
        t = p["text"].lower()
        matched = False
        for cat, words in keywords.items():
            if any(w in t for w in words):
                categories[cat] += 1
                matched = True
                break
        if not matched:
            categories["Other"] += 1
    lengths = [p["length"] for p in prompts]
    return {
        "prompt_count": len(prompts),
        "avg_length": round(sum(lengths) / len(lengths), 1) if lengths else 0,
        "max_length": max(lengths) if lengths else 0,
        "min_length": min(lengths) if lengths else 0,
        "categories": dict(categories),
        "prompts": [{"session_id": p["session_id"], "text": p["text"][:150], "length": p["length"]} for p in prompts[:20]],
    }


def get_model_usage(conn):
    """Count how many times each AI model was used."""
    rows = conn.execute("SELECT data FROM message").fetchall()
    counter = Counter()
    for row in rows:
        data = json.loads(row["data"]) if isinstance(row["data"], str) else row["data"]
        if data.get("role") != "assistant":
            continue
        model = data.get("model", {})
        if not isinstance(model, dict):
            continue
        mid = model.get("modelID", "")
        pid = model.get("providerID", "")
        if not mid:
            continue
        key = f"{pid}/{mid}" if pid else mid
        counter[key] += 1
    total = sum(counter.values())
    return {
        "total_calls": total,
        "unique_models": len(counter),
        "top_models": [
            {"name": m, "count": c, "pct": round(c / total * 100, 1) if total else 0}
            for m, c in counter.most_common(10)
        ],
    }


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def make_bars(items, key_count="count", max_count=None, label_key="name", color="#64ffda"):
    """Turn a list of items into HTML horizontal bar chart rows."""
    if not items:
        return '<p style="color:var(--text-secondary);font-style:italic;">No data available.</p>'
    if max_count is None:
        max_count = max(i.get(key_count, 0) for i in items) or 1
    total = sum(i.get(key_count, 0) for i in items) or 1
    html = ""
    for item in items:
        c = item.get(key_count, 0)
        w = (c / max_count) * 85
        pct = c * 100 / total
        html += f'''<div class="bar-row">
          <span class="bar-label">{item.get(label_key, "")}</span>
          <div class="bar-track"><div class="bar-fill" data-width="{w}%" style="background:{color};"></div></div>
          <span class="bar-value">{c} ({pct:.0f}%)</span>
        </div>'''
    return html


# ---------------------------------------------------------------------------
# Narrative generation — writes the text summaries for the dashboard
# ---------------------------------------------------------------------------

def generate_narratives(data):
    """Create the 'At a Glance' section text from usage data."""
    tool = data["tool_usage"]["usage"]
    errors = data["tool_usage"]["errors"]
    areas = data["project_areas"]
    rt = data["response_times"]
    ma = data["multi_agent"]
    overall = data["overall"]
    top_area = areas[0] if areas else {}

    bash_c = tool.get("bash", 0)
    read_c = tool.get("read", 0)
    edit_c = tool.get("edit", 0)
    write_c = tool.get("write", 0)
    grep_c = tool.get("grep", 0)
    glob_c = tool.get("glob", 0)

    explorer_score = read_c + grep_c + glob_c
    write_err = errors.get("write", 0)
    bash_err = errors.get("bash", 0)
    rw_ratio = round(read_c / max(write_c, 1), 1)

    multi_pct = round(ma["parallel_events"] / max(ma["total_sessions"], 1) * 100, 1)

    strengths = (
        f"You work across {overall['total_sessions']} sessions "
        f"with {overall['total_messages']:,} messages. "
        f"Your bash usage ({bash_c:,} calls) shows you use the command line for testing. "
        f"Edit ({edit_c:,}) and Write ({write_c:,}) show you build code step by step. "
        f"Grep ({grep_c:,}) and Glob ({glob_c:,}) mean you search files thoroughly."
    )
    friction = (
        f"Write errors ({write_err}) and Bash errors ({bash_err}) suggest trouble "
        f"with file operations and running commands. "
        f"Your Read/Write ratio ({rw_ratio}:1) means you spend a lot of time exploring "
        f"before making changes. "
        f"Average response time is {rt['average_seconds']}s (median {rt['median_seconds']}s)."
    )
    quick_wins = (
        f"Add pre-commit checks to reduce bash errors ({bash_err} found). "
        f"Use parallel Task agents for faster exploration instead of reading files one by one. "
        f"Commit after each logical step, not just at the end. "
        f"Limit exploration rounds before switching to building."
    )
    horizon = (
        f"Build automated pipelines using your {ma['parallel_events']} parallel sub-agent events. "
        f"Set up self-correcting TDD loops with automatic test runners. "
        f"Sync documentation automatically alongside code changes."
    )

    return {"strengths": strengths, "friction": friction, "quick_wins": quick_wins, "horizon": horizon}


def generate_big_wins(data):
    """Show the user what they did well."""
    tool = data["tool_usage"]["usage"]
    areas = data["project_areas"]
    ma = data["multi_agent"]
    ma_pct = round(ma["parallel_events"] / max(ma["total_sessions"], 1) * 100, 1)
    read_c = tool.get("read", 0)
    grep_c = tool.get("grep", 0)
    glob_c = tool.get("glob", 0)
    bash_c = tool.get("bash", 0)
    edit_c = tool.get("edit", 0)
    write_c = tool.get("write", 0)
    discovery = read_c + grep_c + glob_c
    top_area = areas[0] if areas else {}

    wins = []
    wins.append(f'''<div class="big-win reveal">
      <div class="big-win-title">Great at Exploring Code</div>
      <p style="color:var(--text-secondary);margin-top:12px;">
        You used Read ({read_c:,}) + Grep ({grep_c:,}) + Glob ({glob_c:,}) = {discovery:,} search operations.
        This means you understand the code well before making changes.
        This careful approach helps avoid mistakes.
      </p>
    </div>''')
    wins.append(f'''<div class="big-win reveal">
      <div class="big-win-title">Power User of the Command Line</div>
      <p style="color:var(--text-secondary);margin-top:12px;">
        With {bash_c:,} bash calls and {edit_c:,} edits across {data['overall']['total_sessions']} sessions,
        you use automation a lot and work in a cycle of build and improve.
      </p>
    </div>''')
    if ma["parallel_events"] > 0:
        wins.append(f'''<div class="big-win reveal">
          <div class="big-win-title">Using Parallel Agents</div>
          <p style="color:var(--text-secondary);margin-top:12px;">
            {ma["parallel_events"]} parallel sub-agent events from {ma["parent_sessions"]} parent sessions
            ({ma_pct}%) show you are already using multi-agent workflows well.
          </p>
        </div>''')
    wins.append(f'''<div class="big-win reveal">
      <div class="big-win-title">Building Code Step by Step</div>
      <p style="color:var(--text-secondary);margin-top:12px;">
        Edit ({edit_c:,}) + Write ({write_c:,}) operations show steady code improvement,
        where you keep refining by using tools repeatedly.
      </p>
    </div>''')
    return "".join(wins)


def generate_friction_html(data):
    """Show problem areas and give advice on how to fix them."""
    errors = data["tool_usage"]["errors"]
    tool = data["tool_usage"]["usage"]
    write_err = errors.get("write", 0)
    bash_err = errors.get("bash", 0)
    read_c = tool.get("read", 0)
    write_c = tool.get("write", 0)
    rw = round(read_c / max(write_c, 1), 1)
    rt = data["response_times"]

    sections = []
    if write_err > 0:
        sections.append(f'''<div class="friction-category reveal">
          <div class="friction-title">Write Errors ({write_err} problems)</div>
          <p style="color:var(--text-secondary);margin-top:8px;">
            The write tool had many errors. Common causes: file not found, no permission, 
            or someone else changed the file.
          </p>
          <h4 style="margin-top:12px;">How to Fix</h4>
          <p style="color:var(--text-secondary);">Always check that the file exists before writing. Use glob to find the path first.</p>
        </div>''')
    if bash_err > 0:
        sections.append(f'''<div class="friction-category reveal">
          <div class="friction-title">Bash Command Errors ({bash_err} problems)</div>
          <p style="color:var(--text-secondary);margin-top:8px;">
            Bash is your most-used tool but also has many errors. Most failures come from 
            missing tools or wrong file paths.
          </p>
          <h4 style="margin-top:12px;">How to Fix</h4>
          <p style="color:var(--text-secondary);">Check that all needed tools are installed before running. Add pre-commit hooks to catch issues early.</p>
        </div>''')
    if rw > 3:
        sections.append(f'''<div class="friction-category reveal">
          <div class="friction-title">Too Much Exploring, Not Enough Building</div>
          <p style="color:var(--text-secondary);margin-top:8px;">
            You read ({read_c:,}) much more than you write ({write_c:,}) — a ratio of {rw}:1.
            Some sessions spend more time looking at code than creating it.
          </p>
          <h4 style="margin-top:12px;">How to Fix</h4>
          <p style="color:var(--text-secondary);">Set a limit on how many times you explore (e.g., 5 reads) before switching to building.</p>
        </div>''')
    if rt["average_seconds"] > rt["median_seconds"] * 1.5:
        sections.append(f'''<div class="friction-category reveal">
          <div class="friction-title">Slow Response Times</div>
          <p style="color:var(--text-secondary);margin-top:8px;">
            The average response time ({rt['average_seconds']}s) is much higher than the median ({rt['median_seconds']}s),
            which means some requests take a long time and break your flow.
          </p>
          <h4 style="margin-top:12px;">How to Fix</h4>
          <p style="color:var(--text-secondary);">Use parallel sub-agents for tasks that don't depend on each other, instead of waiting one at a time.</p>
        </div>''')
    if not sections:
        sections.append('''<div class="friction-category reveal">
          <div class="friction-title">No Major Problems Found</div>
          <p style="color:var(--text-secondary);margin-top:8px;">
            Your workflow looks clean with few errors. Keep up the good habits!
          </p>
        </div>''')
    return "".join(sections)


def generate_agents_md_suggestions(data):
    """Create ready-to-use AGENTS.md rules based on actual usage problems."""
    errors = data["tool_usage"]["errors"]
    tool = data["tool_usage"]["usage"]
    read_c = tool.get("read", 0)
    write_c = tool.get("write", 0)
    bash_err = errors.get("bash", 0)
    write_err = errors.get("write", 0)
    rw = round(read_c / max(write_c, 1), 1)

    rules = []
    if bash_err > 0:
        rules.append(f'''<div class="chart-card reveal" style="margin-bottom:16px;">
          <h4>Rule: Check Before Running Bash</h4>
          <code class="code-block">Before running bash commands, check that all needed tools are installed. Run npm install or check for required packages first.</code>
          <p style="color:var(--text-secondary);font-size:1rem;">This would prevent {bash_err} bash errors from missing tools.</p>
        </div>''')
    if write_err > 0:
        rules.append(f'''<div class="chart-card reveal" style="margin-bottom:16px;">
          <h4>Rule: Check File Paths Before Writing</h4>
          <code class="code-block">Before writing to a file, check the path with glob. Create parent folders if needed.</code>
          <p style="color:var(--text-secondary);font-size:1rem;">This would reduce {write_err} write errors by checking paths first.</p>
        </div>''')
    if rw > 3:
        rules.append(f'''<div class="chart-card reveal" style="margin-bottom:16px;">
          <h4>Rule: Limit Exploration Time</h4>
          <code class="code-block">After 5 read or grep operations, switch to building. Set a limit for how long you explore.</code>
          <p style="color:var(--text-secondary);font-size:1rem;">Fixes the {rw}:1 Read-to-Write ratio problem.</p>
        </div>''')
    rules.append('''<div class="chart-card reveal">
      <h4>Rule: Commit After Each Step</h4>
      <code class="code-block">Commit changes after finishing one logical piece of work, not just at the end. Use git add and commit step by step.</code>
      <p style="color:var(--text-secondary);font-size:1rem;">Prevents large file changes and makes it easier to undo mistakes.</p>
    </div>''')
    return "".join(rules)


def generate_features_html():
    """Suggest features the user might not know about."""
    return '''<div class="feature-card reveal">
  <h4 style="color:var(--accent-blue);margin-bottom:8px;">Auto-Update Documentation</h4>
  <p style="color:var(--text-secondary);font-size:1.14rem;">Keep README files up to date with your code changes. After editing code, say: "Update the docs for what I just changed."</p>
</div>
<div class="feature-card reveal">
  <h4 style="color:var(--accent-blue);margin-bottom:8px;">Test-Build-Test Loop</h4>
  <p style="color:var(--text-secondary);font-size:1.14rem;">Use the RED-GREEN-REFACTOR cycle: write a test, run it (expect fail), build the feature, run again (expect pass), then clean up.</p>
</div>
<div class="feature-card reveal">
  <h4 style="color:var(--accent-blue);margin-bottom:8px;">Track How Much You Build</h4>
  <p style="color:var(--text-secondary);font-size:1.14rem;">Watch the files_changed number per session as a way to measure progress. Short, focused sessions often produce better results.</p>
</div>'''


def generate_patterns_html():
    """Show new ways to use OpenCode with copyable prompts."""
    return '''<div class="chart-card reveal" style="margin-bottom:16px;">
  <h4 style="color:var(--text-heading);">Use Parallel Agents for Exploration</h4>
  <p style="color:var(--text-secondary);font-size:1.14rem;margin-bottom:12px;">Instead of checking files one by one, launch multiple agents at the same time.</p>
  <code class="code-block">"Launch 3 agents: one to read src/, one to search for patterns, one to find test files. Show me all results together."</code>
  <button class="copy-btn" onclick="copyText(this)">Copy</button>
</div>
<div class="chart-card reveal" style="margin-bottom:16px;">
  <h4 style="color:var(--text-heading);">Edit Files in Batches</h4>
  <p style="color:var(--text-secondary);font-size:1.14rem;margin-bottom:12px;">Group related file changes into one action instead of editing each file separately.</p>
  <code class="code-block">"Read all config files, then edit them all at once. Use glob to find them first."</code>
  <button class="copy-btn" onclick="copyText(this)">Copy</button>
</div>
<div class="chart-card reveal" style="margin-bottom:16px;">
  <h4 style="color:var(--text-heading);">Self-Correcting Test Loop</h4>
  <p style="color:var(--text-secondary);font-size:1.14rem;margin-bottom:12px;">Create a test → build → verify cycle that fixes problems automatically.</p>
  <code class="code-block">"Write a test, run it (expect fail), build the feature, run until it passes. If bash errors happen, fix missing tools first."</code>
  <button class="copy-btn" onclick="copyText(this)">Copy</button>
</div>'''


def generate_horizon_html(data):
    """Show what the user could do next with their skills."""
    ma = data["multi_agent"]
    return f'''<div class="horizon-card reveal">
  <h4 style="color:var(--accent-purple);margin-bottom:8px;">Full Development Pipelines</h4>
  <p style="color:var(--text-secondary);font-size:1.14rem;margin-top:8px;">
    You already have {ma["parent_sessions"]} parent sessions that used sub-agents. 
    You could scale this up to full automated pipelines.
  </p>
</div>
<div class="horizon-card reveal">
  <h4 style="color:var(--accent-purple);margin-bottom:8px;">Tests That Fix Themselves</h4>
  <p style="color:var(--text-secondary);font-size:1.14rem;margin-top:8px;">
    Build test loops that find failures, figure out the cause, and apply fixes automatically.
  </p>
</div>
<div class="horizon-card reveal">
  <h4 style="color:var(--accent-purple);margin-bottom:8px;">Reuse Your Patterns</h4>
  <p style="color:var(--text-secondary);font-size:1.14rem;margin-top:8px;">
    Use your session patterns to create templates for new projects. The agent learns how you work.
  </p>
</div>'''


# ---------------------------------------------------------------------------
# Main HTML generation
# ---------------------------------------------------------------------------

def build_html(data, template_path):
    """Fill the HTML template with all the data and return the complete page."""
    with open(template_path) as f:
        html = f.read()

    o = data["overall"]

    # Basic stats
    html = html.replace("{total_sessions}", str(o["total_sessions"]))
    html = html.replace("{days_span}", str(o["days_span"]))
    html = html.replace("{start_date}", o["start_date"])
    html = html.replace("{end_date}", o["end_date"])
    html = html.replace("{total_messages}", f"{o['total_messages']:,}")
    html = html.replace("{msgs_per_day}", str(o["msgs_per_day"]))

    # Narrative summaries
    n = generate_narratives(data)
    html = html.replace("{narrative_strength}", n["strengths"])
    html = html.replace("{narrative_friction}", n["friction"])
    html = html.replace("{quick_wins}", n["quick_wins"])
    html = html.replace("{horizon_summary}", n["horizon"])

    # Project areas
    pa_html = ""
    for pa in data["project_areas"]:
        dname = os.path.basename(pa["directory"])
        total_t = sum(pa["tools"].values()) or 1
        top_t = max(pa["tools"], key=pa["tools"].get) if pa["tools"] else "none"
        top_pct = pa["tools"].get(top_t, 0) * 100 // total_t if top_t != "none" else 0
        pa_html += f'''<div class="project-area reveal">
          <h4>{dname} ({pa["sessions"]} sessions)</h4>
          <p>{pa["dominant"].title()} is the main tool ({pa["tools"].get(pa["dominant"], 0)} calls, {top_pct}% of tools in this area).</p>
        </div>'''
    html = html.replace("{project_areas_html}", pa_html)

    # Model usage
    mu = data["model_usage"]
    html = html.replace("{model_total_calls}", str(mu["total_calls"]))
    html = html.replace("{model_unique_models}", str(mu["unique_models"]))
    html = html.replace("{model_bars_html}", make_bars(
        mu["top_models"], key_count="count", label_key="name", color="#64ffda"
    ) if mu["top_models"] else '<p style="color:var(--text-secondary);font-style:italic;">No model usage data available.</p>')

    # Tool usage bars
    tu = data["tool_usage"]
    total_tool_calls = sum(tu["usage"].values()) or 1
    max_usage = max(tu["usage"].values()) if tu["usage"] else 1
    tool_items = [{"name": k, "count": v} for k, v in sorted(tu["usage"].items(), key=lambda x: -x[1])]
    html = html.replace("{tool_bars_html}", make_bars(tool_items, max_count=max_usage))

    # Error bars
    max_err = max(tu["errors"].values()) if tu["errors"] else 1
    err_items = [{"name": k, "count": v} for k, v in sorted(tu["errors"].items(), key=lambda x: -x[1])]
    html = html.replace("{error_bars_html}", make_bars(err_items, max_count=max_err, color="#ff5252"))

    # Response time
    rt = data["response_times"]
    rt_max = max(b["count"] for b in rt["buckets"]) if rt["buckets"] else 1
    rt_bars = ""
    for b in rt["buckets"]:
        w = (b["count"] / rt_max) * 85
        rt_bars += f'''<div class="bar-row">
          <span class="bar-label">{b["range"]}</span>
          <div class="bar-track"><div class="bar-fill" data-width="{w}%" style="background:#7c4dff;"></div></div>
          <span class="bar-value">{b["count"]}</span>
        </div>'''
    rt_html = f'''<div class="chart-card reveal">
      <div style="display:flex;gap:32px;margin-bottom:16px;">
        <div><strong>Median:</strong> {rt["median_seconds"]}s</div>
        <div><strong>Average:</strong> {rt["average_seconds"]}s</div>
      </div>
      <div class="chart-title">Response Time Breakdown</div>
      {rt_bars}
    </div>'''
    html = html.replace("{response_time_html}", rt_html)

    # Multi-agent
    ma = data["multi_agent"]
    ma_pct = round(ma["parallel_events"] / max(ma["total_sessions"], 1) * 100, 1)
    html = html.replace("{multi_agent_html}", f'''<div class="chart-card reveal">
      <h4 class="multi-agent-title" style="font-weight:700;color:#b388ff;font-size:1.26rem;">Multi-Agent Activity</h4>
      <p style="color:var(--text-secondary);margin-bottom:16px;">
        You launched sub-agents in {ma["parent_sessions"]} parent sessions, making {ma["parallel_events"]} parallel events.
      </p>
    </div>''')

    # Time of day
    tod = data["time_of_day"]
    tod_max = max(t["count"] for t in tod) if tod else 1
    tod_html = ""
    for t in tod:
        w = (t["count"] / tod_max) * 85
        c = "#64ffda" if "Afternoon" in t["period"] else "#7c4dff"
        tod_html += f'''<div class="bar-row">
          <span class="bar-label">{t["period"]}</span>
          <div class="bar-track"><div class="bar-fill" data-width="{w}%" style="background:{c};"></div></div>
          <span class="bar-value">{t["count"]}</span>
        </div>'''
    html = html.replace("{time_of_day_html}", tod_html)

    # Prompt analysis
    pa = data["prompt_analysis"]
    html = html.replace("{prompt_count}", str(pa["prompt_count"]))
    html = html.replace("{avg_prompt_length}", f"{pa['avg_length']:,.0f}")
    cat_items = sorted(pa["categories"].items(), key=lambda x: -x[1])
    cat_max = max(c for _, c in cat_items) if cat_items else 1
    cat_html = ""
    for name, count in cat_items:
        w = (count / cat_max) * 85
        pct = count * 100 // max(pa["prompt_count"], 1)
        cat_html += f'''<div class="bar-row">
          <span class="bar-label">{name}</span>
          <div class="bar-track"><div class="bar-fill" data-width="{w}%" style="background:#64ffda;"></div></div>
          <span class="bar-value">{pct}%</span>
        </div>'''
    html = html.replace("{prompt_categories_html}", cat_html)

    # Big wins, friction, suggestions, features, patterns, horizon
    html = html.replace("{big_wins_html}", generate_big_wins(data))
    html = html.replace("{friction_html}", generate_friction_html(data))
    html = html.replace("{agents_md_suggestions_html}", generate_agents_md_suggestions(data))
    html = html.replace("{features_html}", generate_features_html())
    html = html.replace("{patterns_html}", generate_patterns_html())
    html = html.replace("{horizon_html}", generate_horizon_html(data))

    # Fun ending
    fact = f"You sent {o['total_messages']:,} messages across {o['total_sessions']} sessions."
    first_area = data["project_areas"][0] if data["project_areas"] else None
    detail = f"With {tu['usage'].get('bash', 0):,} bash calls and lots of back-and-forth, you are making real progress."
    html = html.replace('"{fun_fact}"', f'"{fact}"')
    html = html.replace("{fun_detail}", detail)

    return html


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """Read arguments, collect data, build the dashboard, save it."""
    db_path = None
    out_path = "insights.html"

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--out" and i + 1 < len(sys.argv):
            out_path = sys.argv[i + 1]
            i += 1
        elif not arg.startswith("--") and db_path is None:
            db_path = arg
        i += 1

    try:
        db_path = db_path or find_db_path()
        conn = get_db(db_path)

        data = {
            "overall": get_overall_stats(conn),
            "tool_usage": get_tool_usage(conn),
            "response_times": get_response_times(conn),
            "multi_agent": get_multi_agent(conn),
            "project_areas": get_project_areas(conn),
            "time_of_day": get_time_of_day(conn),
            "prompt_analysis": get_prompt_analysis(conn, limit=10),
            "model_usage": get_model_usage(conn),
        }
        conn.close()

        # Find the template file relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(script_dir, "..", "templates", "insights.html")

        html = build_html(data, template_path)
        with open(out_path, "w") as f:
            f.write(html)

        size = len(html)
        print(f"Dashboard saved to {out_path}")
        print(f"File size: {size:,} bytes")
        print(f"Data: {data['overall']['total_sessions']} sessions, {data['overall']['total_messages']:,} messages over {data['overall']['days_span']} days")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
