# Vendored files of the Graph app

The Graph app loads its graph library from this folder only (REQ-GA-009, REQ-GA-010): no CDN, no npm, no build step.
The file is used unchanged; replacing it is a new dependency decision of the owner (D-124).

| File | Library | Version | Licence | Size (bytes) | sha256 |
|---|---|---|---|---|---|
| `vis-network.min.js` | vis-network, standalone UMD build (defines the global `vis`, injects its own CSS) | 10.1.2 (released 2026-08-19) | Apache-2.0 or MIT (dual, the user's choice; header of the file) | 652000 | `fc674cfa6cceb27a3b40ff4ea75c204a2d8570fb39b9a627127cf7039e141ad4` |

- Source: https://cdn.jsdelivr.net/npm/vis-network@10.1.2/standalone/umd/vis-network.min.js (fetched 2026-10-31; the sha256 matches the hash jsDelivr lists for the npm package).
- Project: https://github.com/visjs/vis-network
- The file ends with a `sourceMappingURL` comment; the map is not vendored. Browsers only ask for it while the developer tools are open, and then from this folder (a 404), never from outside.
- Check: `sha256sum graph_app/vendor/vis-network.min.js` (also checked by `tests/js/graph-app-files.test.mjs`).
