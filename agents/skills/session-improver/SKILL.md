---
name: session-improver
description: Checks your current OpenCode session for slow spots, missed chances, and repeated work. Creates new skills to fix the problems it finds.
license: Apache-2.0
compatibility: opencode
metadata:
  audience: developers
  workflow: session-optimization
---

## What I Do

Look at the current OpenCode session for slow patterns, repeated work, and things that could be automated. For each problem found, use the `skill-generator` skill to create a new skill that fixes it. Run between agent/user tasks to keep improving your workflow.

## When to Use Me

Use this skill when:

- A task finishes (code built, question answered, file changed)
- The user says "analyze session", "find improvements", "optimize workflow"
- You notice the same thing being done over and over
- Many tool calls were needed for a simple task
- The agent had to ask questions that could have been answered ahead of time

## How to Use Me

### Step 1: Check Session History

Look at recent messages and find improvement areas:

**Slow Patterns:**
- Many tool calls one after another that could be combined into one skill
- Reading or writing the same files across different tasks
- Running the same commands many times
- Manual steps that could be automatic (version bumps, release notes, changelogs)

**Missed Chances:**
- Tasks the agent did but could have been made into a reusable skill
- Questions from the user that show they are confused about the project
- Times when the agent had to search for docs that should have been loaded already
- Common errors that a skill could prevent

**Workflow Gaps:**
- Missing skills for common jobs (testing, linting, committing)
- No skill exists for tools or MCPs used many times
- Agent had to make things up instead of following a set workflow
- Cross-file or cross-repo tasks that had no plan

### Step 2: Sort and Rank Problems

For each problem found:

1. **Rate severity** (High / Medium / Low) based on:
   - How often does this happen?
   - How much time could be saved?
   - How annoying is it for the user?

2. **Group related problems** together

3. **Show to user** with:
   - List of problems (max 5, show High severity first)
   - Short description of each problem
   - How long it would take to make a skill for it
   - Ask which ones to work on

### Step 3: Create Skills

For each problem the user picks:

1. **Load `skill-generator`** using the `skill` tool
2. **Give context** about what needs to be built:
   - What the problem is
   - What the new skill should do
   - What it should NOT do
   - Who will use it and when

3. **Guide skill-generator** through its Q&A, but fill in answers from your analysis so the user only needs to say yes or make small changes

4. **Check each skill** before moving on:
   - Name format is correct
   - Description is the right length
   - No duplicate names exist
   - SKILL.md structure is complete

### Step 4: Wrap Up

After making all skills, give a summary:

- List of problems fixed
- Names and descriptions of new skills
- Where files were saved
- Ideas for future improvements

Ask user if they want to:
- Make more skills from remaining problems
- Review or change any skill
- Run another analysis after using the new skills

### Step 5: Set Up Auto-Run

After creating skills, help the user set up auto-activation. Two ways:

**Way A: Global AGENTS.md Rule (Best)**

Add to `~/.config/opencode/AGENTS.md`:

```markdown
## Session Improvement Analysis
After finishing any big task, check if there were slow spots or missed automation chances. If you find patterns that could be fixed with a skill, offer to run the session-improver skill. Do not run it on every small task — only after meaningful ones.

Look for:
- Many tool calls for simple work
- Reading/writing same files across tasks
- User asking about project setup more than once
- Tasks that took longer than expected
```

**Way B: Project-Level AGENTS.md Rule**

Add to `.opencode/AGENTS.md` in the project:

```markdown
## Session Improvement Analysis
After finishing big tasks, check for slow spots and offer to make skills using the session-improver skill. Focus on patterns specific to this project.
```

## Problem Categories (Reference)

### 1. Too Many Tool Calls
- Many calls one after another that could be one skill
- Same file operations across tasks
- Same search patterns for the same files

### 2. Missing Knowledge
- No docs skill for project-specific tools
- No skill for frameworks or libraries used often in this project
- Agent had to guess instead of following a workflow

### 3. Repeated Manual Work
- Version bumps, release notes, changelogs
- Test file setup and boilerplate code
- Config file updates in many places

### 4. Workflow Coordination
- Cross-file changes that need consistency checks
- Multi-step processes with no guide
- Missing checks before committing or pushing

### 5. User Experience
- Confusing project layout causing repeated questions
- No skill for common requests (find X, create Y, update Z)
- Agent not aware of project rules or patterns

## Guidelines

- Only check recent messages (last 10-20), not the whole session
- Focus on problems you can actually fix, not theoretical ones
- Show at most 5 problems per check to not overwhelm the user
- Always ask before creating new skills
- If no good problems found, say so and move on
- Work on High severity items first
- When using skill-generator, fill in as many answers as possible from your analysis
- Do not guess about problems without evidence from the session
- Do not run analysis after trivial tasks

## Examples

### Example 1: Session Analysis Finding

```
Session Analysis Results:

High Priority:
1. Multiple git commands used one after another for commit workflow
   → Could be combined into a "git-commit" skill

Medium Priority:
2. Reading package.json many times across different tasks
   → Could create a "dependency-manager" skill

3. User asked same project structure question twice
   → Missing a "project-overview" skill for onboarding
```

### Example 2: Using skill-generator

```
Creating skill for problem #1 (git-commit workflow):

Loading skill-generator...

Pre-filled answers from analysis:
- Purpose: Make git commit workflow automatic with standard formatting
- Name: git-commit-workflow
- Needs: Check message format, stage files, create commit, push if clean
- Limits: Don't touch untracked files, don't force push without asking
- Audience: developers
- Workflow: github

[Then go through skill-generator Q&A to confirm]
```

## Troubleshooting

**Skill not activating after AGENTS.md setup:**
- Check AGENTS.md is in the right place (project root or ~/.config/opencode/)
- Check session-improver skill exists in one of the known locations
- Make sure no syntax errors in AGENTS.md

**Too many problems reported:**
- Show only High severity items first
- Group related items together
- Ask user which types matter most

**skill-generator not working:**
- Check skill-generator is installed and can be loaded via `skill` tool
- Pass clear, specific context about what to build
- If skill-generator has its own questions, answer them based on your analysis
