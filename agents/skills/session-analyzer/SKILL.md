---
name: session-analyzer
description: Runs the full OpenCode session check — pulls data from the database, creates an interactive HTML dashboard, and shows you your usage patterns in one step.
license: Apache-2.0
compatibility: opencode
metadata:
  audience: developers
  workflow: custom
---

## What I Do

- Run the OpenCode session analyzer to get full stats from the SQLite database
- Get recent prompts (last 10 sessions) with categories and samples
- Turn JSON output directly into HTML without temp files
- Build a complete interactive insights dashboard (`insights.html`)
- Show top tips based on data patterns

## When to Use Me

- User asks for session analysis, insights report, or usage stats
- User says "generate insights", "analyze my sessions", "show me usage patterns"
- After finishing big tasks (see AGENTS.md Session Improvement Hook)
- When user wants to see trends in their OpenCode session history

## How to Use Me

### Step 1: Run the Analyzer

Run both analyzer commands at the same time and save output to variables:

```bash
# Get full stats
STATS=$(python3 ~/.agents/skills/insights/session_analyzer.py 2>/dev/null)

# Get recent prompts
PROMPTS=$(python3 ~/.agents/skills/insights/session_analyzer.py --recent 2>/dev/null)
```

Do NOT save to temp files. Read JSON directly from the variables.

### Step 2: Read Key Numbers

From the stats JSON, get:

- `total_sessions`, `total_messages`, `days_span`, `time_range.start_date`, `time_range.end_date`
- `tool_usage` (top tools), `tool_errors`
- `response_times.buckets`, `median_seconds`, `average_seconds`
- `multi_clauding.total_parallel_events`, `sessions_with_children`
- `time_of_day.periods`

From prompts JSON:
- `prompt_count`, `avg_prompt_length`
- `categories` breakdown
- First 5 entries from `prompts_sample`

### Step 3: Build the HTML Dashboard

Use the data to fill the HTML template. Key sections:

1. **Header** — session count, days, date range
2. **At a Glance** — summary of what works, what slows you down, quick wins, future ideas
3. **Stats Row** — messages, sessions, days, msgs per day
4. **What You Work On** — project areas from sessions_by_directory
5. **Tool Usage Charts** — horizontal bar charts for top tools and errors
6. **Response Time** — buckets with median and average
7. **Multi-Agent Section** — parallel session detection
8. **Time of Day** — activity by period (Morning / Afternoon / Evening / Night)
9. **Prompt Analysis** — categories, average length, sample prompts
10. **Big Wins** — what you did well
11. **Friction Points** — problem areas with data-backed examples
12. **AGENTS.md Suggestions** — ready-to-use markdown tips
13. **Features to Try** — new ways to use OpenCode
14. **New Usage Patterns** — copyable prompt examples
15. **On the Horizon** — future workflow possibilities
16. **Fun Ending** — a fun fact based on your data

### Step 4: Save and Show

Save as `insights.html` in the current folder. After building:

1. Confirm the file path and size (should be under 50KB)
2. Highlight top 3 tips from the dashboard
3. Ask if user wants to create skills or update AGENTS.md

## Guidelines

- Always run both analyzer commands at the same time for speed
- Read JSON directly — never save to temp files
- Keep HTML under 50KB; put all CSS and JS inside the file
- Be fair and data-driven; do not judge the user
- Focus on useful tips, not just numbers
- If no problems found, say "Your workflow looks good!"
- Use `jq` for JSON if available, otherwise use Python one-liners

## Examples

### Example 1: Basic Use
```bash
# User says "generate insights"
STATS=$(python3 ~/.agents/skills/insights/session_analyzer.py 2>/dev/null)
PROMPTS=$(python3 ~/.agents/skills/insights/session_analyzer.py --recent 2>/dev/null)
# Parse data and build dashboard
```

### Example 2: After a Task
After finishing a big coding task, offer:
"I finished your request. Want me to run session analysis to find ways to improve your workflow?"

## Troubleshooting

**Analyzer not found:**
Check that `~/.agents/skills/insights/session_analyzer.py` exists. If not, guide user to install it.

**No data:**
Some stats (tool usage, response times) may show zero if the database has limited logging. Tell the user this is expected and suggest enabling detailed logging.

**Large output:**
If HTML goes over 50KB, trim prompt samples or chart data. Keep only the most important sections.
