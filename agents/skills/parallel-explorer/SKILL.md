---
name: parallel-explorer
description: Speeds up codebase analysis by running multiple search agents at the same time instead of one after another. Uses the 92 parallel events found in usage data.
license: Apache-2.0
compatibility: opencode
metadata:
  audience: developers
  workflow: code-exploration
---

## What I Do

- Run multiple explore agents at the same time for faster codebase analysis
- Cover frontend, backend, routes, tests, config, and docs all at once
- Combine results from all agents before deciding what to do
- Make exploration 3-5x faster than checking files one by one
- Follow a standard pattern for multi-agent work

## When to Use Me

- When asked to learn a new codebase or feature area
- Before making changes that touch many layers (UI + API + DB)
- When fixing bugs that could be in different parts of the system
- When doing code review across the full stack
- When the task mentions many folders or concerns

## How to Use Me

### Step 1: Pick What to Explore

Find 3-5 areas to check at the same time:

- **Frontend**: UI components, pages, routes, state
- **Backend**: API endpoints, services, middleware, data
- **Database**: Schema, migrations, queries, models
- **Config**: Package files, build setup, deployment, env
- **Tests**: Test files, patterns, fixtures
- **Docs**: README, API docs, setup guides

### Step 2: Launch Parallel Agents

Use the `task` tool with `subagent_type: "explore"` for each area:

```
Example: For a full app, launch 3-4 agents:
- explore(frontend) → components, pages, styles
- explore(backend) → routes, controllers, services
- explore(database) → schema, migrations, models
- explore(tests) → test setup, coverage, patterns
```

### Step 3: Combine Results

Gather results from all agents. Look for:

- Do frontend components match backend API endpoints?
- Are all database fields in the models?
- Do tests cover the code paths found?

### Step 4: Write Summary

Give a clear picture of the codebase:

- How it is built (architecture)
- Key files and how they connect
- Patterns and rules found
- Missing pieces or problems found

## Guidelines

- Use 3-5 agents max to avoid too much context
- Give each agent a narrow focus for best results
- Do not use parallel agents for simple single-file tasks
- Always say "quick" or "medium" for how deep to explore
- Combine findings before making any changes
- When user asks "how does X work" — explore all relevant layers at once

## Examples

- User: "Add user profile feature" → explore frontend pages, backend API patterns, DB schema at the same time
- User: "Fix login bug" → explore auth frontend, auth backend, session handling, test coverage together
- User: "What is in this project?" → launch agents for structure, dependencies, entry points, and tests
