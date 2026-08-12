#!/usr/bin/env bash
#
# Build C-MAGE.app from installers/droplet.applescript.
#
#   ./installers/make-app.sh              put it on the Desktop
#   ./installers/make-app.sh ~/Applications
#
# Called by install-macos.command, and usable on its own by anyone who already
# has the environments built (for example via ./install.sh).
#
# osacompile ships with macOS, so this needs nothing installed. Because the app
# is compiled locally rather than downloaded, macOS does not quarantine it and
# it opens without a Gatekeeper warning.
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="${1:-${HOME}/Desktop}"
APP_PATH="${DEST_DIR}/C-MAGE.app"

[ "$(uname -s)" = "Darwin" ] || { echo "make-app.sh: macOS only." >&2; exit 1; }
command -v osacompile >/dev/null 2>&1 || { echo "make-app.sh: osacompile not found." >&2; exit 1; }

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Bake the repository location and preferences path into the compiled app, so
# the droplet works no matter where it is dragged to.
# The web UI only needs the standard library, but it must be a Python that
# exists on this machine -- prefer one of the C-MAGE environments so the app
# keeps working even where no system python3 is installed.
PYTHON_BIN=""
for candidate in \
    "${REPO_ROOT}/.micromamba/envs/cmage-visualheist/bin/python" \
    "${CONDA_EXE:+$(dirname "$(dirname "${CONDA_EXE}")")/envs/cmage-visualheist/bin/python}" \
    "${HOME}/miniconda3/envs/cmage-visualheist/bin/python" \
    "${HOME}/miniforge3/envs/cmage-visualheist/bin/python" \
    "/opt/miniconda3/envs/cmage-visualheist/bin/python" \
    "$(command -v python3 || true)"; do
    [ -n "$candidate" ] && [ -x "$candidate" ] && { PYTHON_BIN="$candidate"; break; }
done
[ -n "$PYTHON_BIN" ] || { echo "make-app.sh: no usable Python found." >&2; exit 1; }

sed -e "s|__REPO_DIR__|${REPO_ROOT}|" \
    -e "s|__PYTHON_BIN__|${PYTHON_BIN}|" \
    "${REPO_ROOT}/installers/launcher.applescript" > "${tmp}/launcher.applescript"

rm -rf "$APP_PATH"
mkdir -p "$DEST_DIR"
osacompile -o "$APP_PATH" "${tmp}/launcher.applescript"

echo "Created ${APP_PATH}"
echo "  repository : ${REPO_ROOT}"
echo "  python     : ${PYTHON_BIN}"
