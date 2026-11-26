#!/usr/bin/env python3
"""Copies the MATLAB and Python functions of ros2neuro_devel_test/{matlab,python} into the documentation and builds the zips to download.

The docs repository is separate from the one of ros2neuro_devel_test, so the page cannot read ../src when it is built: the functions are
copied to docs/reproducibility/files/r2n/ (the page shows their code from there) and zipped (ros2neuro_matlab.zip: the r2n_*.m files only);
the Python ones (python/r2n_*.py) go to files/python/r2n/ and ros2neuro_python.zip.

    python3 tools/sync_matlab.py            # copy and rebuild ros2neuro_matlab.zip
    python3 tools/sync_matlab.py --check    # exit 1 if a copy or the zip is not what the sources give (nothing is written)

Run it from the docs repository after changing anything in ros2neuro_devel_test/matlab/ or python/ .
"""
import argparse
import io
import sys
import zipfile
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent
WS_SRC = DOCS.parent / "src"
DEVEL = WS_SRC / "ros2neuro_devel_test"
OUT = DOCS / "docs" / "reproducibility"
FILES = OUT / "files"

# one entry per language: sources, pattern, copy folder (inside files/), zip, root folder of the zip, README of the zip
LANGS = [
    dict(src=DEVEL / "matlab", pattern="r2n_*.m", copy="r2n", zip=OUT / "ros2neuro_matlab.zip", root="ros2neuro_matlab", readme="""ROS2neuro in MATLAB
===================

One function per stage of the chain (CAR, DC, Laplacian, windows, Butterworth, Welch, FFT, spectrogram, FBCSP, Gaussian, LDA, QDA,
SVM, exponential and buffer integrators, ...). Copy the ones you need. Float32 like ROS 2. The filters use the native functions
of MATLAB (Signal Processing Toolbox: butter, filter, hann, ...).

Docs:    https://ros2neuro.github.io/docs/reproducibility/matlab/
Tests:   https://github.com/ros2neuro/ros2neuro_devel_test
"""),
    dict(src=DEVEL / "python", pattern="r2n_*.py", copy="python/r2n", zip=OUT / "ros2neuro_python.zip", root="ros2neuro_python", readme="""ROS2neuro in Python
===================

The same functions as the MATLAB ones (CAR, DC, Laplacian, windows, Butterworth, Welch, FFT, spectrogram, FBCSP, Gaussian, LDA, QDA,
SVM, integrators, ...) with numpy and scipy, plus the loaders of the .r2nd models, of the scikit-learn models (skops) and of the
deep-learning models (braindecode / PyTorch). Put the folder on sys.path and import the function you need.

Docs:    https://ros2neuro.github.io/docs/reproducibility/python/
Tests:   https://github.com/ros2neuro/ros2neuro_devel_test
"""),
]


def sources(lang):
    """{relative path: bytes} of the files shown by the page."""
    return {f"{lang['copy']}/{p.name}": p.read_bytes() for p in sorted(lang["src"].glob(lang["pattern"]))}


def build_zip(lang, files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(f"{lang['root']}/{name}", date_time=(2026, 1, 1, 0, 0, 0))   # fixed date: the same sources give the same zip
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, data)
    return buf.getvalue()


def sync(lang, check):
    """Returns the list of what is out of date (and fixes it unless `check`)."""
    if not lang["src"].is_dir():
        sys.exit(f"{lang['src']} not found")
    files = sources(lang)
    zipped = build_zip(lang, {**{n.split("/")[-1]: d for n, d in files.items()}, "README.txt": lang["readme"].encode()})
    bad = []
    for name, data in files.items():
        target = FILES / name
        if not target.is_file() or target.read_bytes() != data:
            bad.append(f"files/{name}")
            if not check:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    folder = FILES / lang["copy"]
    for stale in sorted(folder.glob(lang["pattern"])):
        if str(stale.relative_to(FILES)) not in files:
            bad.append(f"files/{stale.relative_to(FILES)} (not in the sources any more)")
            if not check:
                stale.unlink()
    if not lang["zip"].is_file() or lang["zip"].read_bytes() != zipped:
        bad.append(lang["zip"].name)
        if not check:
            lang["zip"].write_bytes(zipped)
    return files, zipped, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    failed = False
    for lang in LANGS:
        files, zipped, bad = sync(lang, args.check)
        if args.check:
            if bad:
                print("out of date:", *bad, sep="\n  ")
                failed = True
            else:
                print(f"ok: {len(files)} files and {lang['zip'].name} are what the sources give")
        else:
            print(f"{len(files)} files copied to {(FILES / lang['copy']).relative_to(DOCS)}, {lang['zip'].name} ({len(zipped) // 1024} KB); changed: {', '.join(bad) or 'nothing'}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
