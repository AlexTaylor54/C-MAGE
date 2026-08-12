#!/usr/bin/env python3
"""Local web interface for C-MAGE.

Serves a single page on localhost and opens it in the default browser. The
page is a drop target: PDFs dragged onto it are uploaded, the pipeline runs,
and the results folder opens when it finishes.

Standard library only, so any of the three environment Pythons can run it --
and so can a system Python 3.9+.

    python webui/server.py
    python webui/server.py --port 8765 --no-browser

Only ever bound to 127.0.0.1. This is a local tool, not a service: there is no
authentication and it should not be exposed to a network.
"""

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

REPO_ROOT = Path(__file__).resolve().parent.parent
PAGE = Path(__file__).resolve().parent / "index.html"
WINDOWS = os.name == "nt"
MAX_UPLOAD = 200 * 1024 * 1024  # per file; generous for a paper, bounded anyway

STAGE_NAMES = {
    1: "Finding figures in the pages",
    2: "Cutting out the structures",
    3: "Reading the structures",
}

# One job at a time -- this is a single-user desktop tool.
JOB = {
    "state": "idle",     # idle | running | done | error
    "stage": 0,          # 0-3
    "message": "",
    "lines": [],         # tail of pipeline output, for the details panel
    "results": None,     # path to 03_results
    "counts": None,      # {"high": n, "low": n}
    "failed": [],        # input files stage 1 could not read
    "started": None,
}
JOB_LOCK = threading.Lock()


# ---------------------------------------------------------------- settings

def settings_path():
    if WINDOWS:
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path.home() / "Library" / "Application Support"
    return base / "C-MAGE" / "output-folder.txt"


def default_output():
    return str(Path.home() / "Documents" / "C-MAGE Results")


def get_output_folder():
    try:
        value = settings_path().read_text(encoding="utf-8").strip()
        if value:
            return value
    except OSError:
        pass
    return default_output()


def set_output_folder(path):
    p = settings_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(str(path), encoding="utf-8")


def pick_folder_dialog(current):
    """Ask the OS for a folder. The browser cannot do this -- it has no access
    to arbitrary paths -- so the request is handed back to the desktop."""
    try:
        if platform.system() == "Darwin":
            script = (
                'set d to POSIX file "%s" as alias\n'
                'set f to choose folder with prompt "Choose where C-MAGE saves results:" '
                'default location d\n'
                'return POSIX path of f' % current.replace('"', '')
            )
            out = subprocess.run(["osascript", "-e", script],
                                 capture_output=True, text=True, timeout=300)
            if out.returncode != 0:
                return None  # cancelled
            return out.stdout.strip().rstrip("/") or None
        if WINDOWS:
            ps = (
                "Add-Type -AssemblyName System.Windows.Forms;"
                "$d = New-Object System.Windows.Forms.FolderBrowserDialog;"
                "$d.Description = 'Choose where C-MAGE saves results';"
                "$d.SelectedPath = '%s';"
                "if ($d.ShowDialog() -eq 'OK') { $d.SelectedPath }" % current.replace("'", "")
            )
            out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                                 capture_output=True, text=True, timeout=300)
            return out.stdout.strip() or None
    except Exception:
        return None
    return None


def reveal(path):
    try:
        if platform.system() == "Darwin":
            subprocess.Popen(["open", str(path)])
        elif WINDOWS:
            os.startfile(str(path))  # noqa: S606
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        pass


# ---------------------------------------------------------------- the job

def run_job(input_dir, output_root):
    stage_re = re.compile(r"Stage (\d)/3")
    high_re = re.compile(r"High Confidence of Correct Counter = (\d+)")
    low_re = re.compile(r"Discard Counter = (\d+)")
    fail_re = re.compile(r"ERROR: Failed to process ([^:]+):")
    counts = {}
    failed = []

    def update(**kw):
        with JOB_LOCK:
            JOB.update(kw)

    def add_line(text):
        with JOB_LOCK:
            JOB["lines"].append(text.rstrip())
            del JOB["lines"][:-400]

    update(state="running", stage=0, message="Starting up", lines=[],
           results=None, counts=None, failed=[], started=time.time())

    try:
        process = subprocess.Popen(
            [sys.executable, str(REPO_ROOT / "run_pipeline.py"),
             "--pdfs", str(input_dir), "--out", str(output_root)],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=str(REPO_ROOT), text=True, encoding="utf-8",
            errors="replace", bufsize=1,
        )
        for line in process.stdout:
            add_line(line)
            m = stage_re.search(line)
            if m:
                n = int(m.group(1))
                update(stage=n, message=STAGE_NAMES.get(n, ""))
            m = high_re.search(line)
            if m:
                counts["high"] = int(m.group(1))
            m = low_re.search(line)
            if m:
                counts["low"] = int(m.group(1))
            m = fail_re.search(line)
            if m:
                failed.append(m.group(1).strip())
        code = process.wait()
    except Exception as exc:                      # noqa: BLE001
        update(state="error", message=f"Could not start the pipeline: {exc}")
        return
    finally:
        shutil.rmtree(input_dir, ignore_errors=True)

    if code != 0:
        update(state="error", message="The pipeline stopped with an error.")
        return

    runs = sorted(Path(output_root).glob("run_*"), key=lambda p: p.name)
    results = str(runs[-1] / "03_results") if runs else None
    total = counts.get("high", 0) + counts.get("low", 0)

    # A run that read nothing still exits zero, so success is judged on output
    # rather than on the exit code. Reporting "finished" for an empty result is
    # worse than reporting a failure.
    if total == 0:
        update(state="empty", stage=3, results=results,
               counts={"high": 0, "low": 0}, failed=failed,
               message="No chemical structures were found.")
        return

    update(state="done", stage=3, message="Finished",
           results=results, counts=counts, failed=failed)
    if results:
        reveal(results)


# ---------------------------------------------------------------- handler

class Handler(BaseHTTPRequestHandler):
    server_version = "C-MAGE"

    def log_message(self, *args):
        pass  # the browser is the interface; the terminal stays quiet

    # -- helpers ----------------------------------------------------------
    def _send(self, code, body=b"", ctype="application/json"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def _json(self, payload, code=200):
        self._send(code, json.dumps(payload), "application/json")

    # -- routes -----------------------------------------------------------
    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/":
            try:
                self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            except OSError:
                self._send(500, b"index.html is missing", "text/plain")
        elif route == "/status":
            with JOB_LOCK:
                payload = dict(JOB)
            payload["lines"] = payload["lines"][-60:]
            payload["output_folder"] = get_output_folder()
            self._json(payload)
        elif route == "/reveal":
            with JOB_LOCK:
                results = JOB.get("results")
            if results:
                reveal(results)
            self._json({"ok": bool(results)})
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        route = urlparse(self.path).path
        if route == "/upload":
            self._upload()
        elif route == "/run":
            self._run()
        elif route == "/choose-folder":
            current = get_output_folder()
            picked = pick_folder_dialog(current)
            if picked:
                set_output_folder(picked)
            self._json({"output_folder": get_output_folder()})
        elif route == "/reset":
            # Also clear anything left staged by an abandoned or rejected
            # upload, so it cannot join the next batch.
            shutil.rmtree(self.server.staging_dir, ignore_errors=True)
            with JOB_LOCK:
                JOB.update(state="idle", stage=0, message="", lines=[],
                           results=None, counts=None, failed=[])
            self._json({"ok": True})
        else:
            self._send(404, b"not found", "text/plain")

    # -- actions ----------------------------------------------------------
    def _upload(self):
        """One file per request, sent as a raw body. Avoids parsing multipart,
        which left the standard library in 3.13."""
        params = parse_qs(urlparse(self.path).query)
        name = (params.get("name") or ["upload.pdf"])[0]
        # Never trust a client-supplied filename as a path.
        name = Path(name).name
        if not name.lower().endswith(".pdf"):
            self._json({"error": "Only PDF files are accepted."}, 400)
            return

        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_UPLOAD:
            self._json({"error": "That file is empty or too large."}, 400)
            return

        staging = Path(self.server.staging_dir)
        staging.mkdir(parents=True, exist_ok=True)
        target = staging / name
        remaining = length
        looks_like_pdf = True
        first_chunk = True
        # The body is always read to the end even when the content is rejected,
        # otherwise the connection is left half-consumed.
        with open(target, "wb") as handle:
            while remaining > 0:
                chunk = self.rfile.read(min(65536, remaining))
                if not chunk:
                    break
                if first_chunk:
                    looks_like_pdf = chunk.startswith(b"%PDF-")
                    first_chunk = False
                handle.write(chunk)
                remaining -= len(chunk)

        if not looks_like_pdf:
            target.unlink(missing_ok=True)
            self._json({"error": f"{name} is not a PDF file."}, 400)
            return
        self._json({"ok": True, "name": name})

    def _run(self):
        with JOB_LOCK:
            busy = JOB["state"] == "running"
        if busy:
            self._json({"error": "A run is already in progress."}, 409)
            return

        staging = Path(self.server.staging_dir)
        pdfs = sorted(staging.glob("*.pdf")) if staging.is_dir() else []
        if not pdfs:
            self._json({"error": "No PDFs were uploaded."}, 400)
            return

        output_root = Path(get_output_folder())
        try:
            output_root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self._json({"error": f"Cannot write to {output_root}: {exc}"}, 400)
            return

        # Hand the staging directory to the job and start a fresh one, so a
        # second batch can be uploaded while this one runs.
        job_input = staging
        self.server.staging_dir = str(
            Path(self.server.staging_root) /
            f"upload_{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}")

        threading.Thread(target=run_job, args=(job_input, output_root),
                         daemon=True).start()
        self._json({"ok": True, "count": len(pdfs)})


def main():
    parser = argparse.ArgumentParser(description="C-MAGE local web interface.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    staging_root = Path(
        os.environ.get("TMPDIR", "/tmp") if not WINDOWS
        else os.environ.get("TEMP", ".")) / "cmage-uploads"
    staging_root.mkdir(parents=True, exist_ok=True)

    port = args.port
    server = None
    for attempt in range(20):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            port += 1
    if server is None:
        sys.exit("Could not find a free port.")

    server.staging_root = str(staging_root)
    server.staging_dir = str(staging_root / f"upload_{datetime.now():%Y%m%d-%H%M%S}")

    url = f"http://127.0.0.1:{port}/"
    print(f"C-MAGE is running at {url}")
    print("Close this window when you are finished.")
    if not args.no_browser:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
