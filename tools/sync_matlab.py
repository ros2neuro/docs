#!/usr/bin/env python3
"""Copies the MATLAB functions of ros2neuro_devel_test/matlab into the documentation and builds the zip to download.

The docs repository is separate from the one of ros2neuro_devel_test, so the page cannot read ../src when it is built: the functions are
copied to docs/reproducibility/files/r2n/ (the page shows their code from there) and zipped (ros2neuro_matlab.zip: the r2n_*.m files only).

    python3 tools/sync_matlab.py            # copy and rebuild ros2neuro_matlab.zip
    python3 tools/sync_matlab.py --check    # exit 1 if a copy or the zip is not what the sources give (nothing is written)

Run it from the docs repository after changing anything in ros2neuro_devel_test/matlab/ .
"""
import argparse
import io
import sys
import zipfile
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent
WS_SRC = DOCS.parent / "src"
DEVEL = WS_SRC / "ros2neuro_devel_test"
SRC = DEVEL / "matlab"
OUT = DOCS / "docs" / "reproducibility"
FILES = OUT / "files"
ZIP = OUT / "ros2neuro_matlab.zip"
ROOT = "ros2neuro_matlab"

README = """ROS2neuro in MATLAB
===================

One function per stage of the chain (CAR, DC, Laplacian, windows, Butterworth, Welch, FFT, spectrogram, FBCSP, Gaussian, LDA, QDA,
SVM, exponential and buffer integrators, ...). Copy the ones you need. Float32 like ROS 2. The filters use the native functions
of MATLAB (Signal Processing Toolbox: butter, filter, hann, ...).

Docs:    https://ros2neuro.github.io/docs/reproducibility/matlab/
Tests:   https://github.com/ros2neuro/ros2neuro_devel_test
"""

def sources():
    """{relative path: bytes} of the .m files shown by the page."""
    return {f"r2n/{p.name}": p.read_bytes() for p in sorted(SRC.glob("r2n_*.m"))}


def build_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(f"{ROOT}/{name}", date_time=(2026, 1, 1, 0, 0, 0))   # fixed date: the same sources give the same zip
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, data)
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    check = args.check
    if not SRC.is_dir():
        sys.exit(f"{SRC} not found")
    files = sources()
    zipped = build_zip({**{n.split("/")[1]: d for n, d in files.items()}, "README.txt": README.encode()})
    bad = []
    for name, data in files.items():
        target = FILES / name
        if not target.is_file() or target.read_bytes() != data:
            bad.append(f"files/{name}")
            if not check:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    for stale in sorted(FILES.rglob("*.m")):
        if str(stale.relative_to(FILES)) not in files:
            bad.append(f"files/{stale.relative_to(FILES)} (not in the sources any more)")
            if not check:
                stale.unlink()
    if not ZIP.is_file() or ZIP.read_bytes() != zipped:
        bad.append(ZIP.name)
        if not check:
            ZIP.write_bytes(zipped)
    if check:
        if bad:
            print("out of date:", *bad, sep="\n  ")
            sys.exit(1)
        print(f"ok: {len(files)} files and {ZIP.name} are what the sources give")
    else:
        print(f"{len(files)} files copied to {FILES.relative_to(DOCS)}, {ZIP.name} ({len(zipped) // 1024} KB); changed: {', '.join(bad) or 'nothing'}")


if __name__ == "__main__":
    main()
