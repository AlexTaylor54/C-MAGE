# C-MAGE

C-MAGE extracts chemical structures from the figures in a paper and turns them
into machine-readable CXSMILES.

![C-MAGE](details/pipeline.png)

| Stage | Component | Input → Output |
|---|---|---|
| 1 | VisualHeist | PDF pages → figure images |
| 2 | DECIMER Image Segmentation | figures → individual structure images |
| 3 | CXMolScribe | structures → CXSMILES |

## Install

Needs ~7 GB of disk and Linux, Windows, or macOS 12+ on Apple Silicon. Intel
Macs cannot run it — PyTorch has published no macOS x86_64 wheels since 2.2.2.
A GPU is optional.

You also need conda. If you don't have it, install
[Miniforge](https://conda-forge.org/download/) — pick the file matching your
system and run it.

```bash
git clone https://github.com/AlexTaylor54/C-MAGE.git
cd C-MAGE
./install.sh
```

That builds all three environments and installs everything. Nothing else to
configure.

## Run

Put your PDFs in `MERMaid/pdfdir/`, then:

```bash
./run_pipeline.sh
```

The first run downloads ~2.4 GB of models. `./run_pipeline.sh --help` lists the
options — a different input folder, running only some stages, forcing CPU. On
Windows use `run_pipeline.py`.

## Results

Each run gets its own timestamped folder:

```
results/run_20260814-134947/03_CXMS_Results/
├── Completed_HighConfidence_CMAGE.xlsx    structures worth keeping
├── Completed_LowConfidence_CMAGE.xlsx     structures to check by eye
├── highconfidence_images/
└── lowconfidence_images/
```

The split is on CXMolScribe's confidence at a threshold of 0.8431. Each
spreadsheet shows the cropped structure next to the predicted CXSMILES and a
rendering of what that CXSMILES means, so a bad prediction is visible at a
glance.

---

`MERMaid/` and `cxmolscribe-wd/DECIMER-Image-Segmentation/` are vendored copies
of [MERMaid](https://github.com/aspuru-guzik-group/MERMaid) and
[DECIMER](https://github.com/Kohulan/DECIMER-Image-Segmentation).
