#!/usr/bin/env bash
# Parse and validate the SysML v2 models of the repository with the engine of the Jupyter kernel (OMG pilot implementation), before you load them in a notebook.
#   bash tools/check_sysml.sh                 all models: specs/mia (architecture.sysml, then model/*.sysml) and specs/number-gate
#   bash tools/check_sysml.sh FILE...         only these files, in this order, in one session
# Needs Java 17+ (the JRE with the compiler module is enough) and the installed kernel; override the place with SYSML_KERNEL_DIR.
# Exit code: 0 clean, 1 errors in a model, 2 the checker could not run. Takes about half a minute, most of it loading the SysML library.
set -euo pipefail
cd "$(dirname "$0")/.."

KERNEL=${SYSML_KERNEL_DIR:-$HOME/sysml-kernel/sysml}
JAR=$(ls "$KERNEL"/jupyter-sysml-kernel-*-all.jar 2>/dev/null | head -1 || true)
[ -n "$JAR" ] && [ -d "$KERNEL/sysml.library" ] || { echo "no kernel found in $KERNEL (set SYSML_KERNEL_DIR to the folder with the jar and sysml.library)"; exit 2; }
command -v java >/dev/null || { echo "java not found"; exit 2; }

if [ $# -gt 0 ]; then
  files=("$@")
else
  files=(specs/mia/architecture.sysml)
  for f in specs/mia/model/*.sysml; do [ -e "$f" ] && files+=("$f"); done
  for f in specs/*/architecture.sysml; do [ "$f" = specs/mia/architecture.sysml ] || { files+=(-- "$f"); }; done
fi

# the library loader prints a line per library file; they hide the result. pipefail keeps the exit code of java.
java -cp "$JAR" "$(dirname "$0")/sysml_check/SysmlCheck.java" "$KERNEL/sysml.library" "${files[@]}" 2> >(grep -v '^log4j' >&2) | grep -v '^Reading '
