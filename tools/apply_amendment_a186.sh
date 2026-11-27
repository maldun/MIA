#!/usr/bin/env bash
# Amendment A-186 (G-V4.GRAPHSTORE.TRANSFER, 2026-11-22, D-464): IF-102 v8 -> v9, text only. The table list names the record tables of IF-301
# (graphs, graph_nodes, graph_edges, context_nodes, context_edges, skills), which the storage layer has served since IF-301 v2/v3. No new operation,
# no behaviour change, the contract suite is unchanged. IF-102 is frozen at G-V4 (joint amendment): the owner's yes covers GRAPHSTORE and GRAPHAPI.
# Draft in specs/mia/amendments/A-186/. INSTALL IT ON THE LINE OF WORK goal/v4.graphstore.transfer.
#   bash tools/apply_amendment_a186.sh           show the diff (changes nothing)
#   bash tools/apply_amendment_a186.sh --do      install; commit afterwards as "plan: A-186 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
copy specs/mia/amendments/A-186/IF-102-storage-interface.md contracts/IF-102-storage-interface.md
finish
