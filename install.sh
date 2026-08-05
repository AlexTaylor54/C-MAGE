#!/usr/bin/env bash
#
# Create the C-MAGE conda environments and install the in-repo packages.
#
#   ./install.sh                    # all three stages
#   ./install.sh visualheist        # one stage only
#   ./install.sh decimer cxmolscribe
#   ./install.sh --force            # recreate environments that already exist
#
# Stage 3 installs MolScribe from upstream at a pinned commit. To install from
# a local checkout instead:
#
#   CXMOLSCRIBE_SRC=~/src/MolScribe ./install.sh cxmolscribe
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Stage 3 uses MolScribe pinned to the commit recorded in the reference
# environment (envs/legacy/vh_freeze.txt) and in this repository's own git
# history, where MolScribe was originally a submodule at this commit.
MOLSCRIBE_REF="7296a30413eb55436702011efdff78131f66d162"
MOLSCRIBE_URL="git+https://github.com/thomas0809/MolScribe.git@${MOLSCRIBE_REF}"

# Set CXMOLSCRIBE_SRC to install from a local checkout instead -- use this if
# you have local modifications to MolScribe that are not in upstream.
CXMOLSCRIBE_SRC="${CXMOLSCRIBE_SRC:-}"

# Stage 2 needs a different TensorFlow package on macOS. Stages 1 and 3 use the
# same spec everywhere.
case "$(uname -s)" in
    Darwin)
        DECIMER_SPEC="cmage-decimer-macos.yml"
        if [ "$(uname -m)" != "arm64" ]; then
            echo "install.sh: Intel Macs are not supported." >&2
            echo "PyTorch has shipped no macOS x86_64 wheels since 2.2.2, so stages 1 and 3" >&2
            echo "cannot be installed. Apple Silicon on macOS 12 or later is required." >&2
            exit 1
        fi
        ;;
    *)
        DECIMER_SPEC="cmage-decimer.yml"
        ;;
esac

usage() {
    cat <<'EOF'
Create the C-MAGE conda environments and install the in-repo packages.

Usage:
  ./install.sh                       create all three environments
  ./install.sh visualheist           create one stage only
  ./install.sh decimer cxmolscribe   create several
  ./install.sh --force               recreate environments that already exist

Stages: visualheist, decimer, cxmolscribe

Stage 3 installs MolScribe from upstream at a pinned commit. To install from a
local checkout instead (e.g. if you have local modifications):

  CXMOLSCRIBE_SRC=~/src/MolScribe ./install.sh cxmolscribe
EOF
}

FORCE=0
STAGES=()

for arg in "$@"; do
    case "$arg" in
        --force) FORCE=1 ;;
        -h|--help) usage; exit 0 ;;
        visualheist|decimer|cxmolscribe) STAGES+=("$arg") ;;
        *) echo "install.sh: unknown argument '$arg'" >&2; usage >&2; exit 2 ;;
    esac
done

if [ ${#STAGES[@]} -eq 0 ]; then
    STAGES=(visualheist decimer cxmolscribe)
fi

# `conda activate` is a shell function, so it is unavailable in a
# non-interactive script until conda.sh has been sourced.
if ! command -v conda >/dev/null 2>&1; then
    echo "install.sh: conda not found on PATH." >&2
    echo "Install Miniforge or Miniconda first: https://conda-forge.org/download/" >&2
    exit 1
fi
# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"

log() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

env_exists() {
    conda env list | awk '{print $1}' | grep -qx "$1"
}

create_env() {
    local name="$1" spec="$2"
    if env_exists "$name"; then
        if [ "$FORCE" -eq 1 ]; then
            log "Removing existing environment ${name}"
            conda env remove -n "$name" --yes
        else
            log "Environment ${name} already exists, reusing it (--force to recreate)"
            return
        fi
    fi
    log "Creating environment ${name}"
    conda env create -f "${REPO_ROOT}/envs/${spec}"
}

install_visualheist() {
    create_env cmage-visualheist cmage-visualheist.yml
    conda activate cmage-visualheist
    log "Installing MERMaid (VisualHeist) in editable mode"
    # --no-deps: every dependency is pinned in the environment file, and
    # MERMaid's own extras would pull conflicting versions of torch.
    pip install -e "${REPO_ROOT}/MERMaid" --no-deps
    python -c "import visualheist, torch; print('visualheist OK, torch', torch.__version__)"
    conda deactivate
}

install_decimer() {
    create_env cmage-decimer "$DECIMER_SPEC"
    conda activate cmage-decimer
    log "Installing decimer_segmentation in editable mode"
    pip install -e "${REPO_ROOT}/cxmolscribe-wd/DECIMER-Image-Segmentation" --no-deps
    python -c "import decimer_segmentation, tensorflow as tf; print('decimer OK, tf', tf.__version__)"
    conda deactivate
}

install_cxmolscribe() {
    create_env cmage-cxmolscribe cmage-cxmolscribe.yml
    conda activate cmage-cxmolscribe

    if [ -n "$CXMOLSCRIBE_SRC" ]; then
        if [ ! -d "$CXMOLSCRIBE_SRC" ]; then
            echo "install.sh: CXMOLSCRIBE_SRC is set but '${CXMOLSCRIBE_SRC}' is not a directory" >&2
            exit 1
        fi
        log "Installing MolScribe from local checkout ${CXMOLSCRIBE_SRC}"
        pip install -e "$CXMOLSCRIBE_SRC" --no-deps
    else
        log "Installing MolScribe from upstream @ ${MOLSCRIBE_REF:0:8}"
        pip install "molscribe @ ${MOLSCRIBE_URL}" --no-deps
    fi
    python -c "import molscribe, torch; print('molscribe OK, torch', torch.__version__)"
    conda deactivate
}

for stage in "${STAGES[@]}"; do
    "install_${stage}"
done

log "Done. Environments installed: ${STAGES[*]}"
echo "Activate a stage with, e.g.:  conda activate cmage-visualheist"
