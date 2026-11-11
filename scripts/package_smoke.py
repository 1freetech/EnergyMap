"""Smoke-test a packaged desktop GUI by verifying it stays running briefly.

This is a launch check, not an interactive acceptance test. On Linux run
under xvfb-run; do not claim Windows/macOS validation from this check.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    parser.add_argument("--seconds", type=float, default=4.0)
    args = parser.parse_args()
    binary = args.executable.resolve()
    if not binary.is_file():
        parser.error(f"Missing packaged executable: {binary}")
    proc = subprocess.Popen([str(binary)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic() + args.seconds
        while time.monotonic() < deadline:
            code = proc.poll()
            if code is not None:
                out, err = proc.communicate(timeout=2)
                print(f"Packaged GUI exited early (code {code})\n{out.decode(errors='replace')}\n{err.decode(errors='replace')}", file=sys.stderr)
                return 1
            time.sleep(0.2)
        print(f"Packaged GUI remained running for {args.seconds:.1f} seconds: {binary.name}")
        return 0
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
