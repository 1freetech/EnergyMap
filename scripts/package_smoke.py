"""Validate packaged data, then smoke-test that the desktop GUI stays open.

A PyInstaller onefile GUI on Windows spawns a child process. A plain
Popen.terminate() can terminate the parent while the child keeps inherited
stdout/stderr pipes open, hanging communicate(). Discard GUI stdio and use
Windows taskkill /T to terminate the full process tree after a clean check.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    parser.add_argument("--seconds", type=float, default=5.0)
    args = parser.parse_args()
    binary = args.executable.resolve()
    if not binary.is_file():
        parser.error(f"Packaged executable missing: {binary}")
    try:
        checked = subprocess.run([str(binary), "--check-data"], capture_output=True, timeout=90)
    except subprocess.TimeoutExpired:
        print("Packaged data check exceeded 90 seconds", file=sys.stderr)
        return 1
    if checked.returncode:
        print(f"Bundled data check failed ({checked.returncode}):\n"
              f"{checked.stdout.decode(errors='replace')}\n{checked.stderr.decode(errors='replace')}",
              file=sys.stderr)
        return 1

    # No PIPE handles can be inherited by the PyInstaller bootstrap child.
    proc = subprocess.Popen([str(binary)], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic() + args.seconds
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                print(f"GUI exited early with code {proc.returncode}", file=sys.stderr)
                return 1
            time.sleep(.2)
        print(f"Packaged GUI remained open for {args.seconds:.1f} seconds: {binary.name}")
        return 0
    finally:
        if proc.poll() is None:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=15, check=False)
            else:
                proc.terminate()
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=8)


if __name__ == "__main__":
    raise SystemExit(main())
