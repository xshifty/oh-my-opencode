---
name: context7-mcp
description: Gets up-to-date library docs, code examples, and API references. Use this when the user asks about a framework like React, Next.js, Prisma, or any other tool.
license: Apache-2.0
compatibility: opencode
metadata:
  audience: developers
  workflow: documentation
---

When the user asks about libraries, frameworks, or needs code examples, use Context7 to get fresh documentation instead of guessing from old training data.

## When to Use This Skill

Use this skill when the user:

- Asks setup or config questions ("How do I set up Next.js middleware?")
- Wants code using a library ("Write a Prisma query for...")
- Needs API reference ("What are the Supabase auth methods?")
- Mentions a specific framework (React, Vue, Svelte, Express, Tailwind, etc.)

## How to Get Docs

### Step 1: Find the Library

Call `resolve-library-id` with:

- `libraryName`: The name of the library from the user's question
- `query`: The user's full question (helps find better results)

### Step 2: Pick the Best Match

From the results, choose based on:

- Closest name match to what the user asked for
- Higher benchmark scores = better docs quality
- If the user said a version (e.g., "React 19"), pick a version-specific ID

### Step 3: Get the Docs

Call `query-docs` with:

- `libraryId`: The library ID you picked (e.g., `/vercel/next.js`)
- `query`: The user's specific question

### Step 4: Use the Docs

Use the fetched docs to answer:

- Answer with current, correct information
- Include relevant code examples
- Mention the library version if it matters

## Guidelines

- **Be specific**: Pass the user's full question for better results
- **Watch versions**: When users mention versions ("Next.js 15", "React 19"), use version-specific library IDs
- **Prefer official sources**: Pick official packages over community forks when you have a choice
