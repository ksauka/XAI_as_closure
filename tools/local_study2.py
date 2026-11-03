"""Start the eight isolated local Streamlit previews. Never launches recruitment."""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-port", type=int, default=8501)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    apps = sorted((ROOT / "apps").glob("study2_0*.py"))
    ports = list(range(args.base_port, args.base_port + len(apps)))
    for port in ports:
        with socket.socket() as sock:
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                raise SystemExit(
                    f"Port {port} is occupied; choose another --base-port."
                )
    run_root = Path(tempfile.mkdtemp(prefix="facct-study2-preview-"))
    processes = []
    manifest = {
        "mode": "synthetic_local_preview",
        "remote_writes": False,
        "root": str(run_root),
        "apps": [],
    }
    try:
        for index, (app, port) in enumerate(zip(apps, ports)):
            bits = (index // 4, (index // 2) % 2, index % 2)
            condition = "P{}_A{}_F{}".format(*bits)
            work = run_root / condition
            work.mkdir()
            env = dict(
                os.environ,
                STUDY2_LOCAL_PREVIEW="1",
                STUDY2_PREVIEW_ID=f"LOCAL_PREVIEW_{condition}",
                STUDY2_PREVIEW_DATA_ROOT=str(work / "synthetic_logs"),
                PYTHONPATH=str(ROOT / "src"),
            )
            for key in list(env):
                if key.startswith("GITHUB_"):
                    env.pop(key)
            with open(work / "server.log", "w") as log:
                process = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "streamlit",
                        "run",
                        str(app),
                        "--server.address",
                        "127.0.0.1",
                        "--server.port",
                        str(port),
                        "--server.headless",
                        "true",
                        "--browser.gatherUsageStats",
                        "false",
                        "--server.fileWatcherType",
                        "none",
                    ],
                    cwd=work,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
            processes.append(process)
            manifest["apps"].append(
                {
                    "condition_id": condition,
                    "app": app.name,
                    "port": port,
                    "pid": process.pid,
                    "url": f"http://localhost:{port}/?embed=true",
                }
            )
        destination = args.output or run_root / "manifest.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(manifest, indent=2) + "\n")
        for entry in manifest["apps"]:
            for attempt in range(40):
                try:
                    with urlopen(
                        f"http://127.0.0.1:{entry['port']}/_stcore/health", timeout=1
                    ) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(0.25)
            else:
                raise RuntimeError(f"Preview did not start: {entry['condition_id']}")
        print(json.dumps(manifest, indent=2), flush=True)
        signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
        while all(process.poll() is None for process in processes):
            time.sleep(1)
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            process.wait(timeout=15)


if __name__ == "__main__":
    main()
