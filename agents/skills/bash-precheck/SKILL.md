---
name: bash-precheck
description: Checks that tools, files, and folders are ready before running bash commands. Helps stop the 113 bash errors found in usage data.
license: Apache-2.0
compatibility: opencode
metadata:
  audience: developers
  workflow: operations
---

## What I Do

- Check that needed tools are installed before running commands (`which <tool>` or `command -v <tool>`)
- Check that input files or folders exist
- Check that the working directory is the right one
- For network commands, check the port is free before using it
- For long commands, check there is enough disk space
- Check command syntax before running (especially pipes and redirects)
- Give clear error messages when checks fail

## When to Use Me

- Before every `bash` tool call in your workflow
- When fixing a bash error (there were 113 bash errors found — many are from missing checks)
- Before running npm, pip, or cargo installs (check lock file, network, disk space)
- Before running tests (check test tool exists, test files exist)
- Before git commands (check we are in a git repo, branch is correct)

## How to Use Me

### Step 1: Read the Command

Look at the command you want to run and find:
- What tools or commands will be used
- What files or folders will be read or written
- What the working directory should be
- If the command uses network, disk, or special resources

### Step 2: Run Pre-Checks

Run these checks based on Step 1:

- `command -v <tool>` — check the tool is installed
- `ls <file>` — check input files exist
- `pwd` — check working directory
- `df -h .` — check available disk space (for writes or installs)

### Step 3: Run or Report

- If all checks pass: run the command
- If any check fails: tell the user exactly what went wrong

## Guidelines

- Never assume a tool is installed, even if it is common (node, python, git, etc.)
- Always check the working directory — do not assume it is correct
- For chained commands (`&&`, `||`, pipes), check each part separately
- After a bash error, find the cause before trying again
- For npm/pip/cargo: always check for lock or requirements files before installing

## Examples

- Running `npm run build` → first check `node -v`, `npm -v`, `package.json` exists, `npm install` has been run
- Running `pytest tests/` → first check `python3 -m pytest --version`, `ls tests/`, `pwd`
- Running `git push` → first check `git status`, confirm branch tracks remote
