#!/usr/bin/env bash
# Run Audock's test suites against tools/audock.
#   tests/run.sh            regression (102 cases) + synthetic (≈1,600 cases, seed 1234)
#   SEED=7 tests/run.sh     synthetic suite with another seed
#   PYTHON=/path/to/python  use a python that has PyYAML (adds the YAML-validity group)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d -t audock-tests-XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

echo "== regression suite"
cp -r "$ROOT" "$WORK/vault"
( cd "$WORK/vault" && rm -rf .git journal bases && git init -q && git add -A \
    && git -c user.name=t -c user.email=t@t commit -qm init >/dev/null )
bash "$ROOT/tests/regression.sh" "$WORK/vault" | sed 's/\x1b\[[0-9;]*m//g' | grep -E 'FAIL|RESULT' -A1

echo "== synthetic suite (seed ${SEED:-1234})"
SB="$WORK" "${PYTHON:-python3}" "$ROOT/tests/synth_tests.py" "$ROOT/tools/audock"
