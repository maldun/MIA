# Vendored libraries of the chat page

The chat page loads **nothing from the internet** (see `ui/REQUIREMENTS_CHAT.md`, principle 7). These libraries are served by MIA itself
with fixed versions. They come unchanged from the npm packages below, with two exceptions: `.mjs` is renamed to `.js` (Python 3.10 does not
know the `.mjs` type, browsers refuse such module scripts) and the trailing `sourceMappingURL` comment is removed (the map files are not shipped).

| Library | Version | License | File here | From the package | SHA-256 of the file | SHA-256 of the package |
|---|---|---|---|---|---|---|
| socket.io-client | 4.7.5 | MIT ([text](licenses/socket.io-client.LICENSE)) | `socket.io.esm.min.js` | `dist/socket.io.esm.min.js` | `6ff784dcad2e6bb7956924c80e40ad39ce460420a41a16030813153ddfa6ce4e` | `7edcce1563010138d40d1a61275557d95aea5f94ed595ec4d99cae2bf4ccc7c8` |
| marked | 12.0.2 | MIT ([text](licenses/marked.LICENSE.md)) | `marked.esm.js` | `lib/marked.esm.js` | `fae1ea526332deb9fbf219fc3c9d504888351a1870c03f493cad856064c8c90e` | `6cfd2d09c6bce2541558a1547e5f3b9895ed743f0d287536ff2280e318e8a074` |
| DOMPurify | 3.1.6 | MPL-2.0 OR Apache-2.0 ([text](licenses/dompurify.LICENSE)) | `purify.es.js` | `dist/purify.es.mjs` | `f4c617ee8b63c5e161968756c6d9b29fc894ad588f824047f3332492f50c88ee` | `385981ebd0366fcce5313c1801019af737260ca29fe60d38a97f956d5ff1013a` |

Packages: <https://registry.npmjs.org/socket.io-client/-/socket.io-client-4.7.5.tgz>, <https://registry.npmjs.org/marked/-/marked-12.0.2.tgz>, <https://registry.npmjs.org/dompurify/-/dompurify-3.1.6.tgz>

socket.io 4.7.5 is the same version the old page loaded from a CDN; its UMD build `dist/socket.io.min.js` has the integrity hash
`sha384-2huaZvOR9iDzHqslqwpR87isEmrfxqyWOF7hr7BY6KG0+hVKLoEXMPUJw3ynWuhO`, identical to the hash the old page pinned.

## Updating

1. In an empty folder: `npm pack <name>@<version>` (npm verifies the registry checksum), unpack the tarball into its own folder.
2. Copy the file named in the table, apply the two changes above, update this table (`sha256sum`), check the licenses.
3. Run `node --test tests/js/` and `python tests/test_chat_page.py`, and look at the page in a browser.
