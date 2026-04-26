---
name: insights
description: Creates an interactive OpenCode insights dashboard with your usage stats, patterns, and tips for getting better results
agent: build
---

Creates a complete HTML insights dashboard from your OpenCode session history. The `generate_report.py` script collects all data, creates charts and summaries, and saves everything into one dashboard file.

## Step 0: Build the Dashboard

Run the report generator. It finds the database, collects all data, writes summaries from your usage patterns, and fills the HTML template in one step:

```bash
python3 "{OPENCODE_CONFIG_DIR}/scripts/generate_report.py"
```

Options:
- `python3 "{OPENCODE_CONFIG_DIR}/scripts/generate_report.py" /path/to/db.db` — use a specific database file
- `python3 "{OPENCODE_CONFIG_DIR}/scripts/generate_report.py" --out /path/to/output.html` — save to a different location

The script creates `insights.html` in the current folder with all sections filled in.

> **Why this script?** `generate_report.py` replaced the old multi-script workflow. It talks to the database through `shared.py`, creates data-based summaries, and builds the full HTML dashboard — no more manual JSON collection or template assembly.

## Step 1: Check the Dashboard (Optional)

Open the file in your browser. If you want to improve specific parts, you have two options:

### Option A — Use the Report As Is
Just show the file path, point out the top findings, and ask if the user wants follow-ups.

### Option B — Add More Detail
Run individual `get_*.py` scripts from `{OPENCODE_CONFIG_DIR}/scripts/` to get fresh data for specific sections. Useful when the user asks about one particular number.

## Step 2: Present

1. Show the file path as a clickable link using `file:///`
2. Point out the top 3 findings (biggest win, biggest problem, best quick fix)
3. Ask if the user wants to:
   - Create any suggested skills (use `skill-generator` or `session-improver`)
   - Update AGENTS.md based on problem areas
   - Run a deeper analysis on one topic

## Example

```
User: "Show me insights"

Agent runs:
python3 {OPENCODE_CONFIG_DIR}/scripts/generate_report.py
→ Dashboard saved to insights.html (55KB)
→ 234 sessions, 9,349 messages over 37 days

Agent shows:
- File: file:///Users/xshifty/dev/ai/oh-my-opencode/insights.html
- Top finding: 92 parallel subagent events show advanced multi-agent work
- Key problem: 190 write errors — add file checks before writing
- Quick fix: use Task agents for parallel file exploration
```

## Troubleshooting

**Database not found:**
- Run `{OPENCODE_CONFIG_DIR}/scripts/find_db.py` to find the database path manually
- Check OpenCode docs for custom install locations
- Fall back to analyzing just the current session

**Script error:**
- Make sure Python 3.12+ and no extra packages needed (stdlib only)
- Check the OpenCode database is not locked by another program

**User wants insights but DB is empty:**
- Explain that OpenCode needs active use to build history
- Dashboard will show data from the current session only

## Important Notes

- `generate_report.py` uses `shared.py` for database access — both must be in the same `scripts/` folder
- The template is found relative to the script: `scripts/../templates/insights.html`
- All data-based summaries are created programmatically from usage patterns — no AI calls needed
- If the user wants deeper detail on one section, run the matching `get_*.py` script separately
