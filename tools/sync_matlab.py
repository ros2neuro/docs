#!/usr/bin/env python3
"""Copies the MATLAB functions of ros2neuro_devel_test into the documentation and builds the two zips to download.

The docs repository is separate from the one of ros2neuro_devel_test, so the page cannot read ../src when it is built: the files are
copied to docs/reproducibility/files/ (the page shows their code from there) and zipped.

  ros2neuro_matlab.zip          the r2n/ functions, check_functions.m, check_evaluation.m and reference/: the first REFERENCE_ROWS
                                samples of the input and of the ROS 2 output of every filter (the CSV in ros2neuro_filters_*/test/) and the
                                .r2nd of the test model, so that check_functions passes every line with nothing else.
  ros2neuro_matlab_example.zip  one recorded evaluation (GDF + CSV of every topic + the yaml and the model of the launcher), so that
                                check_evaluation runs with nothing else. Built only when asked (--example), from a run you checked.

    python3 tools/sync_matlab.py                          # copy and rebuild ros2neuro_matlab.zip
    python3 tools/sync_matlab.py --example GDF RUN_FOLDER # also rebuild ros2neuro_matlab_example.zip from that run
    python3 tools/sync_matlab.py --check                  # exit 1 if a copy or a zip is not what the sources give (nothing is written)

Run it from the docs repository after changing anything in ros2neuro_devel_test/matlab/ or in the CSV of the filter packages.
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
LAUNCHER = DEVEL / "launch" / "gaussian_4class"
OUT = DOCS / "docs" / "reproducibility"
FILES = OUT / "files"
ZIP = OUT / "ros2neuro_matlab.zip"
EXAMPLE_ZIP = OUT / "ros2neuro_matlab_example.zip"
ROOT = "ros2neuro_matlab"

# Every filter is causal or works one frame (32 samples) at a time: the first rows of the ROS 2 output are the filter of the first
# rows of the input. 512 rows = 16 frames = 1 s at 512 Hz.
REFERENCE_ROWS = 512
FILTER_CSV = {
    "ros2neuro_filters": ["rawdata.csv", "output_data.csv"],
    "ros2neuro_filters_car": ["rawdata.csv", "output_data.csv"],
    "ros2neuro_filters_dc": ["rawdata.csv", "output_data.csv"],
    "ros2neuro_filters_laplacian": ["rawdata.csv", "output_data.csv"],
    "ros2neuro_filters_hann": ["rawdata.csv", "output_data.csv"],
    "ros2neuro_filters_hamming": ["rawdata.csv", "output_data.csv"],
    "ros2neuro_filters_blackman": ["rawdata.csv", "output_data.csv"],
    "ros2neuro_filters_flattop": ["rawdata.csv", "output_data.csv"],
    "ros2neuro_filters_butterworth": ["rawdata.csv", "output_data_lowpass.csv", "output_data_highpass.csv"],
}
REFERENCE_MODEL = LAUNCHER / "model" / "fake_4class_gaussian.r2nd"
# what check_evaluation reads from the launcher folder
LAUNCHER_FILES = ["config/pipeline.yaml", "config/layout.yaml", "config/integrator_exponential.yaml",
                  "config/protocol_evaluation.yaml", "model/manifest.yaml", "model/fake_4class_gaussian.r2nd"]

README = """ROS2neuro in MATLAB
===================

r2n/                 one function per stage of the chain (CAR, DC, Laplacian, windows, Butterworth, Welch, Gaussian, integrator, ...).
                     Copy the ones you need. Float32 like ROS 2, no toolbox.
check_functions.m    checks every function: the filters against the output of the ROS 2 nodes (reference/, the first 512 samples
                     of the CSV of the ros2neuro_filters_* packages), the others on cases whose answer is known.
                     check_functions('/path/to/src') uses the full CSV of a workspace instead.
check_evaluation.m   the whole chain (Laplacian, Welch, Gaussian, integrator, outcome of every trial) on a recorded evaluation,
                     compared with what ROS 2 published. Unzip ros2neuro_matlab_example.zip here (it adds example/) and run it
                     with no arguments. Needs BIOSIG for sload (reading the GDF).

Start:   check_functions        then, with the example:   check_evaluation
Docs:    https://ros2neuro.github.io/docs/reproducibility/matlab/
"""

EXAMPLE_README = """Example for check_evaluation.m
==============================

One evaluation of ros2neuro_devel_test/launch/gaussian_4class (4 classes, 8 trials), recorded with
    ros2 launch ros2neuro_devel_test gaussian_4class_matlab.launch.xml

evaluation.gdf       the raw EEG and the events of the protocol, written by the recorder
run/                 a CSV of every topic of the run (raw, filtered, psd, prediction, integrated, flow, events), meta.txt
gaussian_4class/     the yaml files and the model the launcher used (check_evaluation reads every parameter from them)

Unzip it next to ros2neuro_matlab.zip (both extract into ros2neuro_matlab/), then in MATLAB:  check_evaluation
"""


def head_rows(data, rows):
    """The first `rows` lines of a CSV without header."""
    lines = data.split(b"\n")
    return b"\n".join(lines[:rows]) + b"\n"


def sources():
    """{relative path: bytes} of the .m files shown by the page."""
    files = {f"r2n/{p.name}": p.read_bytes() for p in sorted((SRC / "r2n").glob("*.m"))}
    for name in ("check_functions.m", "check_evaluation.m"):
        files[name] = (SRC / name).read_bytes()
    return files


def reference():
    """{relative path: bytes} of reference/: the cropped CSV of the filter packages and the test model."""
    files = {}
    for pkg, names in FILTER_CSV.items():
        for name in names:
            path = WS_SRC / pkg / "test" / name
            if not path.is_file():
                sys.exit(f"{path} not found (run run_ros_pipeline.sh of {pkg})")
            files[f"reference/{pkg}/test/{name}"] = head_rows(path.read_bytes(), REFERENCE_ROWS)
    files[f"reference/{REFERENCE_MODEL.name}"] = REFERENCE_MODEL.read_bytes()
    return files


def launcher_files():
    return {f"example/gaussian_4class/{name}": (LAUNCHER / name).read_bytes() for name in LAUNCHER_FILES}


def example(gdf, run):
    files = {"example/README.txt": EXAMPLE_README.encode(), "example/evaluation.gdf": Path(gdf).read_bytes()}
    for p in sorted(Path(run).iterdir()):
        if p.suffix in (".csv", ".txt"):
            files[f"example/run/{p.name}"] = p.read_bytes()
    files.update(launcher_files())
    return files


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
    ap.add_argument("--example", nargs=2, metavar=("GDF", "RUN_FOLDER"))
    args = ap.parse_args()
    check = args.check
    if not (SRC / "r2n").is_dir():
        sys.exit(f"{SRC / 'r2n'} not found")
    files = sources()
    zipped = build_zip({**files, **reference(), "README.txt": README.encode()})
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
    if args.example and not check:
        EXAMPLE_ZIP.write_bytes(build_zip(example(*args.example)))
        bad.append(EXAMPLE_ZIP.name)
    # the example must still carry the yaml and the model of the launcher
    if EXAMPLE_ZIP.is_file():
        with zipfile.ZipFile(EXAMPLE_ZIP) as z:
            for name, data in launcher_files().items():
                try:
                    same = z.read(f"{ROOT}/{name}") == data
                except KeyError:
                    same = False
                if not same:
                    bad.append(f"{EXAMPLE_ZIP.name}: {name} differs from the launcher (rebuild it with --example from a new run)")
    else:
        bad.append(f"{EXAMPLE_ZIP.name} missing (build it with --example)")
    if check:
        if bad:
            print("out of date:", *bad, sep="\n  ")
            sys.exit(1)
        print(f"ok: {len(files)} files, {ZIP.name} and {EXAMPLE_ZIP.name} are what the sources give")
    else:
        print(f"{len(files)} files copied to {FILES.relative_to(DOCS)}, {ZIP.name} ({len(zipped) // 1024} KB)"
              + (f", {EXAMPLE_ZIP.name} ({EXAMPLE_ZIP.stat().st_size // 1024} KB)" if EXAMPLE_ZIP.is_file() else "")
              + f"; changed: {', '.join(b for b in bad if not b.endswith('--example)')) or 'nothing'}")


if __name__ == "__main__":
    main()
