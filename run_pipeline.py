#!/usr/bin/env python3
"""Run C-MAGE end to end on a local machine.

The three stages live in three environments that cannot coexist, so this
launches each one under its own interpreter rather than importing anything.
It uses only the standard library, so it can be run by any of the three
environments' Pythons.

    python run_pipeline.py                              PDFs from MERMaid/pdfdir
    python run_pipeline.py --pdfs ~/papers
    python run_pipeline.py --stages 2,3 --figures examples/stage2_input
    python run_pipeline.py --device cpu

MERMaid/pipeline_sub.sh is the cluster equivalent and submits to SGE; use this
anywhere else. run_pipeline.sh is a thin wrapper around this file.
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
WINDOWS = os.name == "nt"

STAGES = {
    1: ("cmage-visualheist", "VisualHeist -- extracting figures"),
    2: ("cmage-decimer", "DECIMER -- segmenting structures"),
    3: ("cmage-cxmolscribe", "CXMolScribe -- reading structures"),
}


def bold(text):
    return text if WINDOWS else f"\033[1m{text}\033[0m"


def log(message):
    print(f"\n{bold('==> ' + message)}", flush=True)


def env_roots():
    """Places an environment might live.

    Probed as directories rather than by calling `conda info --base`, which
    needs conda to be executable in the current shell -- not true under
    restricted shells, cron, or the bundled micromamba install.
    """
    roots = [REPO_ROOT / ".micromamba" / "envs"]
    if os.environ.get("MAMBA_ROOT_PREFIX"):
        roots.append(Path(os.environ["MAMBA_ROOT_PREFIX"]) / "envs")
    if os.environ.get("CONDA_EXE"):
        roots.append(Path(os.environ["CONDA_EXE"]).parent.parent / "envs")
    home = Path.home()
    roots += [home / n / "envs" for n in
              ("micromamba", "miniforge3", "miniconda3", "anaconda3")]
    roots += [Path("/opt/miniconda3/envs"), Path("/opt/anaconda3/envs")]
    return roots


def find_env(name):
    """Return (python_executable, extra_PATH_entries) for an environment."""
    for root in env_roots():
        prefix = root / name
        python = prefix / ("python.exe" if WINDOWS else Path("bin") / "python")
        if python.exists():
            # poppler's binaries are not next to python on Windows, and on Unix
            # the environment's bin/ must be on PATH for pdf2image to find them.
            extra = ([prefix, prefix / "Library" / "bin", prefix / "Scripts"]
                     if WINDOWS else [prefix / "bin"])
            return python, [str(p) for p in extra]
    return None, None


def run_stage(number, script, args, run_dir):
    env_name, description = STAGES[number]
    python, path_entries = find_env(env_name)
    if python is None:
        sys.exit(
            f"Environment '{env_name}' not found.\n"
            "Run install.sh, or installers/install-macos.command on a Mac, or\n"
            "installers/install-windows.bat on Windows."
        )

    log(f"Stage {number}/3  {description}")
    child_env = dict(os.environ)
    child_env["PATH"] = os.pathsep.join(path_entries + [child_env.get("PATH", "")])

    log_path = run_dir / "logs" / f"stage{number}.log"
    started = time.time()
    with open(log_path, "w", encoding="utf-8", errors="replace") as log_file:
        process = subprocess.Popen(
            [str(python), str(script), *[str(a) for a in args]],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            env=child_env, cwd=str(REPO_ROOT), text=True,
            encoding="utf-8", errors="replace", bufsize=1,
        )
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            log_file.write(line)
        code = process.wait()

    if code != 0:
        sys.exit(f"\nStage {number} failed. Details above, and in {log_path}")
    print(f"    ({time.time() - started:.0f}s)", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="Run the C-MAGE pipeline locally.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Stages:\n"
               "  1  VisualHeist   PDFs          -> figure images\n"
               "  2  DECIMER       figures       -> structure images\n"
               "  3  CXMolScribe   structures    -> SMILES spreadsheets",
    )
    parser.add_argument("--pdfs", type=Path, default=REPO_ROOT / "MERMaid" / "pdfdir",
                        help="Directory of input PDFs.")
    parser.add_argument("--figures", type=Path, default=None,
                        help="Feed stage 2 from existing figure images instead of "
                             "stage 1 output. Use with --stages 2,3.")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "results",
                        help="Root directory for per-run output folders.")
    parser.add_argument("--stages", default="1,2,3", help="Comma-separated stages to run.")
    parser.add_argument("--model-size", default="base", choices=["base", "large"])
    parser.add_argument("--device", default=None, help="torch device: cpu, mps or cuda.")
    args = parser.parse_args()

    wanted = {int(s) for s in args.stages.split(",") if s.strip()}
    if args.device:
        os.environ["CMAGE_DEVICE"] = args.device

    run_dir = args.out / f"run_{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    for sub in ("01_VH_Figures", "02_DIS_Segments", "03_CXMS_Results", "logs"):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
    results_xlsx = run_dir / "02_DIS_Segments" / "DIS_CMAGE_results.xlsx"

    log(f"Run directory: {run_dir}")

    if 1 in wanted:
        if not args.pdfs.is_dir() or not any(args.pdfs.glob("*.pdf")):
            sys.exit(f"No PDFs found in {args.pdfs}\nPut PDFs there, or pass --pdfs.")
        run_stage(1, REPO_ROOT / "MERMaid" / "scripts" / "run_visualheist.py",
                  ["--pdf_dir", args.pdfs,
                   "--image_dir", run_dir / "01_VH_Figures",
                   "--model_size", args.model_size], run_dir)
    else:
        log("Stage 1/3  skipped")

    stage2_input = args.figures or (run_dir / "01_VH_Figures")

    if 2 in wanted:
        if not Path(stage2_input).is_dir():
            sys.exit(f"Figure directory does not exist: {stage2_input}")
        run_stage(2, REPO_ROOT / "cxmolscribe-wd" / "DECIMER-Image-Segmentation" / "pipeline_dis.py",
                  ["--input-dir", stage2_input,
                   "--output-dir", run_dir / "02_DIS_Segments",
                   "--results-excel", results_xlsx], run_dir)

    if 3 in wanted:
        run_stage(3, REPO_ROOT / "cxmolscribe-wd" / "folder_ms.py",
                  ["--results-excel", results_xlsx,
                   "--output-dir", run_dir / "03_CXMS_Results",
                   "--canvas", REPO_ROOT / "cxmolscribe-wd" / "DECIMER-Image-Segmentation" / "canvas.xlsx"],
                  run_dir)

    log("Done")
    print(f"Results:  {run_dir / '03_CXMS_Results'}")
    print("  Completed_HighConfidence_CMAGE.xlsx   structures worth keeping")
    print("  Completed_LowConfidence_CMAGE.xlsx    structures to review or discard")
    print(f"Logs:     {run_dir / 'logs'}")


if __name__ == "__main__":
    main()
