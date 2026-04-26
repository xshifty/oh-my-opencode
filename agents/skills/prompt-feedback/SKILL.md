---
name: prompt-feedback
description: Looks at your last 10 OpenCode sessions to see how you write prompts. Finds problems like short or unclear prompts and suggests how to improve.
license: Apache-2.0
compatibility: opencode
metadata:
  audience: developers
  workflow: custom
---

## What I Do

- Get prompts from the last 10 OpenCode sessions
- Look at prompt length, category types, and how well they are written
- Find patterns like very short prompts, missing details, or messy format
- Create new AGENTS.md rules or tips to help you write better prompts
- Suggest specific fixes to make your prompts clearer and more useful

## When to Use Me

- User asks for "prompt analysis", "improve my prompts", or "prompt quality report"
- After running the session insights dashboard (adds deeper prompt analysis)
- When user gets mixed or bad results from the agent
- Every 10-20 sessions as part of regular checkup

## How to Use Me

### Step 1: Get Recent Prompts

Run the analyzer with `--recent` flag:

```bash
PROMPTS=$(python3 ~/.agents/skills/insights/session_analyzer.py --recent 2>/dev/null)
```

From the JSON output, read:
- `prompt_count`: Total prompts in last 10 sessions
- `avg_prompt_length`: Average character count
- `longest_prompt.text` and `.length`: Longest prompt example
- `shortest_prompt.text` and `.length`: Shortest prompt example
- `categories`: Breakdown by type (question, task, debugging, code_review, planning, other)
- `prompts_sample[]`: Recent prompts with session_id and text_preview

### Step 2: Check Prompt Quality

Look at these things:

**Length Variance:**
- Compare: longest_prompt.length / avg_prompt_length
- If > 5x difference: mark as "highly uneven prompt lengths"
- If shortest is empty or < 10 chars: mark as "very short prompts found"

**Category Mix:**
- High "other" count (>40%): suggests unclear what the user wants
- Low "planning" count (<5%): user skips planning steps
- High "question" with low "task": more exploring than building

**Structure Quality (from text_preview):**
- Prompts without file paths or line numbers: mark as missing details
- Single word prompts ("yes", "go ahead"): mark as too short
- Prompts with clear sections or bullet points: mark as good pattern

### Step 3: Create Feedback Rules

Based on what you find, write targeted rules. Examples:

**If high length variance:**
```markdown
## Prompt Quality Guidelines
- Keep prompts between 200-1500 characters for best results
- Use clear sections: goal | context | constraints
- Avoid single-word prompts; include file paths and line numbers
```

**If low planning category:**
```markdown
## Planning Before Execution
- For multi-step tasks, break down into steps first
- Include expected output for each step
- Ask questions before jumping into code
```

**If many unclear prompts:**
```markdown
## Structured Prompt Format
Use this for complex requests:
---description: Brief task description
agent: build
---

Goal: What you want
Context: File paths, line numbers, existing code
Constraints: Limits or requirements
Expected Output: What to deliver
```

### Step 4: Show Results

Show user a summary like:

```
Prompt Quality Analysis (Last 10 Sessions)

Metrics:
- Prompts checked: {prompt_count}
- Average length: {avg_prompt_length} chars
- Length variance: {variance_ratio}x (longest / average)
- Categories: Question ({q}), Task ({t}), Other ({o})

Issues Found:
1. High length variance — prompts from 0 to {max_len} chars
2. {count} very short prompts (< 50 chars)
3. Low planning category ({p}% of prompts)

Suggested AGENTS.md Additions:
{generated_rules}
```

Ask user if they want to:
- Add rules to their AGENTS.md file
- Create a prompt template skill for consistent formatting
- Run analysis again after making changes

## Guidelines

- Always check the last 10 sessions for recent patterns
- Be specific about problems; avoid generic advice like "be more detailed"
- Show real prompt examples from the user's history when you can
- Create ready-to-use markdown snippets for AGENTS.md
- If prompt quality is good, say so positively
- Do not change AGENTS.md without asking the user first

## Examples

### Example 1: High Variance Found
```
Prompt Quality Analysis (Last 10 Sessions)

Metrics:
- Prompts checked: 37
- Average length: 1,237 chars
- Length variance: 10.3x (longest/average)
- Categories: Question (14), Task (8), Other (14)

Issues Found:
1. High length variance — prompts from 0 to 12,716 chars
2. 5 very short prompts ("yes", "go ahead", "try again")
3. Low planning category (1/37 = 2.7%)

Suggested AGENTS.md Additions:
- Prompt Quality Guidelines section with length limits
- Structured prompt template for complex requests
```

### Example 2: Good Prompt Quality
```
Prompt Quality Analysis (Last 10 Sessions)

Your prompts show good quality:
- Average length: 850 chars, max variance only 3x
- Good task mix (60% tasks, 25% questions)
- Most prompts include file paths and clear goals

No changes needed — keep up the good work!
```

## Troubleshooting

**Analyzer returns no recent sessions:**
Check that `session_analyzer.py` is at `~/.agents/skills/insights/session_analyzer.py`. If not, guide user to install it.

**Not enough data (< 5 prompts):**
Need more sessions for useful analysis. Suggest running again after 5+ more sessions.

**Unclear categories:**
The analyzer may group some prompts wrong. Focus on length and structure — these are easier to measure.
