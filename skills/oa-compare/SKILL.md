---
name: oa-compare
description: Compare the online-assessment patterns of several companies from OAHelper (question count, coding vs MCQ split, difficulty, topics, recency) to decide what to study first or which OAs overlap. Use when the user says "compare X and Y OAs", "which of these companies' OAs are similar", "what topics are common across my upcoming OAs", or lists several companies they are applying to.
---

# Compare OAs across companies

Part of [oahelper-mcp](https://github.com/SirjanSingh/oahelper-mcp) by Sirjan Singh.

## 1. Gather (cheap first)

For each company:
1. `oahelper_offline(company)`. Use the saved pack when it exists.
2. If not saved, `oahelper_search(company)` (one request) gives set dates, counts and
   question types. That is enough for the comparison table. Only run `oahelper_sync`
   if the user wants topic-level detail, and cap it at about 20 requests per company.

Ask before syncing more than 4 companies in one go; it burns the daily cap.

## 2. Compare

Use sets from the last 12 months; fall back to older ones and flag it.

| Column | From |
|---|---|
| Sets in last 12 months | set dates |
| Questions per OA | set question counts |
| Coding / MCQ / SQL split | question types |
| Typical difficulty | difficulty scores of saved questions |
| Top topics | question titles, tags and statements |
| Latest set | newest date |

## 3. Output

1. The table above, one row per company.
2. **Shared topics**: topics that appear in 2 or more companies, ranked by how many.
   These are the highest-leverage things to study.
3. **Company-specific**: anything only one company tests (e.g. SQL only at X).
4. **Study order**: a short ranked list, factoring in the OA dates if the user gave them.

Say where data is thin (one set, old sets, no saved questions). Write `UNKNOWN` instead
of guessing a number.
