"""Run a local, isolated rehearsal of the second expert assessment."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8509)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    with socket.socket() as sock:
        try:
            sock.bind(('127.0.0.1', args.port))
        except OSError:
            raise SystemExit(f'Port {args.port} is occupied. Choose another --port.')
    work = Path(tempfile.mkdtemp(prefix='facct-study1-round2-preview-'))
    env = dict(os.environ, STUDY1_LOCAL_PREVIEW='1',
               STUDY1_PREVIEW_ID='LOCAL_PREVIEW_STUDY1_ROUND2',
               STUDY1_PREVIEW_DATA_ROOT=str(work / 'synthetic_logs'),
               PYTHONPATH=str(ROOT / 'src'))
    for key in list(env):
        if key.startswith('GITHUB_'):
            env.pop(key)
    manifest = dict(mode='synthetic_local_preview', remote_writes=False,
                    root=str(work), url=f'http://localhost:{args.port}/',
                    entry_point='apps/study1_validation_v2.py')
    with (work / 'server.log').open('w') as log:
        process = subprocess.Popen([
            sys.executable, '-m', 'streamlit', 'run',
            str(ROOT / manifest['entry_point']), '--server.address', '127.0.0.1',
            '--server.port', str(args.port), '--server.headless', 'true',
            '--browser.gatherUsageStats', 'false', '--server.fileWatcherType', 'none',
        ], cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT)
    try:
        manifest['pid'] = process.pid
        destination = args.output or work / 'manifest.json'
        destination.write_text(json.dumps(manifest, indent=2) + '\n')
        for _ in range(80):
            if process.poll() is not None:
                raise RuntimeError('The preview stopped; inspect its server.log.')
            try:
                with urlopen(f'http://127.0.0.1:{args.port}/_stcore/health', timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(.25)
        else:
            raise RuntimeError('The preview did not become available.')
        print(json.dumps(manifest, indent=2), flush=True)
        signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
        while process.poll() is None:
            time.sleep(1)
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=15)


if __name__ == '__main__':
    main()
