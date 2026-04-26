# oh-my-opencode

<div align="center">

A collection of [OpenCode](https://opencode.ai) skills, commands, scripts, and agent configurations designed to enhance AI-assisted development workflows.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org)

</div>

## Quick Start

```bash
# Install with symlinks to your OpenCode config directory
./install.sh

# Or specify a custom target
./install.sh --target ~/.config/opencode
```

That's it. All skills, commands, scripts, and templates are now symlinked into your OpenCode configuration.

## Overview

This repository provides reusable components for OpenCode agents: structured skills that guide agent behavior, cached data query scripts for session analysis, an HTML dashboard template, a shared command for insights generation, and an AGENTS.md constitution defining best practices.

## Structure

```
agents/
├── AGENTS.md                          # Agent constitution & guidelines
├── commands/
│   └── insights.md                    # Session insights dashboard command
├── scripts/                           # Cached data query scripts (Python)
│   ├── shared.py                      # Common DB helpers (find_db, get_db)
│   ├── find_db.py                     # Auto-discovers OpenCode DB path
│   ├── session_analyzer.py            # Full session analyzer with --recent flag
│   ├── get_overall_stats.py           # Session/message counts & time range
│   ├── get_tool_usage.py              # Tool usage counts & error rates
│   ├── get_response_times.py          # Response time distribution buckets
│   ├── get_multi_agent.py             # Parallel subagent detection
│   ├── get_project_areas.py           # Directory breakdowns with tool patterns
│   ├── get_time_of_day.py             # Activity by morning/afternoon/evening/night
│   ├── get_recent_prompts.py          # Prompt analysis from last N sessions
│   ├── get_prompt_analysis.py         # Prompt categories, avg length, samples
│   ├── get_model_usage.py             # Model usage stats (top models, unique count)
│   ├── get_session_details.py         # Enriched session data (duration, parent, files)
│   └── generate_report.py             # Self-contained insights dashboard generator
├── skills/                            # Reusable agent skill definitions
│   ├── context7-mcp/SKILL.md          # Documentation lookup via Context7 MCP
│   ├── prompt-feedback/SKILL.md       # Prompt quality analysis & AGENTS.md rules
│   ├── session-analyzer/SKILL.md      # Interactive HTML dashboard generator
│   ├── session-improver/SKILL.md      # Workflow optimization pipeline
│   └── skill-generator/SKILL.md       # Guided skill creation wizard
└── templates/
    └── insights.html                  # Self-contained HTML dashboard template
```

## Skills

### skill-generator

Guides users through creating new OpenCode skills via interactive Q&A. Validates name format, description length, and generates a complete `SKILL.md` with frontmatter, sections, guidelines, and examples.

**When to use:** User wants to create a new agent skill or design a reusable workflow.

### session-improver

Analyzes the current OpenCode session for inefficiencies, repetitive patterns, and missed automation opportunities. Generates targeted skills via `skill-generator` to automate improvements. Activates automatically after significant tasks.

**When to use:** After completing a task, or when user says "analyze session", "find improvements", or "optimize workflow".

### session-analyzer

Runs the OpenCode session analyzer, parses JSON output, and generates an interactive HTML dashboard (`insights.html`) in a single step — no temp files or manual reads required.

**When to use:** User asks for session analysis, insights report, usage statistics, or after running significant tasks.

### prompt-feedback

Extracts prompts from the last 10 OpenCode sessions and analyzes quality patterns (length variance, vagueness, missing structure). Auto-generates actionable AGENTS.md rules or user-facing guidelines to improve future prompting quality.

**When to use:** User asks for "prompt analysis", "improve my prompts", or "prompt quality report".

### context7-mcp

Instructs the agent to use Context7 MCP to fetch current documentation instead of relying on training data when the user asks about libraries, frameworks, APIs, or needs code examples.

**When to use:** Any question involving a library, framework, SDK, CLI tool, or cloud service — even well-known ones like React, Next.js, Prisma, Express, Tailwind, Django, or Spring Boot.

## Commands

### insights

Analyzes OpenCode session history and generates an interactive HTML insights dashboard with prompt analysis from the last 10 sessions. Produces a self-contained `insights.html` file with charts, statistics, friction points, big wins, and actionable recommendations.

**Usage:** Run via OpenCode command interface or directly:
```bash
# Via OpenCode
/insights

# Direct CLI
python3 {OPENCODE_CONFIG_DIR}/scripts/generate_report.py
```
The script auto-discovers the database, collects all metrics, generates narratives from usage patterns, and fills the HTML template — all in one step.

## Scripts

All scripts are standalone Python files that query the OpenCode SQLite database directly. Most output clean JSON to stdout. The exception is `generate_report.py` which produces a complete HTML dashboard.

| Script | Purpose |
|---|---|
| `find_db.py` | Auto-discovers the OpenCode DB path across common locations |
| `get_overall_stats.py` | Session count, message counts, time range |
| `get_tool_usage.py` | Tool usage counts and error rates per tool |
| `get_response_times.py` | Response time distribution (buckets: <1s to >5min) |
| `get_multi_agent.py` | Parallel subagent detection & session grouping |
| `get_project_areas.py` | Directory breakdowns with dominant tools per area |
| `get_time_of_day.py` | Activity patterns by morning/afternoon/evening/night |
| `get_recent_prompts.py` | Prompt analysis from last N sessions (default: 10) |
| `get_prompt_analysis.py` | Prompt categories, avg length, longest/shortest samples |
| `get_model_usage.py` | Model usage stats (top 10 models, unique count, percentages) |
| `get_session_details.py` | Enriched session data with duration, parent status, files_changed |
| `generate_report.py` | **Self-contained dashboard generator** — queries DB, generates narratives, fills HTML template, outputs insights.html |
| `session_analyzer.py` | Full analyzer — runs all queries and outputs combined JSON |

**Usage:**
```bash
# From repository root
python3 agents/scripts/<script>.py [db_path]                    # JSON to stdout
python3 agents/scripts/generate_report.py [--out path] [db_path]  # HTML file

# After installation (uses OPENCODE_CONFIG_DIR)
python3 {OPENCODE_CONFIG_DIR}/scripts/<script>.py [db_path]
python3 {OPENCODE_CONFIG_DIR}/scripts/generate_report.py [--out path] [db_path]
```

`generate_report.py` options:
- `--out /path/to/output.html` — custom output path (default: `insights.html` in current dir)
- No DB path means auto-discovery via `find_db.py`

## Agent Constitution (`AGENTS.md`)

The `agents/AGENTS.md` file defines core rules for agent behavior:

1. Never assume — always ask for clarification
2. Tool calling recovery — avoid repeated failed tool calls
3. Parallel agents — use concurrent subagents when possible
4. TDD approach — follow RED, GREEN, REFACTOR cycle
5. Follow language/framework standards and best practices (SOLID, DRY, KISS, YAGNI)
6. Prefer Context7 for documentation lookups

It also includes guidelines for prompt quality, parallel task delegation, and a session improvement hook that triggers `session-improver` after significant tasks.

## Installation

### Quick Install (Recommended)

Run the automated installer (creates symlinks to your OpenCode config directory):

```bash
./install.sh
```

Or specify a target:

```bash
./install.sh --target ~/.config/opencode
```

The installer symlinks all `agents/` contents into your OpenCode config:
- `AGENTS.md`, `commands/`, `skills/`, `scripts/`, `templates/`

### Manual Install

1. **Skills** — Copy skill directories to your global skills folder:
   ```bash
   mkdir -p ~/.agents/skills/
   cp -r agents/skills/* ~/.agents/skills/
   ```

2. **Commands** — Symlink the commands directory:
   ```bash
   ln -sf $(pwd)/agents/commands ~/.config/opencode/commands
   ```

3. **Scripts & Templates** — Optional, for CLI usage:
    ```bash
    mkdir -p ~/.config/opencode/{scripts,templates}
    cp agents/scripts/*.py ~/.config/opencode/scripts/
    cp agents/templates/insights.html ~/.config/opencode/templates/
    ```

4. **Agent Constitution** — Place `AGENTS.md` in the appropriate location:
   ```bash
   cp agents/AGENTS.md ~/.config/opencode/AGENTS.md
   # OR place it in your project root for per-project rules
   cp agents/AGENTS.md ./AGENTS.md
   ```

## License

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
