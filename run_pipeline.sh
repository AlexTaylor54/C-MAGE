#!/usr/bin/env bash
#
# Run C-MAGE end to end on a local machine (macOS or Linux, no scheduler).
#
#   ./run_pipeline.sh                          PDFs from MERMaid/pdfdir/
#   ./run_pipeline.sh --pdfs ~/papers          any directory of PDFs
#   ./run_pipeline.sh --stages 2,3 \
#       --figures examples/stage2_input        skip stage 1, use existing figures
#   ./run_pipeline.sh --device cpu             force CPU everywhere
#
# Each stage runs in its own conda environment, because the three cannot
# coexist -- see envs/README.md. Results land in one directory per run so
# repeated runs never overwrite each other.
#
# MERMaid/pipeline_sub.sh is the cluster equivalent and submits to SGE; use
# this script anywhere else.
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PDF_DIR="${REPO_ROOT}/MERMaid/pdfdir"
FIGURES_DIR=""
OUT_ROOT="${REPO_ROOT}/results"
STAGES="1,2,3"
MODEL_SIZE="base"
DEVICE="${CMAGE_DEVICE:-}"

usage() {
    cat <<'EOF'
Run the C-MAGE pipeline locally.

Options:
  --pdfs DIR        Directory of input PDFs        (default: MERMaid/pdfdir)
  --figures DIR     Feed stage 2 from existing figure images instead of
                    stage 1 output. Use with --stages 2,3
  --out DIR         Root for run directories       (default: results)
  --stages LIST     Comma-separated stages to run  (default: 1,2,3)
  --model-size S    VisualHeist model, base|large  (default: base)
  --device DEV      torch device: cpu, mps, cuda   (default: auto-detect)
  -h, --help        Show this message

Stages:
  1  VisualHeist   PDFs           -> figure images
  2  DECIMER       figure images  -> segmented structure images
  3  CXMolScribe   structures     -> SMILES spreadsheets
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --pdfs)       PDF_DIR="$2"; shift 2 ;;
        --figures)    FIGURES_DIR="$2"; shift 2 ;;
        --out)        OUT_ROOT="$2"; shift 2 ;;
        --stages)     STAGES="$2"; shift 2 ;;
        --model-size) MODEL_SIZE="$2"; shift 2 ;;
        --device)     DEVICE="$2"; shift 2 ;;
        -h|--help)    usage; exit 0 ;;
        *) echo "run_pipeline.sh: unknown argument '$1'" >&2; usage >&2; exit 2 ;;
    esac
done

wants() { case ",${STAGES}," in *",$1,"*) return 0 ;; *) return 1 ;; esac; }

if ! command -v conda >/dev/null 2>&1; then
    echo "run_pipeline.sh: conda not found. Run ./install.sh first." >&2
    exit 1
fi
# conda activate is a shell function and is unavailable until this is sourced.
# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"

[ -n "$DEVICE" ] && export CMAGE_DEVICE="$DEVICE"

RUN_DIR="${OUT_ROOT}/run_$(date +%Y%m%d-%H%M%S)"
mkdir -p "${RUN_DIR}"/{01_figures,02_segments,03_results,logs}

RESULTS_XLSX="${RUN_DIR}/02_segments/DIS_CMAGE_results.xlsx"

log() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

log "Run directory: ${RUN_DIR}"

if wants 1; then
    if [ ! -d "$PDF_DIR" ] || [ -z "$(find "$PDF_DIR" -maxdepth 1 -name '*.pdf' -print -quit)" ]; then
        echo "run_pipeline.sh: no PDFs found in ${PDF_DIR}" >&2
        echo "Put PDFs there, or pass --pdfs DIR." >&2
        exit 1
    fi
    log "Stage 1/3  VisualHeist -- extracting figures"
    conda activate cmage-visualheist
    python "${REPO_ROOT}/MERMaid/scripts/run_visualheist.py" \
        --pdf_dir "$PDF_DIR" \
        --image_dir "${RUN_DIR}/01_figures" \
        --model_size "$MODEL_SIZE" 2>&1 | tee "${RUN_DIR}/logs/stage1.log"
    conda deactivate
else
    log "Stage 1/3  skipped"
fi

# Stage 2 reads stage 1's output unless --figures points somewhere else.
STAGE2_INPUT="${FIGURES_DIR:-${RUN_DIR}/01_figures}"

if wants 2; then
    if [ ! -d "$STAGE2_INPUT" ]; then
        echo "run_pipeline.sh: figure directory does not exist: ${STAGE2_INPUT}" >&2
        exit 1
    fi
    log "Stage 2/3  DECIMER -- segmenting structures from ${STAGE2_INPUT}"
    conda activate cmage-decimer
    python "${REPO_ROOT}/cxmolscribe-wd/DECIMER-Image-Segmentation/pipeline_dis.py" \
        --input-dir "$STAGE2_INPUT" \
        --output-dir "${RUN_DIR}/02_segments" \
        --results-excel "$RESULTS_XLSX" 2>&1 | tee "${RUN_DIR}/logs/stage2.log"
    conda deactivate
fi

if wants 3; then
    log "Stage 3/3  CXMolScribe -- reading structures"
    conda activate cmage-cxmolscribe
    python "${REPO_ROOT}/cxmolscribe-wd/folder_ms.py" \
        --results-excel "$RESULTS_XLSX" \
        --output-dir "${RUN_DIR}/03_results" \
        --canvas "${REPO_ROOT}/cxmolscribe-wd/DECIMER-Image-Segmentation/canvas.xlsx" \
        2>&1 | tee "${RUN_DIR}/logs/stage3.log"
    conda deactivate
fi

log "Done"
echo "Results:  ${RUN_DIR}/03_results"
echo "  Completed_HighConfidence_CMAGE.xlsx   structures worth keeping"
echo "  Completed_LowConfidence_CMAGE.xlsx    structures to review or discard"
echo "Logs:     ${RUN_DIR}/logs"
