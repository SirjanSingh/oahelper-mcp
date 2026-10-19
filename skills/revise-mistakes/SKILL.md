---
name: revise-mistakes
description: Re-test the user on OA questions and MCQs they previously got wrong or needed hints for, using the practice log kept by the oahelper skills, with simple spaced repetition. Use when the user says "revise my mistakes", "what did I get wrong", "redo my weak questions", "review before the OA", or "spaced repetition".
---

# Revise mistakes

Part of [oahelper-mcp](https://github.com/SirjanSingh/oahelper-mcp) by Sirjan Singh.

The log is `library/_progress.md`, a table written by `oa-mock`, `mcq-drill` and
`solve-coach`:

```
| date | company | ref | title | topic | result |
```

If it does not exist, say there is nothing to revise yet and suggest `mcq-drill` or
`oa-mock` to start one.

## 1. Pick what is due

Take the latest row per `ref`. Due when:

| Latest result | Due after |
|---|---|
| wrong, not-solved, too-slow | 1 day |
| solved-with-hints | 3 days |
| correct after a previous miss | 7 days |
| correct twice in a row | retired, skip |

Sort due items oldest first. Default session: up to 10 items, or what the user asks for.
Filter by company or topic if the user names one.

## 2. Re-test

- Load each item from its saved file in `library/<co>/questions/` (no network).
- MCQ: ask it fresh without the earlier answer, then mark it.
- Coding: give the statement and ask for the approach in a few lines plus complexity.
  Full code only if the user wants. Judge the approach, not the syntax.
- After each item, give the one idea that was missing last time.

## 3. Close

Append a new row per item with today's date and the new result. Then report:

```
Revised <n>: <k> now correct, <m> still weak
Still weak: <topics>
Next due: <date> (<count> items)
```
