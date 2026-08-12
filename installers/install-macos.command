#!/bin/bash
#
# C-MAGE installer for macOS (Apple Silicon).
#
# A chemist downloads this one file and double-clicks it. It fetches C-MAGE,
# builds the three Python environments it needs, and puts a "C-MAGE" launcher
# on the Desktop. No terminal commands, no conda, no git required.
#
# Everything lands in ~/C-MAGE and can be removed by deleting that folder and
# the Desktop launcher.
#
set -uo pipefail

REPO_OWNER="AlexTaylor54"
REPO_NAME="C-MAGE"
BRANCH="main"

APP_DIR="${HOME}/C-MAGE"
MAMBA_ROOT="${APP_DIR}/.micromamba"
MAMBA_BIN="${MAMBA_ROOT}/bin/micromamba"
LAUNCHER="${HOME}/Desktop/C-MAGE.app"

MOLSCRIBE_REF="7296a30413eb55436702011efdff78131f66d162"

# --------------------------------------------------------------------------
# Presentation. This window is the entire user interface, so it should read
# like a progress report rather than a build log.
# --------------------------------------------------------------------------
bold=$(printf '\033[1m'); dim=$(printf '\033[2m'); red=$(printf '\033[31m')
green=$(printf '\033[32m'); reset=$(printf '\033[0m')

step()  { printf '\n%s==> %s%s\n' "$bold" "$*" "$reset"; }
note()  { printf '    %s%s%s\n' "$dim" "$*" "$reset"; }
ok()    { printf '    %s%s%s\n' "$green" "$*" "$reset"; }

die() {
    printf '\n%s%s%s\n\n' "$red" "$*" "$reset"
    printf 'Installation stopped. Nothing was changed.\n'
    printf '\nPress Return to close this window.'
    read -r _
    exit 1
}

finish() {
    printf '\nPress Return to close this window.'
    read -r _
}

clear
cat <<'BANNER'
  ┌─────────────────────────────────────────────┐
  │                                             │
  │   C-MAGE                                    │
  │   Chemical structure extraction from PDFs   │
  │                                             │
  └─────────────────────────────────────────────┘
BANNER
printf '\nThis will install C-MAGE on your Mac. It takes about 15 minutes\n'
printf 'and downloads roughly 7 GB. You can keep using your Mac meanwhile.\n'

# --------------------------------------------------------------------------
# 1. Check the machine can run it at all, before downloading anything.
# --------------------------------------------------------------------------
step "Checking your Mac"

[ "$(uname -s)" = "Darwin" ] || die "This installer is for macOS."

if [ "$(uname -m)" != "arm64" ]; then
    die "C-MAGE needs an Apple Silicon Mac (M1, M2, M3 or M4).

This Mac has an Intel processor. PyTorch, which C-MAGE depends on, has not
released Intel Mac versions since 2024, so it cannot be installed here."
fi

macos_major=$(sw_vers -productVersion | cut -d. -f1)
if [ "$macos_major" -lt 12 ]; then
    die "C-MAGE needs macOS 12 (Monterey) or later.
This Mac is running macOS $(sw_vers -productVersion)."
fi

free_gb=$(df -g "${HOME}" | awk 'NR==2 {print $4}')
if [ "${free_gb:-0}" -lt 12 ]; then
    die "Not enough free disk space.

C-MAGE needs about 12 GB. This Mac has ${free_gb} GB available."
fi

ok "Apple Silicon, macOS $(sw_vers -productVersion), ${free_gb} GB free"

# --------------------------------------------------------------------------
# 2. Make room, preserving anything the user put here previously.
# --------------------------------------------------------------------------
if [ -d "$APP_DIR" ]; then
    step "An existing C-MAGE installation was found"
    printf '    %s\n\n' "$APP_DIR"
    printf '    Reinstall? Your previous results will be kept in a folder\n'
    printf '    named C-MAGE.previous. [y/N] '
    read -r answer
    case "$answer" in
        [yY]*) ;;
        *) printf '\nNothing was changed.\n'; finish; exit 0 ;;
    esac
    backup="${HOME}/C-MAGE.previous"
    rm -rf "$backup"
    mv "$APP_DIR" "$backup" || die "Could not move the existing installation."
    ok "Moved to ${backup}"
fi

# --------------------------------------------------------------------------
# 3. Download C-MAGE itself. curl and tar ship with macOS, so this avoids
#    requiring git or the Xcode command line tools.
# --------------------------------------------------------------------------
step "Downloading C-MAGE"
mkdir -p "$APP_DIR" || die "Could not create ${APP_DIR}."
tarball="${TMPDIR:-/tmp}/cmage-src.tar.gz"
curl -fL --progress-bar \
    "https://codeload.github.com/${REPO_OWNER}/${REPO_NAME}/tar.gz/refs/heads/${BRANCH}" \
    -o "$tarball" || die "Could not download C-MAGE. Check your internet connection."
tar -xzf "$tarball" -C "$APP_DIR" --strip-components=1 || die "The download was damaged. Please try again."
rm -f "$tarball"
ok "Installed to ${APP_DIR}"

# --------------------------------------------------------------------------
# 4. micromamba is a single binary and needs no installer of its own, so the
#    user never has to install conda.
# --------------------------------------------------------------------------
step "Setting up the package manager"
mkdir -p "$MAMBA_ROOT"
curl -fL https://micro.mamba.pm/api/micromamba/osx-arm64/latest \
    | tar -xj -C "$MAMBA_ROOT" bin/micromamba 2>/dev/null
[ -x "$MAMBA_BIN" ] || die "Could not set up the package manager."
export MAMBA_ROOT_PREFIX="$MAMBA_ROOT"
ok "Ready"

mm() { "$MAMBA_BIN" -r "$MAMBA_ROOT" "$@"; }
env_python() { echo "${MAMBA_ROOT}/envs/$1/bin/python"; }

build_env() {
    local name="$1" spec="$2" label="$3"
    step "Building environment ${label}"
    note "This is the slow part -- several minutes per environment."
    mm create -y -q -f "${APP_DIR}/envs/${spec}" >/dev/null \
        || die "Could not build the ${label} environment.

Try running this installer again. If it keeps failing, send the
text in this window to whoever gave you C-MAGE."
    ok "Done"
}

build_env cmage-visualheist cmage-visualheist.yml     "1 of 3  (reading pages)"
build_env cmage-decimer     cmage-decimer-macos.yml   "2 of 3  (finding structures)"
build_env cmage-cxmolscribe cmage-cxmolscribe.yml     "3 of 3  (reading structures)"

# --------------------------------------------------------------------------
# 5. The three in-repo packages. --no-deps because every dependency is
#    already pinned in the environment files; letting pip resolve these
#    packages' own metadata pulls a conflicting PyTorch.
# --------------------------------------------------------------------------
step "Installing C-MAGE components"

"$(env_python cmage-visualheist)" -m pip install -q -e "${APP_DIR}/MERMaid" --no-deps \
    || die "Could not install the page-reading component."
"$(env_python cmage-decimer)" -m pip install -q -e "${APP_DIR}/cxmolscribe-wd/DECIMER-Image-Segmentation" --no-deps \
    || die "Could not install the structure-finding component."
"$(env_python cmage-cxmolscribe)" -m pip install -q \
    "molscribe @ git+https://github.com/thomas0809/MolScribe.git@${MOLSCRIBE_REF}" --no-deps \
    || die "Could not install the structure-reading component."
ok "Done"

# --------------------------------------------------------------------------
# 6. Fetch the models now rather than on first use. Together they are about
#    2.4 GB, and none of the three stages reports download progress -- a first
#    run would sit silent for minutes and look like a hang.
# --------------------------------------------------------------------------
step "Downloading the chemistry models"
note "About 2.4 GB. This only happens once."
"$(env_python cmage-visualheist)" -c "from huggingface_hub import snapshot_download; snapshot_download('shixuanleong/visualheist-base', revision='e36203e67a05b9dd66d1310fd3a217e8b334ab30', ignore_patterns=['*.bin'])" >/dev/null 2>&1 \
    || die "Could not download the page-reading model."
"$(env_python cmage-decimer)" -c "from decimer_segmentation import load_model; load_model()" >/dev/null 2>&1 \
    || die "Could not download the structure-finding model."
"$(env_python cmage-cxmolscribe)" -c "from huggingface_hub import hf_hub_download; hf_hub_download('yujieq/MolScribe', 'swin_base_char_aux_1m.pth')" >/dev/null 2>&1 \
    || die "Could not download the structure-reading model."
ok "Done"

# --------------------------------------------------------------------------
# 7. Desktop launcher.
# --------------------------------------------------------------------------
step "Creating the Desktop app"
bash "${APP_DIR}/installers/make-app.sh" "${HOME}/Desktop" >/dev/null \
    || die "Could not create the Desktop app."
ok "C-MAGE is now on your Desktop"

# --------------------------------------------------------------------------
cat <<EOF

${green}${bold}Installation complete.${reset}

  Drag one or more PDFs onto the ${bold}C-MAGE${reset} icon on your Desktop,
  or double-click it to pick them. Results open by themselves when done.

  ${dim}To remove C-MAGE: delete ${APP_DIR} and the Desktop icon.${reset}

EOF
finish
