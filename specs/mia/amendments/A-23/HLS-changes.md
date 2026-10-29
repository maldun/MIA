# A-23: three places of the High-Level Specification that the owner should change by hand

The HLS is the owner's document; A-23 does not install a copy of it. REQ-BE-054 and REQ-WFM-019 are reworded (run mode by default, slices as the option `slice` and for paid models); the parent `FR-11` and two table rows still describe slices only. Proposed new wording:

1. `FR-11` (line 51): replace "she works in time slices (first 600 s), gives an intermediate report with a recommendation at the end of each, and continues only when the requesting user agrees" by
   "she works by default without a question at a limit, bounded by hard caps, and shows her progress with the figures of the budget and of the sources; in time slices (first 600 s, an intermediate report with a recommendation at the end of each, and she continues only when the requesting user agrees) when the user asks for it (option `slice`) or when the model is a paid one".
2. Latency table (line 183): "review: slices of 600 s with a question to continue" -> "review: runs to the end (local models), with a live status; slices of 600 s with a question to continue in the mode slice".
3. Budget paragraph (line 199): add "Hard caps of the mode run: the limits times 100 (configurable)." after the list of the review limits.
