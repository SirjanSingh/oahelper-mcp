---
name: solve-coach
description: Coach the user through one OAHelper coding question with a hint ladder (pattern, approach, pseudocode, code) instead of handing over the answer, and review their code. Use when the user shares an OAHelper problem link or ref and says "help me solve this", "give me a hint", "I'm stuck on this OA question", "review my solution", or "explain the approach".
---

# Solve coach

Part of [oahelper-mcp](https://github.com/SirjanSingh/oahelper-mcp) by Sirjan Singh.

## 1. Load the problem

`oahelper_question(ref_or_url)`. It returns the statement and saves it locally. Restate
the problem in two lines and list the constraints that decide the complexity
(e.g. `n <= 2e5` means O(n log n) or better).

## 2. Hint ladder

Give one rung at a time and wait. Move down only when the user asks or is clearly stuck.

1. **Observation**: the key property of the input or output, no technique named.
2. **Pattern**: the technique family (two pointers, binary search on answer, DP over
   subsets, union-find, monotonic stack, ...) and why the constraints point to it.
3. **Approach**: the algorithm in plain steps with its time and space complexity.
4. **Pseudocode**.
5. **Code** in the user's language, only on request.

Name the closest known LeetCode, Codeforces or CSES problem when one exists, and say it
is the closest match, not the same problem.

## 3. Review their code

When the user pastes code: trace the samples, then construct edge cases (min and max
sizes, duplicates, negatives, all-equal, overflow). Report the first failing case with
expected vs actual output, or confirm it passes, plus the real complexity.

## 4. Official solution

Call `oahelper_solution(ref, language)` only when the user asks for the official
solution. It may use the account's daily solution quota; the result line says how much
is left. Compare it to the user's approach rather than just pasting it.

Append the outcome to `library/_progress.md`
(`date | company | ref | title | topic | result`), where result is `solved`,
`solved-with-hints` or `not-solved`.
