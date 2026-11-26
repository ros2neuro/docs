# Acquisition: tests and replication

!!! info ""
    Plugins: [Acquisition](../../packages/acquisition/index.md) · part of [Reproducibility](../index.md) › [Packages](index.md)

How the acquisition is checked: the **XDF** plugin is the reference of every other test: it publishes the GDF exactly, sample by sample, and the manager's trials are checked on the events. Nothing is computed, so there is no function to replay: the check compares the published samples with the ones of the file.

| Test (`ros2neuro_devel_test`) | What it checks | Check | MATLAB functions | Python functions |
|---|---|---|---|---|
| `acquisition/` | the XDF plugin publishes the GDF exactly; the 6 trials of the manager (calibration) | `check_acquisition` | none | none |

How to run a test: [Packages](index.md#run-the-checks). Every function is explained, with its code, in [MATLAB](../matlab.md) and [Python](../python.md); [download them](../download.md).

## Acquisition (base package)

The package includes unit tests for basic node behavior, including:

- configuration failure when `plugin` is empty
- configuration failure when the requested plugin does not exist

Run them with:

```bash
colcon test --packages-select ros2neuro_acquisition
```

## Dummy device

The package includes unit tests covering:

- parameter-driven configuration
- frame info generation
- runtime read behavior
- trigger generation
- invalid parameter rejection

Run them with:

```bash
colcon test --packages-select ros2neuro_acquisition_dummy
```

## eegdev device

The package currently includes:

- unit tests for `EGDOpenOptions`
- a pluginlib loading test for `EGDDevice`
- a file-based integration test using `test/test_short.gdf` (skipped when the `libeegdev` datafile backend cannot
  open it)

Run them with:

```bash
colcon test --packages-select ros2neuro_acquisition_eegdev
```

The automated `.gdf` integration tests use the 60-second fixture
`test/test_short.gdf`. The longer `test/test.gdf` file remains available for
manual and exploratory checks.

The end-to-end round-trip test that validates `eegdev -> recorder_xdf -> gdf`
lives in the [`ros2neuro_recorder_xdf`](../../packages/recorder/xdf.md) package, because it exercises recorder
behavior in addition to acquisition.

The `.gdf` integration tests use a short temporary path under `/tmp` before
opening the file, because some `libeegdev` setups are sensitive to long file paths.

## LSL device

### Testing the Plugin

#### Test files in `test/`

| File | Role |
|---|---|
| `rawdata.csv` | Ground-truth input: a multi-channel recording saved as comma-separated `float32` rows (no header). Each row is one sample; columns are EEG channels followed by the trigger channel. |
| `test_config.yaml` | Parameter file for the acquisition node: plugin `LSLDevice`, stream name `TestStream`, 31 EEG channels + 1 trigger channel, framerate 16 Hz. |
| `lsl_csv_streamer.py` | ROS2 node that reads `rawdata.csv` and publishes it block-by-block as a real LSL Outlet (type `EEG`, name `TestStream`, 512 Hz, 32 samples/block at 16 Hz) to emulate a real EEG device. Prints `Finished streaming CSV data via LSL.` when the file ends. |
| `topic_saver.py` | ROS2 node that subscribes to `/acquisition/neurodata`, unpacks each `NeuroFrame` sample by sample, and appends every row (EEG channels then trigger channel) to a CSV file. |
| `test_lsl_device.cpp` | gtest. Besides the configuration/state tests it opens a real in-process LSL outlet and checks that frames are read continuously and that `read()` fails (`is_stream_lost()`) once the outlet disappears; also checks that destroying a never-configured device does not crash. |
| `test_config_yaml.py` | pytest: the shipped `config/lsl_configuration.yaml` contains no unresolved launch substitutions and has a numeric `framerate`. |
| `compare_acquisition.m` | MATLAB script for visual and numerical verification (see below). |
| `test_acquisition_lsl.launch.py` | Launch file (in `test/`, installed to the package `launch/` directory) that starts the full test pipeline (see below). |

---

#### End-to-end test with MATLAB

The test verifies that the plugin acquires data without any loss or alteration. `rawdata.csv` is used as a known reference: it is replayed as a real LSL stream, the acquisition node receives it and publishes it on ROS2, the received data is saved to `acquired_data.csv`, and the two files are compared in MATLAB. If the plugin is correct, the two signals are numerically identical.

##### Step 1 — build and source

```bash
cd ~/ros2neuro_ws
colcon build --packages-select ros2neuro_acquisition_lsl
source install/setup.bash
```

##### Step 2 — run the test launcher

```bash
ros2 launch ros2neuro_acquisition_lsl test_acquisition_lsl.launch.py
```

This starts four processes simultaneously:

1. **`lsl_csv_streamer.py`** — reads `rawdata.csv` and streams it as a 512 Hz LSL Outlet named `TestStream`, pushing 32 samples per tick at 16 Hz to emulate a real device.
2. **`acquisition` node** — loads the `LSLDevice` plugin, discovers `TestStream` by name, and publishes the acquired data on `/acquisition/neurodata` at 16 Hz (32 samples/frame, 31 EEG channels + 1 trigger).
3. **`neuroviz`** — real-time visualizer of the incoming `NeuroFrame` stream.
4. **`topic_saver.py`** — subscribes to `/acquisition/neurodata` and saves every received sample row by row to `acquired_data.csv` in the installed `test/` directory.

Wait until the terminal prints `Finished streaming CSV data via LSL.`, then stop with **CTRL+C**.

##### Step 3 — verify in MATLAB

Open MATLAB and run `compare_acquisition` from anywhere inside the package (source or install tree — the script finds `acquired_data.csv` automatically):

```matlab
compare_acquisition
```

**What the script does:**

1. Loads `rawdata.csv` (LSL input, 32 columns: 31 EEG + 1 trigger) and `acquired_data.csv` (ROS2 output).
2. Finds the temporal alignment offset by scanning `rawdata.csv` for the first row of `acquired_data.csv`. A few samples at the start of `rawdata.csv` are always dropped during LSL connection startup — the script skips them automatically.
3. Computes the error separately for EEG channels and the trigger channel.
4. Prints a report in the MATLAB console:

```
Raw data   : .../test/rawdata.csv
Acquired   : .../test/acquired_data.csv
Raw      : 10240 samples x 32 channels
Acquired : 10240 samples x 32 channels
Alignment offset : N samples dropped at LSL connection startup

--- Results ---
Samples compared              : 10240
EEG  max absolute error       : 5.0022e-12
EEG  mean absolute error      : ~0
Trigger cast error (vs int32) : 0          (expected 0)
Verdict: PERFECT MATCH
```

5. Opens three figures:

**Figure 1 — EEG signal comparison**

The first 6 EEG channels of `rawdata.csv` (blue) and `acquired_data.csv` (red dashed) overlaid. The two traces must be perfectly superimposed.

**Figure 2 — EEG absolute error**

The pointwise `|raw − acquired|` for the same 6 EEG channels. A flat black line at 0 means perfect acquisition. The figure title shows the max error and the verdict.

**Figure 3 — Trigger channel**

Two subplots:
- *Top*: raw float32 trigger (blue stairs), expected `int32(raw)` truncation (green stairs), and acquired trigger (red dashed stairs). All three must overlap.
- *Bottom*: `|int32(raw) − acquired|` per sample. Must be a flat line at 0.

The comparison is against `fix(raw)` (MATLAB) which replicates C++ `static_cast<int32_t>` — both truncate toward zero. Note: MATLAB's `int32()` would be wrong here because it rounds to nearest (`int32(0.9999) = 1`) while the plugin truncates (`static_cast<int32_t>(0.9999f) = 0`). A raw float like `0.9999` becomes `0` in the acquired data, so raw-vs-acquired differs by up to 1.0 — which is expected. What matters is that `acquired == fix(raw)` exactly (cast error = 0).

> **EEG error ~5e-12** — normal float32 rounding, counts as **PERFECT MATCH**.
> **Trigger cast error 0** — the int32 truncation was applied correctly.

## XDF / GDF replay device

### Tests of the whole stack

[`ros2neuro_devel_test`](https://github.com/ros2neuro/ros2neuro_devel_test) (`acquisition/`) replays `data/test.gdf` with this plugin and checks, in MATLAB, that every sample, the 32 samples per frame, the 16 frames per second and the events of the manager are exactly what the file holds; it also draws the signal of ros2neuro against the file and their difference. Run: `acquisition/acquisition.launch.py` then `check_acquisition`; the check is a MATLAB file you read from the top (see the README of that package).
