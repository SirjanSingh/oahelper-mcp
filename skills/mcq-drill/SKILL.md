---
name: mcq-drill
description: Quiz the user one MCQ at a time from a company's real OA multiple-choice questions and answer keys saved by the oahelper MCP server, with scoring and explanations. Use when the user says "quiz me", "MCQ practice for X", "drill aptitude", "test me on X's MCQs", or wants to revise CS fundamentals, aptitude or output-prediction questions from past OAs.
---

# MCQ drill

Part of [oahelper-mcp](https://github.com/SirjanSingh/oahelper-mcp) by Sirjan Singh.

## 1. Load questions

1. `oahelper_offline(company)`. If there are no MCQ sets saved, `oahelper_sync(company)`.
2. MCQ answer keys live in the question files under `library/<co>/questions/`, in the
   `## MCQ answers` section. Read those files; do not refetch.
3. If the user named a topic (OS, DBMS, networks, aptitude, output prediction, SQL),
   filter to it. Otherwise draw from the newest sets first.
4. Skip questions marked correct in `library/_progress.md` unless the user asks for a
   full pass.

## 2. Drill loop

- Ask one question at a time: stem and options, with the number (e.g. `Q4 of 15`).
  Default length 15 unless the user picks another.
- Never reveal the answer before the user commits to one. Accept letters or option text.
- After each answer: correct or not, the right option, and a 1 to 3 line explanation.
  Use the saved explanation when present; otherwise write your own and say so.
- If the saved key looks wrong, say so plainly with your reasoning instead of defending it.
- Keep a running score. The user can say "stop" at any point.

## 3. Wrap up

```
Score: <correct>/<attempted>
Missed by topic: OS 2, DBMS 1, ...
Review these: Q3 (paging), Q9 (normal forms), ...
```

Append each attempt to `library/_progress.md`
(`date | company | ref | title | topic | result`), creating it with that header if needed.
