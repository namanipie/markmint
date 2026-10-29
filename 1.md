# Antigravity AI Brain

A simple memory architecture designed to reduce unnecessary token usage in AI coding tools.

## Files

- `AI_BRAIN.md` — persistent compressed project memory
- `AI_RULES.md` — rules telling the AI when it may read source files
- `SESSION_MEMORY.md` — temporary working memory for the current task

## Recommended Antigravity Instruction

Paste the following into your project's permanent AI instructions:

```text
TOKEN-EFFICIENT PROJECT MEMORY MODE

At the beginning of every task, read AI_RULES.md and AI_BRAIN.md before inspecting source code.

AI_BRAIN.md is the project's persistent compressed memory and should be used for architecture, previous decisions, project state, known files, completed features, and recent changes.

Do not recursively scan or reread the entire repository unless it is genuinely necessary.

For each task:
1. Read AI_RULES.md.
2. Read AI_BRAIN.md.
3. Determine the smallest set of files necessary.
4. Search for exact symbols/files before opening unrelated files.
5. Read the actual target source files before editing them.
6. Make minimal changes.
7. Run relevant validation/tests.
8. Update AI_BRAIN.md after meaningful changes.
9. Store temporary reasoning/context in SESSION_MEMORY.md instead of bloating permanent memory.

Never trust memory over source code when exact implementation details matter. If AI_BRAIN.md conflicts with the source, source code wins and the brain must be corrected.

Never read node_modules, dist, build output, generated assets, lockfiles, or unrelated directories unless explicitly required.

The objective is to minimize context usage without sacrificing correctness.
```

## Suggested Project Layout

```text
project/
├── AI_BRAIN.md
├── AI_RULES.md
├── SESSION_MEMORY.md
├── src/
├── backend/
└── ...
```

## How It Saves Tokens

Instead of repeatedly loading dozens of project files, the AI starts with a compact project summary and opens only the files required for the current request.

Important: this cannot guarantee that an AI tool will *never* read other files. Exact code changes still require reading the real source file. The purpose is to prevent unnecessary repeated repository-wide scans.
