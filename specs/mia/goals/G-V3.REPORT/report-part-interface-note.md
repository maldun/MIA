# Interface note: the Report part of the Full run (G-V3.REPORT, T-04; checks TC-CLV-048, 050, 051, 052)

The browser checks read the page only through these hooks (as the checks of G-V3.PANEL do, `skill-run-view-interface-note.md`). T-04 builds the part with them; a check never reads anything else.

| Hook | What it is | Rule |
|---|---|---|
| `details#srv-report` | the expandable Report part, inside the Full run (`details#srv-full`) | present for every run that is shown; it may open by itself when the run has ended (open point 1 of A-154), the checks open it only if it is closed |
| `#srv-report > summary` | its summary line | holds `#srv-report-state` |
| `#srv-report-state` | the state of the run in words | attribute `data-state` is the state of the record: `running`, `paused`, `done`, `failed` or `stopped` |
| `#srv-report-body` | the rendered report | filled from the file named in `record.report`, fetched as text from `/api/files/<name>`; rendered by `renderReport` (REQ-CLV-049, 052); empty while there is no report |
| `a#srv-report-download` | the download link | `href` is `/api/files/<encoded name>` of the report; absent while the run has no report and where the file is gone |
| `#srv-report-note` | the sentence for the two states without a report | attribute `data-kind` is `waiting` (the record's `report` is empty: the report comes when the run ends, REQ-CLV-050) or `removed` (the file is not in the volume any more, a 404 on the fetch, REQ-CLV-051); absent or `hidden` otherwise |

The page asks again for the report when `skill_run_changed` arrives for the shown run (the record is read as today), so a run that ends fills the part without a reload (REQ-CLV-050). The wording of the two sentences and of the summary line is not fixed by a check: the checks read `data-state` and `data-kind`.

The stand-in skill of the checks is the stub server `ui/tools/skill_run_stub_server.py`: the steps `{"file": {"name", "data"}}` and `{"file_deleted": name}` put a file into the files volume of its mock or take it out.
