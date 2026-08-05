# MERMaid (vendored)

This directory is a vendored copy of
[MERMaid](https://github.com/aspuru-guzik-group/MERMaid), forked at commit
`6bfb46f096a3874e2d3501bd3b696018434c2512`, with local modifications for
C-MAGE.

MERMaid is a multimodal pipeline for mining chemical reactions from PDFs,
consisting of three components:

- **VisualHeist** — segments figures and tables out of PDF pages
- **DataRaider** — extracts reaction data from those images with a VLM
- **KGWizard** — builds a knowledge graph from the extracted data

**C-MAGE uses VisualHeist only.** It is stage 1 of the C-MAGE pipeline, feeding
its extracted figure images to DECIMER Image Segmentation. DataRaider and
KGWizard are retained from upstream but are not part of the C-MAGE pipeline and
are not covered by the C-MAGE environment specs.

## Installation

Do not install this directory on its own. It is installed into the
`cmage-visualheist` environment by the C-MAGE installer:

```bash
./install.sh visualheist
```

See [`envs/README.md`](../envs/README.md) for details.

## Layout

| Path | Contents |
|---|---|
| `src/visualheist/` | VisualHeist — stage 1 of C-MAGE |
| `src/dataraider/` | DataRaider (upstream MERMaid, unused by C-MAGE) |
| `src/kgwizard/` | KGWizard (upstream MERMaid, unused by C-MAGE) |
| `scripts/` | Entry points, and `startup.json` config |
| `Prompts/` | VLM prompt templates used by DataRaider |
| `webapp/` | Streamlit/FastAPI front end (upstream MERMaid, unused by C-MAGE) |

## License

MERMaid is distributed under the license in [`LICENSE`](LICENSE). See
`VisualHeist_README.md` for upstream's own setup notes, which describe the full
MERMaid pipeline rather than C-MAGE's use of it.
