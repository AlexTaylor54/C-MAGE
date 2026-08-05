# C-MAGE environments

C-MAGE runs as three sequential stages, each in its own conda environment.

| Stage | Environment | Spec | What it does |
|---|---|---|---|
| 1 | `cmage-visualheist` | [`cmage-visualheist.yml`](cmage-visualheist.yml) | Extracts figures/tables from PDFs (Florence-2) |
| 2 | `cmage-decimer` | [`cmage-decimer.yml`](cmage-decimer.yml) | Segments chemical structures out of those figures (Mask R-CNN) |
| 3 | `cmage-cxmolscribe` | [`cmage-cxmolscribe.yml`](cmage-cxmolscribe.yml) | Translates each structure image to CXSMILES |

## Quick install

From the repository root:

```bash
./install.sh
```

That creates all three environments and installs the in-repo packages. To do
one stage at a time:

```bash
./install.sh visualheist
```

Options: `--force` recreates environments that already exist; `CXMOLSCRIBE_SRC=<path>`
points the installer at your CXMolScribe checkout (see below).

## Platform support

| Platform | Supported | Notes |
|---|---|---|
| Linux x86_64 | yes | the reference platform; CUDA via the module system |
| Windows | yes | needs poppler on PATH, or `POPPLER_PATH` set |
| macOS, Apple Silicon, 12+ | yes | uses `cmage-decimer-macos.yml`; CPU or MPS |
| macOS, Apple Silicon, 11 | no | `tensorflow-macos` requires macOS 12.0 |
| macOS, Intel | no | PyTorch has shipped no macOS x86_64 wheels since 2.2.2 |

`install.sh` picks the stage 2 spec from `uname` and refuses to run on Intel Macs
rather than failing halfway through.

Stage 2 is the only stage that differs by platform. Plain `tensorflow` has no
arm64 wheel at 2.12, and the releases that do (2.13+) ship a Keras API the
vendored Mask R-CNN code does not run on. `tensorflow-macos==2.12.0` provides
arm64 wheels against the same Keras 2.12, so nothing has to be downgraded.

`tensorflow-metal` is deliberately not included. It can offload to the Apple
GPU but is version-sensitive and has a history of numerical differences — add it
only once the CPU path is known to give correct segmentations.

### Choosing a device

Stages 1 and 3 pick CUDA, then MPS, then CPU. Override with `CMAGE_DEVICE`, or
`--device` on stage 3 and `run_pipeline.sh`:

```bash
CMAGE_DEVICE=cpu ./run_pipeline.sh
```

Florence-2 (stage 1) uses a few operations MPS does not implement. Export
`PYTORCH_ENABLE_MPS_FALLBACK=1` to let those fall back to CPU, or drop to
`CMAGE_DEVICE=cpu` outright.

## Why three environments

There is one hard, irreducible conflict. Stage 2 is built on TensorFlow 2.12,
which requires `numpy < 1.24`. Stages 1 and 3 are built on PyTorch 2.7/2.8,
whose wheels require `numpy >= 1.24`. No single environment satisfies both, so
stage 2 has to stay separate.

Stages 1 and 3 are *not* mutually incompatible in principle — the conflict
there is only in pinned versions, not in requirements. They are kept apart
anyway because stage 3's `OpenNMT-py==2.2.0` / `torchtext==0.5.0` pins are
fragile, and merging them would put those constraints on the Florence-2
install too. Merging stages 1 and 3 is a reasonable future cleanup; merging
stage 2 into either is not.

## MolScribe / CXMolScribe

Stage 3 is referred to as "CXMolScribe" throughout this repository because it
produces CXSMILES-labelled output. The code itself calls upstream
[MolScribe](https://github.com/thomas0809/MolScribe) unmodified, so
`install.sh` installs it from upstream at a pinned commit:

```
7296a30413eb55436702011efdff78131f66d162
```

That commit is not arbitrary — it is the one recorded in
`envs/legacy/vh_freeze.txt`, and the one this repository's own git history
pointed at back when MolScribe was a submodule here.

Two things support treating upstream as correct:

- `folder_ms.py` and `pipeline_ms.py` call
  `model.predict_image_file(..., return_atoms_bonds=True, return_confidence=True)`
  and read `prediction["smiles"]` / `prediction["confidence"]` — all upstream
  API surface. Nothing CXSMILES-specific is imported or called; "CXSMILES"
  appears only in comments and spreadsheet column headers.
- The checkpoint is `yujieq/MolScribe` (`swin_base_char_aux_1m.pth`), the
  upstream author's own weights, not a retrained model.

If you do have local MolScribe modifications that never made it upstream,
install from your checkout instead:

```bash
CXMOLSCRIBE_SRC=~/src/MolScribe ./install.sh cxmolscribe
```

Either way the install uses `--no-deps`: every dependency MolScribe needs is
already pinned in `cmage-cxmolscribe.yml`, and letting pip resolve MolScribe's
own `install_requires` pulls an incompatible torch.

The checkpoint is downloaded at runtime via `huggingface_hub`, so the first run
of stage 3 needs network access.

## Running on the CRC cluster

The GPU builds expect CUDA from the module system, not from conda:

```bash
module load cuda/11.8
module load cudnn/8.9.3
```

CUDA 11.8 / cuDNN 8.9 is what TensorFlow 2.12 (stage 2) needs. The PyTorch
stages ship their own CUDA runtime in the wheels and ignore the loaded module.

In a batch script, `conda activate` is unavailable until you source conda's
shell hook:

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate cmage-visualheist
```

## What is installed where

`install.sh` creates each environment from its spec, then installs the
in-repo packages in editable mode:

| Environment | Editable install | Provides |
|---|---|---|
| `cmage-visualheist` | `./MERMaid` | `import visualheist` |
| `cmage-decimer` | `./cxmolscribe-wd/DECIMER-Image-Segmentation` | `import decimer_segmentation` |
| `cmage-cxmolscribe` | *external* CXMolScribe checkout | `import molscribe` |

The editable installs matter: `scripts/run_visualheist.py` imports
`visualheist` as a top-level package, which only resolves once MERMaid is
installed. Running the scripts from a plain checkout without installing will
fail with `ModuleNotFoundError`.

## System dependencies

`poppler` is included in the stage 1 and stage 2 specs. `pdf2image` shells out
to poppler's `pdftoppm`/`pdftocairo` binaries; without them, PDF loading fails
with `PDFInfoNotInstalledError`. If you build these environments with something
other than conda, install poppler through your system package manager
(`apt install poppler-utils`, `brew install poppler`).

## Regenerating a spec

These files are hand-curated, not `pip freeze` output. When you add a
dependency, add it to the relevant `.yml` with a pin and a comment saying what
needs it. Do not replace them with a freeze — a freeze captures the whole
transitive closure plus whatever else happens to be in the environment, which
is exactly what made the original captures unusable (see below).

To check that a spec still describes a working environment:

```bash
./install.sh --force <stage>
```

To check only that the pins are still mutually satisfiable, without building
anything (fast, and works from any machine):

```bash
uv pip compile --python-version 3.10 \
    --python-platform x86_64-unknown-linux-gnu <(python -c "
import yaml,sys
d=yaml.safe_load(open('envs/cmage-decimer.yml'))
print('\n'.join(x for e in d['dependencies'] if isinstance(e,dict) for x in e['pip']))")
```

Note that `pip install --dry-run --platform ...` is **not** a reliable
substitute: in cross-platform mode pip stops evaluating environment markers
and reports spurious conflicts on `python_version`-gated requirements.

Be careful with stage 2's numpy pin in particular. TensorFlow 2.12 requires
`numpy < 1.24` and scipy 1.15.2 requires `numpy >= 1.23.5`, so `1.23.5` is the
only version satisfying both. There is no slack: bumping either package
breaks the environment.

## `legacy/` — the original captures

Kept for provenance only. **None of these are installable.**

| File | What it is |
|---|---|
| `vh_freeze.txt` | `pip freeze` of the `vh` env. Contains `-e /users/ataylo29/MERMaid` and `RanDepict`/`RxnScribe` from local paths. |
| `vh_freeze_earlier.txt` | Earlier capture, previously `MERMaid/vh_real_requirements.txt`. Records the MERMaid fork point: `aspuru-guzik-group/MERMaid@6bfb46f0`. |
| `decimer_freeze.txt` | `pip freeze` of the `ds` env. 94 of its 161 lines are `@ file:///croot/...` conda build paths. |
| `decimer_conda_export.yml` | `conda env export` of `ds`, previously `DECIMER-Image-Segmentation/ds.yml`. Linux-64 explicit build strings. |
| `cxmolscribe_conda_explicit.txt` | `conda list --explicit` of `2ms`, previously `cxmolscribe-wd/workingMS.txt`. This is the authoritative record of stage 3 and the basis for `cmage-cxmolscribe.yml`. |
| `cxmolscribe_freeze.txt` | **Not a record of the `2ms` env.** Captured from the system Python, so it lists RHEL packages (`rpm`, `selinux`, `subscription-manager`, `cockpit`) and system-Python pins. Ignore it. |

### Dropped from the reconstructed specs

- **RanDepict** — present in the `vh` and system-Python captures, imported
  nowhere in the repository.
- **RxnScribe** — imported only by `MERMaid/src/dataraider/processor_info.py`.
  DataRaider and KGWizard are part of upstream MERMaid but are not part of the
  C-MAGE pipeline, which runs only VisualHeist from MERMaid. If you want to run
  DataRaider, install `rxnscribe` into `cmage-visualheist` separately.
- **vLLM, streamlit, fastapi, uvicorn** — the MERMaid webapp, not used by C-MAGE.
- **TensorFlow 2.7 / Keras 2.7** — present in the `vh` env, but VisualHeist
  imports neither. Left over from an earlier setup.
- **Jupyter** — present throughout the `ds` env capture, not needed to run the
  pipeline.
