# research: the planners (free, checked) and the pipelines around them, 3 repeats each

Run on 2026-10-19/20, light profile (gemma4:12b-it-qat). Suites: `plans` (36 plans scored on the plan alone), `research_compound` (16 compound questions over 14 recorded pages), `research` (20 questions). All starter-sized.

## The planner alone (suite `plans`)

| | plan.free@1 (A) | plan.checked@1 (B) |
|---|---|---|
| plan is as it should be | 63.9 % (69 of 108) | **91.7 % (99 of 108)** |
| number of lookups right | 77.8 % | 91.7 % |
| no word of the question lost | 93.5 % | 100 % |
| nothing asked that should not be | 90.7 % | 100 % |
| no redundant lookup | 100 % | 100 % |
| a single lookup keeps the question's own words | **25 % (5 of 20)** | 100 % (39 of 39) |
| a calculation is flagged when needed | 100 % | 100 % |
| stable over repeats | 91.7 % | 88.9 % |

Paired over the 36 questions: only free right on 3, only checked right on 14, sign test p = 0.013: **believable**. The code checks (13b ST11, `research.check_plan`) fix what the first measurement of the decomposition showed: the planner rewrites simple questions (only 25 % kept the question's words), and the router (a question with no sign of a comparison, a chain or two questions in one is simple) removes the sub-questions nobody needed. Caveat: the router and the rules were written looking at the same questions, so the number for B is an upper bound on what new questions will give.

## End to end (the checked planner inside the pipelines)

| | escalate@1 (free plan) | escalate@2 (checked plan, first version) |
|---|---|---|
| suite `research` | 91.7 % (55 of 60) | 90.0 % (54 of 60) |
| suite `research_compound` | **77.1 % (37 of 48)** | 60.4 % (29 of 48) |

Better plans did **not** give better answers on the compound questions (only escalate@1 right on 4 questions: head-offices-of-both-builders, mayor-of-builders-town, older-company-by-years, viaduct-opening-weekday; only escalate@2 right on none; p = 0.125). Single diagnostic runs showed three different causes, none of them the quality of the plan:
1. **A bug in my rule**: "a single lookup keeps the question's own words" is wrong when a calculation follows. For "On which day of the week did the Oakline Viaduct open?" the lookup must be the fact (the opening date), not the question about the weekday, which no page states. Fixed (the rule does not apply when a calculation is needed; test added). `escalate@2` was measured with the bug and needs a re-measure (variant `escalate2b`).
2. **The separate model call that names the calculation** returned `{'op': 'years_between', 'a': '', 'b': '', 'n': 1887}` for two correctly answered lookups (1887 and 1971): the arguments were wrong although the facts were right. In a typed plan the arguments are references that code resolves, and no such call exists.
3. **A free plan cannot pass a result on**: both sub-questions of "the towns of the head offices of the companies that built the two bridges" got the same query "company name head office location", because the second needs the first's answer. This is the dependent step, the reason for typed plans (13b ST10).

Lesson: a measurement of a part (the plan) can improve while the whole gets worse, because another part was relying on the old behaviour. Both levels need their own suite.
