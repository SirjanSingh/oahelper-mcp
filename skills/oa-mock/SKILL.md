---
name: oa-mock
description: Run a timed mock online assessment for one company using real past questions saved by the oahelper MCP server, then grade it. Use when the user says "mock OA for X", "give me a practice test", "simulate X's assessment", "test me like the real OA", or wants timed practice before an upcoming OA.
---

# Mock OA from past questions

Part of [oahelper-mcp](https://github.com/SirjanSingh/oahelper-mcp) by Sirjan Singh.

## 1. Build the paper

1. `oahelper_offline(company)`. If nothing is saved, run `oahelper_sync(company)` until it
   stops saying `NOT DONE` (or about 40 live requests, whichever comes first).
2. Read `library/<co>/index.md` and the newest 2 or 3 set files. Copy the real format:
   number of coding vs MCQ questions, and the time limit if the sets or interview
   write-ups state one. If no time limit is known, use 90 minutes for 2 to 3 coding
   questions and 1 minute per MCQ, and say it is an assumption.
3. Pick questions the user has not attempted (check `library/_progress.md` if it exists).
   Prefer sets from the last 12 months. Mix difficulties like the real sets do.
4. Never show answers, official solutions or MCQ keys while the mock is running.

## 2. Run it

- Tell the user the format, the number of questions and the end time, then show all
  questions at once like a real OA. Give statements, constraints and sample I/O only.
- Ask them to paste code or answers, in any order, and to say "submit" when done.
- Do not give hints during the mock. If they ask, remind them it is a mock and offer
  hints after submission.

## 3. Grade it

For each coding question:
- Read their code against the statement. Trace it on the sample tests and on 2 or 3
  edge cases you construct (empty input, max constraints, duplicates, negatives).
- Verdict: likely accepted, wrong answer (show the failing case), or too slow (give the
  complexity and the constraint it breaks).
- Fetch `oahelper_solution` only if the user asks for the official one; it may use quota.

For MCQs: compare to the saved answer key. For each miss, give the correct option and a
one-line reason.

## 4. Report

```
Mock: <company>, <n> questions, <time used> of <time limit>
Score: <solved>/<coding>, <correct>/<mcq>
| # | Question | Topic | Result | Note |
Weakest topics: ...
Next: 2 or 3 concrete practice items
```

Append one row per question to `library/_progress.md`
(`date | company | ref | title | topic | result`), creating it with that header if needed.
