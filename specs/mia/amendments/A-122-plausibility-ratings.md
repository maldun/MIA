# Plausibility ratings of G-V2.CONVERT after the baseline probe (owner, 2026-11-15, reviewer maldun)

Not applied: `specs/mia/plausibility.yaml` is protected and the ratings are the owner's. Decided one item at a time (D-245). Basis for 110 to 114 and 059: the probe named in their records ("record the baselines on MP-light, then judge the margin") is done (A-122, runs of 2026-11-15).

| Requirement | Rating before | Rating now | Basis to write | Claim to change |
|---|---|---|---|---|
| REQ-WFM-115 | none | plausible | exact equality of outputs of a deterministic function on all 51 cases; no model quality or measured number | – |
| REQ-WFM-110 | questionable (probe) | plausible | baseline measured 0.95 (57/60), floor 0.85 (17/20), false alarm 0.0003; REQ-WFM-058 guards small losses | `floor` 0.82 to 0.85 against REF-CONVERT-1 (value 0.95) |
| REQ-WFM-111 | questionable (probe) | plausible | baseline 0.639 (69/108), floor 0.54 (20/36), false alarm 0.0122 | none (REF-CONVERT-2 value 0.639) |
| REQ-WFM-112 | questionable (probe) | plausible | baseline 0.940 (141/150), floor 0.83 (42/50), false alarm 0.0001 | none (REF-CONVERT-3 value 0.94) |
| REQ-WFM-113 | questionable (probe) | plausible | baseline 0.974 (114/117), floor 0.87 (34/39), false alarm 0.0000 | `floor` 0.82 to 0.87 against REF-CONVERT-4 (value 0.974) |
| REQ-WFM-114 | questionable (probe) | plausible | baseline 0.680 (104/153), floor 0.59 (31/51), false alarm 0.0064 | none (REF-CONVERT-5 value 0.68) |
| REQ-WFM-059 | questionable (probe) | plausible | its own behaviour is exact; the numbers it refers to (110 to 114) are measured | – |

The `probe` entries of 059 and 110 to 114 are settled by this and can be dropped, the references REF-CONVERT-1 to 5 take the measured values (0.95, 0.639, 0.94, 0.974, 0.68; source: the five run files placed in `eval/baselines/`). Other items of REQ-WFM-057 to 070 keep their ratings (plausible; 068 proposed questionable, rated plausible on 2026-11-07, not touched).
Known limit, written once: on 20 to 51 dev cases a loss of 0.15 is missed in 36 to 65 % of the checks; REQ-WFM-058 is the guard (A-122, point 2).
