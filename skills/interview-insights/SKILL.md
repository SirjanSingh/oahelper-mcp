---
name: interview-insights
description: Turn a company's interview experiences from OAHelper into a round-by-round brief with recurring questions, what interviewers probe, and why candidates were rejected. Use when the user asks "what are X's interview rounds", "what does X ask in interviews", "how was X's interview process", "prep me for the X interview", or has an interview (not an OA) coming up.
---

# Interview insights

Part of [oahelper-mcp](https://github.com/SirjanSingh/oahelper-mcp) by Sirjan Singh.

## 1. Gather

1. `oahelper_interviews(company, pages=2)`. It saves every write-up to
   `library/<co>/interviews/`; read those files for full text, not the short list.
2. If the user named a role (SDE intern, analyst, FTE), keep only matching write-ups and
   say how many remain.
3. Fewer than 3 write-ups: say the evidence is thin and treat patterns as tentative.

## 2. Analyse

- Weight by date. Write-ups from the last 12 months decide the current process; older
  ones are background. Put the year on everything you cite.
- Round structure: how many rounds, what each tests (DSA, LLD, HLD, CS fundamentals,
  projects, HR), duration and mode where stated.
- Repeated questions: anything asked in 2 or more write-ups, with the count.
- Signals: what interviewers dug into (projects, complexity, edge cases, SQL, OOP).
- Rejection reasons people reported, and offers vs rejections in the sample.

## 3. Output

```
# <Company> interview brief (<n> write-ups, <date range>)

## Process
| Round | Focus | Duration | Seen in |

## Asked more than once
- <question or topic> (<count>, <years>)

## What sank people
## Prep checklist (5 to 10 items, most important first)
## Sources
- <file links>
```

Report only what the write-ups say. Mark anything inferred as inferred, and write
`UNKNOWN` where the data is silent. Never present one person's experience as policy.
