---
name: skill-generator
description: Helps you create new OpenCode skills step by step. Asks questions, checks the name and description are correct, then writes the full SKILL.md file for you.
license: Apache-2.0
compatibility: opencode
metadata:
  audience: developers
  workflow: agent-skill-creation
---

## What I Do

Help users create new OpenCode Agent Skills through simple questions. Ask about what the skill should do, its limits, and who will use it. Check that everything follows OpenCode's SKILL.md rules. Write a complete, well-organized `SKILL.md` file ready to use.

## When to Use Me

Use this skill when the user:

- Wants to create a new OpenCode agent skill
- Says "create a skill", "make a skill", "generate a skill", or similar
- Asks how to structure a new SKILL.md file
- Needs help turning an agent workflow into a reusable skill

## How to Use Me

### Step 1: Ask Questions One at a Time

Ask the user questions one by one. Wait for their answer before asking the next. Do not ask everything at once.

**Questions to ask (in order):**

1. **What should this skill do?**
   - Ask for a short description of what the skill does
   - Keep under 1024 characters

2. **What is the skill name?**
   - Must match: `^[a-z0-9]+(-[a-z0-9]+)*$`
   - Lowercase letters, numbers, and single hyphens only
   - No hyphens at start or end, no double hyphens (`--`)
   - Must be 1-64 characters long
   - This will also be the folder name

3. **Where should it go?**
   - Option A: In the project → `.opencode/skills/<name>/SKILL.md`
   - Option B: Global → `~/.agents/skills/<name>/SKILL.md` (recommended)
   - Let the user choose

4. **What must the skill do? (Requirements)**
   - List the main tasks and abilities
   - These go in the "What I do" section

5. **What must the skill NOT do? (Limits)**
   - List rules, things to avoid
   - These go in the "Guidelines" section

6. **Who is it for?**
   - Developers, maintainers, DevOps, QA, etc.
   - This fills in `metadata.audience`

7. **What type of work is this?**
   - e.g., `github`, `testing`, `deployment`, `code-review`
   - This fills in `metadata.workflow`

8. **Any special tools or MCPs to use?**
   - e.g., `git`, `playwright`, `context7-mcp`, custom tools
   - Mention in "How to use me" section

9. **Any example situations?**
   - Real examples of when the skill would be used
   - These go in "Examples" section

### Step 2: Check Answers

Before creating the file, check everything:

- **Name**: Must match `^[a-z0-9]+(-[a-z0-9]+)*$`. Reject uppercase letters, underscores, spaces, or double hyphens.
- **Description**: Must be 1-1024 characters. Remove extra spaces before counting.
- **Folder name**: Must match the skill name exactly.

If something is wrong, explain the problem and ask the user to fix it. Do not continue until everything is correct.

### Step 3: Create SKILL.md

Build a complete `SKILL.md` file with this structure:

```markdown
---
name: <skill-name>
description: <description>
license: Apache-2.0
compatibility: opencode
metadata:
  audience: <audience>
  workflow: <workflow>
---

## What I Do
- List main tasks from the Q&A
- Use bullet points for clarity

## When to Use Me
- Describe when this skill should start
- Include example triggers or situations

## How to Use Me
### Step 1: <step name>
- Detailed instructions for the first step
- Include tool calls, commands, or workflows

### Step 2: <step name>
- Continue with more steps...

## Guidelines
- List rules and limits from the Q&A
- Start each line with `-`
- Include best practices for this skill

## Examples
<!-- Add examples if the user provided any -->

## Troubleshooting
<!-- Add common problems and fixes if needed -->
```

### Step 4: Write the File

Save the `SKILL.md` to the right place. Use full paths for global, relative for project-local.

### Step 5: Confirm and Offer Review

After saving, show:
- Skill name and description
- Where the file was saved
- List of sections included

Offer to:
- Review or change any section
- Add more detail to specific areas
- Create more skills based on the same needs

## Validation Rules (Self-Check)

Before writing the final SKILL.md, check:

1. **Name format**: `echo "<name>" | grep -qE '^[a-z0-9]+(-[a-z0-9]+)*$'`
2. **Description length**: Count characters after trimming spaces (must be 1-1024)
3. **Folder match**: Folder name must equal skill name exactly
4. **Frontmatter required fields**: `name` and `description` must be present and valid
5. **No duplicate names**: Check if the name already exists in:
   - `.opencode/skills/`
   - `~/.config/opencode/skills/`
   - `.agents/skills/`
   - `~/.agents/skills/`

If a duplicate exists, warn and ask if they want to replace it or pick a different name.

## Guidelines

- Be friendly — ask one question at a time and wait for answers
- If the user gives all details up front, you can skip some questions and just confirm
- Always check before creating; never write invalid SKILL.md files
- Suggest improvements if the description is too vague or too long
- Use Apache-2.0 license unless the user wants something else
- Default audience to "developers" if not specified
- Default workflow to "custom" if not specified
