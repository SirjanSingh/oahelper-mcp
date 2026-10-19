---
name: study-plan
description: Build a day-by-day study plan to the user's OA or interview dates from the company patterns saved by the oahelper MCP server and their past practice results. Use when the user says "make me a study plan", "I have X's OA on <date>", "how should I prepare in N days", "schedule my prep", or lists upcoming OA and interview dates.
---

# Study plan to the OA date

Part of [oahelper-mcp](https://github.com/SirjanSingh/oahelper-mcp) by Sirjan Singh.

## 1. Inputs

Ask only for what is missing, in one message:
- Companies and their OA or interview dates (and time zone if close).
- Hours available per day.
- Weak areas the user already knows about (optional).

Use today's date from the environment, not a guess.

## 2. Evidence

1. For each company, `oahelper_offline(company)`; sync only if nothing is saved.
2. Read the newest sets to get the format and topic mix (follow `oa-compare` if there
   are several companies).
3. Read `library/_progress.md` if it exists: topics with misses or `solved-with-hints`
   get extra time, topics solved cleanly get less.

## 3. Plan rules

- Earliest deadline first. The day before each OA is a light day: one timed `oa-mock`
  and a review, nothing new.
- Every day has: one focused topic block, practice from that company's real questions
  in the library, and 10 to 15 minutes of `mcq-drill` if the company's OAs include MCQs.
- Put a full `oa-mock` roughly every 3 to 4 days.
- Each item names a concrete question file or a known LeetCode problem, not just a topic.
- Fit the user's hours. If everything does not fit, cut the lowest-frequency topics and
  say what was cut.

## 4. Output

```
# Prep plan: <companies>, <today> to <last date>

| Date | Focus | Practice (links) | Time |

Cut for time: ...
```

Save it as `prep/study-plan-<today>.md` (or where the user keeps notes) and offer to
update it after each mock.
