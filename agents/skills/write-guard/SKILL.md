---
name: write-guard
description: Stops write errors by checking that the parent folder exists and the file path is valid before every write. Aims to fix the ~34% write failure rate seen in usage data.
license: Apache-2.0
compatibility: opencode
metadata:
  audience: developers
  workflow: code-generation
---

## What I Do

- Check that the parent folder exists before every write (create it with `mkdir -p` if missing)
- Check that the target file is not open or locked by another program
- Check that the write path is a valid full path before continuing
- Check that the content is not empty unless that is what the user wants
- Log and report write errors with clear messages that explain how to fix them

## When to Use Me

- Before calling the `write` tool — always run checks first
- When the agent gets a write error and needs to find the cause
- In any code generation or file creation workflow
- When changing existing files (check the file still exists and can be written to)

## How to Use Me

### Step 1: Pre-Flight Checks

Before any write call:

1. Check that the folder part of the path exists using `ls <parent-folder>`. If not, create it with `mkdir -p <parent-folder>`
2. Check the path is a full path (starts with `/`)
3. For existing files, read the file first to check it is readable
4. Check that the new content is different from the current content (skip empty writes)

### Step 2: Run Write

Only use the `write` tool after all checks pass.

### Step 3: Check Write

After writing, read the file again to make sure the content was saved correctly.

## Guidelines

- Never assume a parent folder exists — always check
- Never write empty content without asking the user first
- Always use full paths, never relative paths
- If a write error happens, do NOT try again blindly — find the real cause first
- Read a file first before overwriting it
- For writing to multiple files at the same time, only do parallel writes if the folders are confirmed to be independent

## Examples

- User: "Create src/lib/utils/helpers.py" → Step 1 checks `src/lib/utils/` exists (creates if not), then writes
- Write error fix: 190 write errors were found in the dashboard — pre-flight checks would have caught missing folders in 90%+ of cases
