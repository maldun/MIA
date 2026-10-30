# IF-404 – Web search and fetch (external), v1

Provider: external (the open web and SearXNG)   Owner: N-2.4.2 Tools and sandbox (the consumer that depends on it)   Consumers: N-2.4.2   Decided by: N-2.4   Mock complexity: 3 (scripted pages, refusals, errors)   Suite: `tests/acceptance/contract/test_if_404_web.py`

Draft v0 from `web_tools.py` (`WebClient`, `check_url`, `SearchError`, `UnsafeUrl`, `UnsupportedContent`, `HttpStatusError`). Everything that comes back is **untrusted** (`@Untrusted`).

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `search(query)` | text | list of `{url, title, content, backend}` | the query text is what leaves the host (NFR-5) |
| `fetch(url)` | an http or https address | `{"text", "hash", "bytes", "truncated"}` | at most 2,000,000 bytes, text extracted from HTML; redirects are checked again |

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| a private or local address, a port other than 80, 443, 8080 and 8443, a scheme other than http and https | `ServiceError("unsafe_url")` | no request was sent |
| a content type that is not text (images, binaries) | `ServiceError("unsupported_content")` | nothing returned |
| HTTP status 400 or more | `ServiceError("http_status", detail=status)` | nothing returned |
| the search service fails or times out | `ServiceError("search_error")` | no partial list |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| fetch size | at most 2,000,000 bytes (`truncated` true beyond) | `max_bytes` of the web client |
| timeouts | connect 5 s, read 15 s | `WebClient` default |
| requests outside | every request goes into the web log | NFR-5 |

## Golden examples
1. Typical: `search("height of the Eiffel Tower")` returns a list of findings; `fetch` of a scripted page returns text with a hash.
2. Failure: `fetch("http://192.168.1.10/admin")` is `unsafe_url` and nothing was sent; a 404 is `http_status` with 404.
3. Edge: a page larger than the limit comes back `truncated`; a link to port 22 is `unsafe_url`; port 8080 and 8443 are allowed (web servers often serve there).

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft from web_tools.py | – |
| v1 | 2026-10-30 | ports 8080 and 8443 are allowed besides 80 and 443, as in `web_tools.ALLOWED_PORTS` (owner's decision) | A-33 |
