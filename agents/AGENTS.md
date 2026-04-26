# Agent Constitution

## MOST IMPORTANT RULES

- RULE 1: Never assume anything. Always ask if something is not clear. Try to search the web first.
- RULE 2: Tool recovery - If you call the same tool many times without success, try a different approach. If you are still stuck, tell the user, suggest fixes, and wait for instructions.
- RULE 3: Parallel agents - Always try to use multiple agents at the same time. Use the `parallel-explorer` skill for codebase analysis.
- RULE 4: TDD - Follow the RED (test fails), GREEN (test passes), REFACTOR (clean up) approach.
- RULE 5: Standards - Follow language and framework best practices. Use SOLID, DRY, KISS, YAGNI, and clean code principles.
- RULE 6: Always use context7 to look up documentation. Prefer it over web search.
- RULE 7: Write guard - Before every `write` call, load the `write-guard` skill to check the parent folder exists and path is valid.
- RULE 8: Bash precheck - Before every `bash` call, load the `bash-precheck` skill to check tools are installed, files exist, and working directory is correct.

<!-- context7 -->
Use Context7 MCP to get current documentation when the user asks about a library, framework, SDK, API, CLI tool, or cloud service — even well-known ones like React, Next.js, Prisma, Express, Tailwind, Django, or Spring Boot. This includes setup help, API details, version changes, debugging, and CLI usage. Use even when you think you know the answer — your training data may not be up to date. Prefer this over web search for library docs.

Do not use for: refactoring, writing scripts from scratch, debugging business logic, code review, or general programming concepts.

## Steps

1. Always start with `resolve-library-id` using the library name and the user's question, unless the user gives an exact library ID in `/org/project` format
2. Pick the best match (ID format: `/org/project`) by: exact name match, description relevance, code snippet count, source reputation (High/Medium preferred), and benchmark score (higher is better). If results look wrong, try different names (e.g., "next.js" not "nextjs"). Use version-specific IDs when the user says a version
3. Call `query-docs` with the selected library ID and the user's full question
4. Answer using the fetched docs
<!-- context7 -->

## Parallel Task Delegation Guidelines

- For codebase analysis, always launch multiple explore agents (frontend, backend, routes) at the same time
- Each agent should have a narrow focus to avoid overlap
- Combine results from all agents before making decisions
- Use the `task` tool with different `subagent_type` values

## Prompt Quality Guidelines

### Length and Structure
- Keep prompts between 200-1500 characters for best results
- Use clear sections: goal | context | constraints | expected output
- Include file paths and line numbers when talking about code
- Do not use single-word or short confirmations; add context

### Prompt Template for Complex Requests
---description: Short task description
agent: build
---

Goal: What you want
Context: File paths, existing code, limits
Expected Output: What to deliver

### Planning Before Execution
- For multi-step tasks, break them into steps first
- Ask questions before jumping into code
- Include file paths and line numbers

## Session Improvement Hook

After finishing any big task (code generation, debugging, file changes, multi-step work), briefly check if there were slow spots or missed chances to automate. If you find patterns that could be improved with a skill, offer to run the `session-improver` skill. Do not run it on every small task — only after meaningful ones.

Look for:
- Many tool calls for simple work that could be combined into one skill
- Reading or writing the same files across different tasks
- User asking about project structure or rules more than once
- Tasks that took longer than they should have
- Same commands run multiple times
- Task got interrupted

When you find improvement chances:
1. Show at most 3-5 findings (start with high-severity items)
2. For each, explain what could be automated and how long it would take
3. Ask if the user wants to create skills for any of them
4. If yes, use `skill-generator` to make targeted skills
