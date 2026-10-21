# LSL device

!!! info ""
    Package: [`ros2neuro_acquisition_lsl`](https://github.com/ros2neuro/ros2neuro_acquisition_lsl) · pluginlib class: `ros2neuro::acquisition::LSLDevice` · part of [Acquisition](index.md)

`ros2neuro_acquisition_lsl` is a plugin for the [`ros2neuro_acquisition`](index.md) framework. It implements the [`ros2neuro::acquisition::NeuroDevice`](index.md) interface and allows the acquisition node to connect to and stream data from any active **Lab Streaming Layer (LSL)** Outlet present on the network, bridging external software (e.g., OpenViBE, EEGLAB, BrainProducts, g.tec) directly into the `ros2neuro` ROS2 ecosystem.

The plugin class exported via `pluginlib` is:

```text
ros2neuro::acquisition::LSLDevice
```

---

## How it works

`LSLDevice` discovers the LSL Outlet at startup and streams data into a `NeuroFrame` message published on `/acquisition/neurodata`.

**Stream discovery** — on `open()`, the device resolves the LSL stream by name if `stream_name` is set, otherwise by `stream_type`. It waits up to 5 seconds for a matching stream to appear on the network.

**Background reader thread** — once started, a dedicated thread calls `lsl::stream_inlet::pull_sample()` in a tight loop (0.5 s timeout per call) and stores incoming samples in a thread-safe ring buffer (a `std::deque` capped at `max_buffered_samples`). If the buffer fills up, the oldest samples are discarded.

**Frame assembly** — the main acquisition thread calls `read()` at the configured `framerate`. It dequeues exactly `samples_per_frame = floor(samplerate / framerate)` samples from the ring buffer and copies them into the `NeuroFrame`.

**Channel layout resolution** — how the LSL stream's flat channel array is split into EEG sensor channels, EXG sensor channels, and trigger channels is resolved once in `setup()`, with the following precedence:

1. **Explicit YAML labels** (`sensors.eeg.labels`, `sensors.exg.labels`, `triggers.trigger.labels`) always win over anything the stream declares about itself. If any enabled block has a non-empty `labels` list, the plugin falls back to the manual/legacy layout: the stream's flat channel array is split *in order* into contiguous EEG, then EXG, then trigger blocks, with each block's channel count equal to its configured label count. If no labels are given at all across every enabled block **and** the stream provides no usable per-channel metadata either, every channel is assigned to EEG (fallback labels `CH1`, `CH2`, …) — this is the plugin's historical behavior, preserved for streams/configs that never described their channels individually.
2. **Stream-declared channel metadata** — if no block has explicit YAML labels, and the LSL stream's `stream_info::desc()` XML fully describes every physical channel with a `<channels><channel><label/><type/></channel>…</channels>` block (the de-facto LSL convention used by many real acquisition devices), the plugin classifies each channel by its declared `<type>`: `EEG` → EEG block, `Trigger`/`Triggers`/`Marker`/`Markers`/`Stim`/`Stimulus` → trigger block, and **everything else non-EEG lands in the EXG ("other") block** — so auxiliary/misc channels are no longer silently folded into EEG. Channels whose block is disabled (`enable: false`) are dropped. A channel with an empty `<label>` still gets a fallback name (`CH`/`EXG`/`TRI` + its position within its block).

Either way, the resulting channels need not be contiguous in the raw LSL sample array — the plugin gathers each block by its actual physical channel indices when filling the `NeuroFrame`.

**Trigger quantization** — trigger values are cast from `float32` (the LSL sample format) to `int32` when filling the `NeuroTrigger` block.

---

## Launch files

### `acquisition_visualization.launch.py` — production launch

Starts the acquisition node and the visualizer against any active LSL stream on the network. Use this for normal operation with real hardware.

```bash
ros2 launch ros2neuro_acquisition_lsl acquisition_visualization.launch.py
```

| Argument | Default | Description |
|---|---|---|
| `config` | `config/lsl_configuration.yaml` | Parameter file for the acquisition node |

### `test/test_acquisition_lsl.launch.py` — test launch

Defined in `test/` and installed to the package launch directory. Starts the full test pipeline: streams `rawdata.csv` as a real LSL outlet, acquires it through the plugin, shows it in the visualizer, and saves the result to `acquired_data.csv`. After stopping, open MATLAB and run `compare_acquisition.m` to compare the two files.

```bash
ros2 launch ros2neuro_acquisition_lsl test_acquisition_lsl.launch.py
```

| Argument | Default | Description |
|---|---|---|
| `csv_path` | `test/rawdata.csv` | CSV file replayed as LSL stream |
| `output_csv` | `test/acquired_data.csv` | Output file saved for MATLAB comparison |
| `config` | `test/test_config.yaml` | Parameter file for the acquisition node |

---

## Standalone executable

A standalone entry point that wires `LSLDevice` directly without loading it via pluginlib:

```bash
ros2 run ros2neuro_acquisition_lsl acquisition_lsl
```

---

## Parameters

All parameters are declared under the prefix that `NeuroAcquisitionNode` passes to `configure()`. With the `lsl_configuration.yaml` configuration that prefix is `device`; with the test configuration it is `acquisition`. The table below uses `<prefix>` to indicate that slot.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `<prefix>.stream_type` | `string` | `"EEG"` | LSL stream type used for discovery when `stream_name` is empty |
| `<prefix>.stream_name` | `string` | `""` | LSL stream name for discovery; takes priority over `stream_type` when non-empty |
| `<prefix>.framerate` | `double` | `16.0` | Requested publish rate in Hz; actual rate is `samplerate / floor(samplerate / framerate)` |
| `<prefix>.max_buffered_samples` | `int` | `5120` | Maximum number of samples held in the internal ring buffer before oldest are dropped |
| `<prefix>.sensors.eeg.enable` | `bool` | `true` | Enable the EEG sensor block |
| `<prefix>.sensors.eeg.name` | `string` | `"EEG"` | Name tag for the EEG sensor in the NeuroFrame |
| `<prefix>.sensors.eeg.labels` | `string[]` | `[]` | Channel labels; length also determines the number of EEG channels taken from the LSL stream |
| `<prefix>.sensors.exg.enable` | `bool` | `false` | Enable the EXG sensor block |
| `<prefix>.sensors.exg.name` | `string` | `"EXG"` | Name tag for the EXG sensor in the NeuroFrame |
| `<prefix>.sensors.exg.labels` | `string[]` | `[]` | Channel labels for the EXG block |
| `<prefix>.triggers.trigger.enable` | `bool` | `true` | Enable the trigger block |
| `<prefix>.triggers.trigger.name` | `string` | `"TRI"` | Name tag for the trigger block in the NeuroFrame |
| `<prefix>.triggers.trigger.labels` | `string[]` | `[]` | Channel labels for the trigger block |

> **Channel count resolution.** If any enabled block has explicit `labels`, the plugin maps those exact counts from the LSL stream, in order (EEG first, then EXG, then triggers) — YAML always overrides the stream. Otherwise, if the LSL stream fully describes its own channels (a `<channels><channel><label/><type/></channel>…` block for every channel), each channel is classified by its declared `<type>`: `EEG` → EEG block, trigger/marker types → trigger block, anything else → EXG. Only if neither source is available are all LSL channels assigned to the EEG block. See "Channel layout resolution" above for the full precedence rules.

### Example configuration

```yaml
acquisition:
  ros__parameters:
    acquisition.plugin: "ros2neuro::acquisition::LSLDevice"

    device:
      stream_type: "EEG"
      stream_name: ""
      framerate: 16.0
      max_buffered_samples: 5120

      sensors:
        eeg:
          enable: true
          name: "EEG"
          labels: ["CH1", "CH2", "CH3", "CH4", "CH5", "CH6", "CH7", "CH8",
                   "CH9", "CH10", "CH11", "CH12", "CH13", "CH14", "CH15", "CH16",
                   "CH17", "CH18", "CH19", "CH20", "CH21", "CH22", "CH23", "CH24",
                   "CH25", "CH26", "CH27", "CH28", "CH29", "CH30", "CH31"]
        exg:
          enable: false
          name: "EXG"

      triggers:
        trigger:
          enable: true
          name: "TRI"
          labels: ["TRIG"]
```

---

## Dependencies

### Runtime (C++)

| Dependency | Version | Role |
|---|---|---|
| `liblsl` | ≥ 1.16 | LabStreamingLayer C++ library — stream discovery, `stream_inlet`, sample pull |
| `rclcpp` | ROS2 (Humble+) | ROS2 C++ client library |
| `pluginlib` | ROS2 | Plugin loading and class registration macros |
| [`ros2neuro_acquisition`](index.md) | — | `NeuroDevice` base class and `NeuroAcquisitionNode` |
| [`ros2neuro_data`](../msgs-data.md#ros2neuro_data) | — | `NeuroFrame`, `NeuroSensor`, `NeuroTrigger` data structures |
| [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs) | — | `NeuroFrame`, `NeuroSensorInfo` ROS2 message definitions |

### Build

| Dependency | Role |
|---|---|
| `ament_cmake` | CMake build system for ROS2 packages |

### Test only

| Dependency | Role |
|---|---|
| `ament_cmake_gtest` | C++ unit test runner (`test_lsl_device.cpp`) |
| `ament_cmake_pytest` | Python test runner |
| `launch_testing_ament_cmake` | End-to-end launch test support |
| `pylsl` (`python3-pylsl`) | Python LSL library used by the CSV streamer script |

Install the Python LSL library if not already present:

```bash
pip install pylsl
```

---

## Testing the Plugin

### Test files in `test/`

| File | Role |
|---|---|
| `rawdata.csv` | Ground-truth input: a multi-channel recording saved as comma-separated `float32` rows (no header). Each row is one sample; columns are EEG channels followed by the trigger channel. |
| `test_config.yaml` | Parameter file for the acquisition node: plugin `LSLDevice`, stream name `TestStream`, 31 EEG channels + 1 trigger channel, framerate 16 Hz. |
| `lsl_csv_streamer.py` | ROS2 node that reads `rawdata.csv` and publishes it block-by-block as a real LSL Outlet (type `EEG`, name `TestStream`, 512 Hz, 32 samples/block at 16 Hz) to emulate a real EEG device. Prints `Finished streaming CSV data via LSL.` when the file ends. |
| `topic_saver.py` | ROS2 node that subscribes to `/acquisition/neurodata`, unpacks each `NeuroFrame` sample by sample, and appends every row (EEG channels then trigger channel) to a CSV file. |
| `compare_acquisition.m` | MATLAB script for visual and numerical verification (see below). |
| `test_acquisition_lsl.launch.py` | Launch file (in `launch/`) that starts the full test pipeline (see below). |

---

### End-to-end test with MATLAB

The test verifies that the plugin acquires data without any loss or alteration. `rawdata.csv` is used as a known reference: it is replayed as a real LSL stream, the acquisition node receives it and publishes it on ROS2, the received data is saved to `acquired_data.csv`, and the two files are compared in MATLAB. If the plugin is correct, the two signals are numerically identical.

#### Step 1 — build and source

```bash
cd ~/ros2neuro_ws
colcon build --packages-select ros2neuro_acquisition_lsl
source install/setup.bash
```

#### Step 2 — run the test launcher

```bash
ros2 launch ros2neuro_acquisition_lsl test_acquisition_lsl.launch.py
```

This starts four processes simultaneously:

1. **`lsl_csv_streamer.py`** — reads `rawdata.csv` and streams it as a 512 Hz LSL Outlet named `TestStream`, pushing 32 samples per tick at 16 Hz to emulate a real device.
2. **`acquisition` node** — loads the `LSLDevice` plugin, discovers `TestStream` by name, and publishes the acquired data on `/acquisition/neurodata` at 16 Hz (32 samples/frame, 31 EEG channels + 1 trigger).
3. **`neuroviz`** — real-time visualizer of the incoming `NeuroFrame` stream.
4. **`topic_saver.py`** — subscribes to `/acquisition/neurodata` and saves every received sample row by row to `acquired_data.csv` in the installed `test/` directory.

Wait until the terminal prints `Finished streaming CSV data via LSL.`, then stop with **CTRL+C**.

#### Step 3 — verify in MATLAB

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
