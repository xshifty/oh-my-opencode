# AGENTS.md — oh-my-opencode

## Repo Purpose

A collection of OpenCode skills, commands, scripts, and agent configs. Components are symlinked into the user's OpenCode config dir via `install.sh`.

## Key Commands

```bash
./install.sh                          # Symlink everything to ~/.config/opencode
./install.sh --target ~/.config/opencode  # Custom target dir
```

Scripts are standalone Python:

```bash
python3 agents/scripts/<script>.py [db_path]       # JSON to stdout (most scripts)
python3 agents/scripts/session_analyzer.py [db_path]  # Combined JSON output
python3 agents/scripts/generate_report.py [--out path] [db_path]  # Writes insights.html
```

Most scripts output JSON to stdout. The exception is `generate_report.py` which writes `insights.html` to the current directory (or `--out` path).

## Architecture

```
agents/
├── AGENTS.md          # Agent constitution (symlinked to OpenCode config)
├── commands/          # OpenCode command definitions (*.md with frontmatter)
├── scripts/           # Python DB query scripts
│   ├── shared.py      # DB helpers: find_db_path(), get_db(), fetch_rows()
│   ├── find_db.py     # Returns {"db_path": "..."} JSON
│   ├── get_*.py       # Individual stats scripts (JSON to stdout)
│   └── generate_report.py  # Self-contained HTML dashboard generator
├── skills/            # SKILL.md directories (context7-mcp, session-analyzer, etc.)
└── templates/         # insights.html — dark theme dashboard template
```

## Script Conventions

- All scripts import from `shared.py` for DB access
- Accept optional `db_path` as first CLI arg; auto-discovers via `find_db_path()` if omitted
- Most scripts output valid JSON to stdout (never print debug info)
- `generate_report.py` is the exception — it writes `insights.html` to disk (accepts `--out path`)
- DB timestamps are in **milliseconds** (divide by 1000 for Python datetime)
- `session_analyzer.py` is the combined runner — use `--recent N` to limit sessions

## DB Schema Notes

- `session` table: `time_created`, `time_updated` (ms epoch), `id`, `cwd`
- `message` table: `data` is JSON with `$.role` field ("user" / "assistant")
- `part` table: `data` is JSON — use `shared.parse_part_data()` to handle str/dict
- Use `shared.build_placeholders()` for safe SQL IN clauses

## Installation Behavior

`install.sh` symlinks top-level items from `agents/` into OpenCode config:
- `AGENTS.md`, `commands/`, `skills/` → direct symlinks
- `scripts/`, `templates/` → explicit folder symlinks (skipped in main loop)
- Existing symlinks are replaced (safe to re-run)
- Creates target dir if missing

## DB Discovery Order

1. `$OPENCODE_CONFIG` env var
2. `~/.config/opencode`
3. `$XDG_CONFIG_HOME/opencode`
4. `~/Library/Application Support/opencode` (macOS)
5. `~/.local/share/opencode/opencode.db` (Linux default)

## Python Requirements

- Python 3.12+
- No external dependencies — stdlib only (`sqlite3`, `json`, `os`, `collections`)

## Important Notes

- `insights.html` template uses `{placeholder}` syntax — `generate_report.py` handles replacement
- Skills are activated by their `name` field in SKILL.md frontmatter
- The `insights` command (in `commands/insights.md`) runs `generate_report.py` as its primary step — no manual script orchestration needed
- `generate_report.py` uses `scripts/../templates/insights.html` to resolve the template path
- `__pycache__/` is gitignored — scripts work fine with or without it
