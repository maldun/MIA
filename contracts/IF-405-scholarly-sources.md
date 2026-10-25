# IF-405 – Scholarly sources (external), v0

Provider: external (OpenAlex, Crossref, PubMed, arXiv, and Semantic Scholar with a key)   Owner: N-2.4.2 Tools and sandbox (the consumer that depends on it)   Consumers: N-2.4.2   Decided by: N-2.4   Mock complexity: 3 (scripted works, the strict cut-off, a failing source)   Suite: `tests/acceptance/contract/test_if_405_scholarly_sources.py`

Draft v0 from `scholar.py` (rules S1 to S5). Everything that comes back is **untrusted** (`@Untrusted`).

## Operation
`search(query, until=None, since=None)` returns `{"works": [work], "errors": [{"source","message"}], "dropped": [{"ref","reason"}]}`.

A work is one record format for all sources: `doi, title, abstract, date ("2001", "2001-11" or "2001-11-22"), year, venue, authors, cited_by, work_type, oa_url, sources, ids, pub_types, retraction {"status","notices","hints"}`.

Rules: the cut-off is strict: a work counts as published up to `until` only if the **latest day its date could mean** is not after `until`; a work without a date is dropped when a cut-off is given (reason `no_date` or `after_cutoff`). Works found by several sources appear once (same DOI or same title), with `sources` listing all. One failing source never stops the others (S5).

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| one source fails or is rate limited | an entry in `errors`; the other sources' works are returned | the answer is partial and says so |
| all sources fail | `works` empty and `errors` for each | no exception |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| what leaves the host | the query text; an e-mail address only if configured | NFR-5 |
| politeness | one request per host at a time, one retry after 429 or 503 | S1 |

## Golden examples
1. Typical: a query returns works in one format, de-duplicated by DOI.
2. Failure: one source raises an error: its error is listed, the works of the others are returned.
3. Edge: `until="2001-11-22"`: a work dated "2001-11-22" counts, "2001-11" counts only if November ends not after that day (it does not), "2001" is dropped with `after_cutoff`, a work without date is dropped with `no_date`.

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft from scholar.py | – |
