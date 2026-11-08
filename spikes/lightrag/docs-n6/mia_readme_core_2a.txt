## Core, phase 2a: the web tools (search and page fetcher, safety rules)

`web_tools.py` gives the pipelines two tools, `web_search` (budget key `search_calls`) and `fetch_page` (`fetch_calls`); a skill lists them under `tools:`.

- **Search**: backends in order, `search_backends` (default `["searxng", "duckduckgo"]`). A backend that fails or finds nothing hands over to the next; the answer says which
  one was used, what failed and which engines SearXNG could not reach. Duplicates (same page with tracking parameters, `www.`, fragments) are merged, results that point to
  private addresses are dropped. "Nothing found" is an answer, not an error; only "no backend answered" is an error.
- **SearXNG** (self-hosted, the first choice): `tools/searxng/run.sh` starts it with podman or docker on `127.0.0.1:8590` (`stop`, `check` also exist). Its settings enable the
  JSON output. Upstream engines (Brave, DuckDuckGo, ...) sometimes throttle it; `check` and the status block show that. Settings: `searxng_port` (default 8590, used by MIA and by `run.sh`; 8888 is taken by too many other programs) or `searxng_url` for another address.
  It is not started by MIA and does not restart with the machine unless you set that up (the image is about 270 MB).
- **DuckDuckGo** (the fallback): no install; it reads the HTML result page (there is no official free API), waits at least 1.5 s between requests and reports a CAPTCHA or rate limit.
- **Fetching** (`WebClient`): only http(s) to public addresses on ports 80, 443, 8080, 8443; the address is checked before the connection, at every redirect (at most 4) and for the
  address that was really connected. Blocked: localhost, the LAN, the tailnet (100.64.0.0/10, `.ts.net`), link-local and cloud metadata addresses (169.254.169.254), IPv6 private ranges,
  names without a dot or ending in `.local`/`.internal`, addresses with a user name. Limits: 5 s connect, 15 s read, 2 MB, content types html/plain/json/xml, no cookies, no scripts.
- **Text from pages**: scripts, styles, menus and **hidden elements** (`display:none`, `hidden`, `aria-hidden`, font size 0) are dropped, because hidden text is a favourite place for
  instructions aimed at models. `chunk_text` cuts long pages at paragraph breaks.
- **Web text is data** (X1): `untrusted()` wraps it in delimiters that the page cannot close, `injection_signals()` flags phrases like "ignore previous instructions" (shown in the
  status block and logged; a hint, not the protection: the protection is narrow tools and schemas in the stages that read the web).
- **What MIA asked the internet** (X4): every search and fetch is a line in `data/runs/web-YYYY-MM.jsonl` (query, backend, results, errors, URL, status, bytes, timing).
- Other keys (optional): `web_timeout` (`[5, 15]`), `web_max_bytes`, `web_max_chars`, `search_results`.
- Try it without MIA: `python tools/try_search.py "query"`, `--fetch 2` to read the first results, `--url ...`, `--backends duckduckgo`, `--safety` (shows what is blocked).
- Tests: `tests/test_web_tools.py` (no network; fakes for sessions and name resolution).
- A limit worth knowing: the check of the connected address uses the socket of the connection when the library gives it, and the name is resolved by the system a second time when
  the connection is made. A name that changes its address between the two lookups is therefore caught by the connected-address check, not by the first one.

