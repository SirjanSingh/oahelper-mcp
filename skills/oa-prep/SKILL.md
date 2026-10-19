---
name: oa-prep
description: Build or update an online-assessment (OA) and interview prep guide for one company from your OAHelper Pro account (the `oahelper` MCP server) plus public sources. Use when the user says "prep me for X", "make a prep guide for X", "what does X ask in the OA", "X OA questions", or names a company with an upcoming OA or interview.
---

# OA prep from OAHelper

OAHelper content comes from the `oahelper` MCP server. Its library at
`<server folder>/library/<company>/` is the offline source of truth: read the files there
rather than re-fetching.

OAHelper's terms forbid bots and redistribution, and the penalty can be losing Pro. Fetch
one company at a time, only when asked. Never copy library content into anything that
leaves this machine (posts, GitHub, shared docs).

## Steps

1. **Offline first.** `oahelper_offline(company)`. If the pack exists and is under a week
   old, go to step 3.
2. **Sync.** `oahelper_sync(company)`, repeated while it says `NOT DONE`, capped at about 60
   live requests for one guide. If the search shows the company under a different
   `unique_company_name`, sync that name. Leave `include_images` off unless a statement
   says its screenshots carry the only copy of the input or the options.
3. **Read the pack.** Start with `library/<co>/index.md`, then the sets, questions and
   interviews. Weight by date: the last 12 months decide the format; older sets are
   pattern evidence only. Put the year on every item you cite.
4. **Add public sources**: LeetCode Discuss, GeeksforGeeks interview experiences, the
   company's own careers pages. Search before asserting anything about the hiring process.
5. **Official solutions** (`oahelper_solution`) only for the few coding questions where
   the approach is not obvious. Solve the rest yourself and label them as your own.
6. **Write the guide** to `prep/<co>-oa-prep.md` (or wherever the user keeps prep notes).
   If a guide already exists, add a `## From OAHelper (<date>)` section instead of a
   second file.

## Guide format

- Header: role, OA date and time if known, how the guide was compiled and when.
- `## What the evidence supports`: a table of the newest reports (date, setting, format,
  source), then the converged picture: question count, time limit, scoring, topic mix.
- Every past OA question: one line with its set name and date, the topic, the closest
  known LeetCode or CSES problem, and a link to the saved file.
- MCQ section: recurring themes from the answer keys, with a few representative
  questions and their answers.
- Interview rounds from the experience write-ups: what each round tests, what sank people.
- A time-boxed study plan when the OA date is known.
- `## Sources`: OAHelper URLs from the file headers, plus public links.

Write unknown values as `UNKNOWN`; never guess.
