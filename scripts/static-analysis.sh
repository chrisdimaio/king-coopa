#!/usr/bin/env bash
# Static analysis for this repo. Run by .githooks/pre-push; also safe to run by hand.
#
#   scripts/static-analysis.sh [DIR] [GIT_LOG_RANGE]
#
# DIR            tree to check (default: repo root). The hook passes an export of the commit being pushed.
# GIT_LOG_RANGE  commits to scan for secrets with gitleaks (default: whole history of HEAD).
#
# Blocking checks:
#   - dashboard Python: ruff (dashboard/ruff.toml) and bandit (medium+ severity)
#   - dashboard page:   eslint on the inline <script> blocks of dashboard/static/index.html
#   - secrets:          gitleaks on the commits being pushed and on the tree
#   - private data:     no RFC1918 IPs in tracked files, plus any patterns in .sensitive-patterns
#                       (gitignored; one extended regex per line, e.g. the real Pi IP or coordinates)
# The legacy controller code in king-coopa/ is reported but does not block.
set -uo pipefail

REPO=$(git rev-parse --show-toplevel)
DIR=${1:-$REPO}
RANGE=${2:-HEAD}
LINT_BIN=${KC_LINT_BIN:-$HOME/.local/share/kc-lint/bin}
fail=0
section() { printf '\n\033[1m== %s\033[0m\n' "$1"; }
bad() { printf '\033[31mFAIL\033[0m %s\n' "$1"; fail=1; }
ok() { printf '\033[32mok\033[0m   %s\n' "$1"; }

for tool in "$LINT_BIN/ruff" "$LINT_BIN/bandit"; do
  [ -x "$tool" ] || { echo "Missing $tool. Install with:"; echo "  python3 -m venv ~/.local/share/kc-lint && ~/.local/share/kc-lint/bin/pip install ruff bandit"; exit 2; }
done
command -v eslint >/dev/null || { echo "Missing eslint"; exit 2; }
command -v gitleaks >/dev/null || { echo "Missing gitleaks"; exit 2; }

cd "$DIR" || exit 2
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

section "ruff (dashboard)"
if "$LINT_BIN/ruff" check --no-cache --config dashboard/ruff.toml dashboard; then ok ruff; else bad ruff; fi

section "bandit (dashboard, medium+)"
if "$LINT_BIN/bandit" -q -r dashboard -ll 2>/dev/null; then ok bandit; else bad bandit; fi

section "eslint (dashboard/static/index.html inline scripts)"
# Lay the inline scripts out on their original line numbers so errors point at index.html.
python3 -I - dashboard/static/index.html "$TMP/index.lint.js" <<'PY'
import re, sys
src = open(sys.argv[1]).read()
lines = [""] * (src.count("\n") + 1)
for m in re.finditer(r"<script>(.*?)</script>", src, re.S):
    start = src[:m.start(1)].count("\n")
    for i, line in enumerate(m.group(1).split("\n")):
        lines[start + i] = line
open(sys.argv[2], "w").write("\n".join(lines))
PY
if eslint --no-eslintrc -c dashboard/.eslintrc.json --no-ignore "$TMP/index.lint.js" | sed "s#$TMP/index.lint.js#dashboard/static/index.html#"; [ "${PIPESTATUS[0]}" -eq 0 ]; then ok eslint; else bad eslint; fi

section "gitleaks (secrets)"
if gitleaks git "$REPO" --log-opts="$RANGE" --no-banner --redact --log-level error; then ok "gitleaks commits ($RANGE)"; else bad "gitleaks commits"; fi
if gitleaks dir . --no-banner --redact --log-level error; then ok "gitleaks tree"; else bad "gitleaks tree"; fi

section "private data (IPs / local patterns)"
# Tracked files: from the index for the working tree, or everything in an exported commit.
if [ "$(cd "$DIR" && pwd -P)" = "$(cd "$REPO" && pwd -P)" ]; then files=$(git -C "$REPO" ls-files)
else files=$(find . -type f | sed 's#^\./##'); fi
hits=$(cd "$DIR" && printf '%s\n' "$files" | grep -v '^LICENSE$' | xargs -d '\n' grep -nIoE '\b(10\.[0-9]{1,3}|192\.168|172\.(1[6-9]|2[0-9]|3[01]))\.[0-9]{1,3}\.[0-9]{1,3}\b' 2>/dev/null)
if [ -f "$REPO/.sensitive-patterns" ]; then
  more=$(cd "$DIR" && printf '%s\n' "$files" | xargs -d '\n' grep -nIoE -f <(grep -vE '^\s*(#|$)' "$REPO/.sensitive-patterns") 2>/dev/null)
  hits=$(printf '%s\n%s' "$hits" "$more" | sed '/^$/d')
fi
if [ -n "$hits" ]; then printf '%s\n' "$hits" | sed 's/:[^:]*$/: <redacted match>/' | sort -u; bad "private data in tracked files"; else ok "no private IPs or local patterns"; fi

section "legacy king-coopa/ (report only)"
legacy=$("$LINT_BIN/ruff" check --no-cache --config dashboard/ruff.toml --output-format concise king-coopa 2>/dev/null | grep -c ':[0-9]*:[0-9]*:')
sec=$("$LINT_BIN/bandit" -q -r king-coopa -ll -f csv 2>/dev/null | tail -n +2 | grep -c .)
echo "ruff: $legacy finding(s); bandit medium+: $sec finding(s) — not blocking"

echo
if [ "$fail" -ne 0 ]; then echo "Static analysis FAILED"; exit 1; fi
echo "Static analysis passed"
