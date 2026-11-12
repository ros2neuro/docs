# eegdev device

!!! info ""
    Package: [`ros2neuro_acquisition_eegdev`](https://github.com/ros2neuro/ros2neuro_acquisition_eegdev) · pluginlib class: `ros2neuro::acquisition::EGDDevice` · part of [Acquisition](index.md)

An acquisition backend for the devices and files supported by the `libeegdev` library: it can open a live eegdev driver or a `.gdf` / `.bdf` file and maps the eegdev channel groups to ROS2neuro sensors and triggers. ANT Neuro eego amplifiers have their own package, [`ros2neuro_acquisition_antneuro`](antneuro.md).

| | |
|---|---|
| **Layer** | Acquisition |
| **Kind** | Plugin of [`ros2neuro_acquisition`](index.md) (pluginlib class `ros2neuro::acquisition::EGDDevice`) |
| **Reads** | a `libeegdev` device or a GDF/BDF file |
| **Publishes** | `NeuroFrame` and `NeuroFrameInfo` through the acquisition node |
| **Run** | `ros2 run ros2neuro_acquisition_eegdev acquisition_eegdev`<br>`ros2 launch ros2neuro_acquisition_eegdev eegdev_file_acquisition.launch.py` |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `rclcpp`, `pluginlib`, [`ros2neuro_acquisition`](index.md), [`ros2neuro_data`](../msgs-data.md#ros2neuro_data), [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)
- **ROS 2 packages** (run only): `launch`, `launch_ros`
- **External libraries**:
    - `libeegdev`: devices and GDF/BDF files
    - `xdffileio`: file support

## Messages and topics

Default node name: `acquisition`.

| | Default topic | Type | Changed by |
|---|---|---|---|
| publishes | `~/neurodata`, `~/neurodata_info` | `NeuroFrame`, `NeuroFrameInfo` | through the acquisition node (`acquisition.topic_data`, `acquisition.topic_info`) |

Messages used:

- `NeuroFrame`, `NeuroFrameInfo`: published through the acquisition node

<!-- /interfaces -->
Its role is to adapt devices and files supported by `libeegdev` to the common
[`ros2neuro::acquisition::NeuroDevice`](index.md) interface, so they can be loaded by the
generic acquisition node and published as `NeuroFrame` / `NeuroFrameInfo`.

## Purpose

The package provides a concrete acquisition backend for EEG/EXG systems exposed
through `libeegdev`.

In practice, it:

1. reads device-specific parameters from the acquisition node
2. opens either a live `libeegdev` driver or a `.gdf` / `.bdf` file
3. queries device identity and channel layout
4. maps eegdev groups into [`ros2neuro_data`](../msgs-data.md#ros2neuro_data) sensors and triggers
5. streams synchronized runtime frames through [`ros2neuro_acquisition`](index.md)

## Main components

The package currently provides:

- `ros2neuro::acquisition::EGDDevice`
- `ros2neuro::acquisition::EGDOpenOptions`
- `plugins.xml` for `pluginlib` registration
- `eegdev_file_acquisition.launch.py` for file-based acquisition

## Plugin class

Use the plugin with:

```yaml
acquisition.plugin: "ros2neuro::acquisition::EGDDevice"
```

## Parameters

All parameters are expected under the prefix `acquisition.`, which the acquisition node uses whenever a plugin class is set.

Supported parameters:

- `acquisition.device`
- `acquisition.open_options`
- `acquisition.samplerate`
- `acquisition.framerate`
- `acquisition.sensors.eeg.enable`
- `acquisition.sensors.eeg.name`
- `acquisition.sensors.eeg.labels`
- `acquisition.sensors.exg.enable`
- `acquisition.sensors.exg.name`
- `acquisition.sensors.exg.labels`
- `acquisition.triggers.trigger.enable`
- `acquisition.triggers.trigger.name`
- `acquisition.triggers.trigger.labels`

Example:

```yaml
/acquisition:
  ros__parameters:
    acquisition.plugin: "ros2neuro::acquisition::EGDDevice"
    acquisition.device: "gtec"                    # driver name, or the path of a .gdf / .bdf file (default "eegdev")
    acquisition.open_options: "gtec|deviceid|any" # optional full eegdev open string (default "")
    acquisition.samplerate: 512                   # default 0
    acquisition.framerate: 16.0                   # default 16.0
    acquisition.sensors.eeg.enable: true          # default true
    acquisition.sensors.eeg.name: "EEG"
    acquisition.sensors.exg.enable: true          # default true
    acquisition.sensors.exg.name: "EXG"
    acquisition.triggers.trigger.enable: true     # default true
    acquisition.triggers.trigger.name: "TRI"
```

Behavior notes:

- `samplerate = 0` means "accept the device default"; a non-zero value must match the rate the device reports,
  otherwise `setup()` fails (it is passed to the driver only for `gtec`)
- `framerate` is the requested publication rate
- `samples_per_frame` is derived internally as `round(samplerate / framerate)`
- `labels`, when set, must have exactly as many entries as the channels of the block (otherwise `setup()` fails);
  when empty, the labels reported by eegdev are used, or `eeg:1`, `eeg:2`, ... (the lower-case block name) if eegdev
  reports none

## libeegdev backend options

The plugin passes `acquisition.open_options` through to `libeegdev`, so the actual
accepted options depend on the selected backend.

Based on the locally installed `libeegdev` man pages, the following backends
and options are available:

### `datafile`

Use this backend to replay biosignal files supported by `xdffileio`.

Supported options:

- `path`

Example:

```text
datafile|path|/home/user/data.gdf
```

### `biosemi`

Backend for Biosemi ActiveTwo hardware.

Supported options:

- `numch`

Accepted values documented by `libeegdev`:

- `32`
- `64`
- `128`
- `256`

Example:

```text
biosemi|numch|32
```

### `gtec`

Backend for gTec gUSBamp hardware.

Supported options:

- `samplerate`
- `lowpass`
- `highpass`
- `notch`
- `deviceid`
- `commongndref`

Example:

```text
gtec|notch|60|lowpass|none|highpass|none|deviceid|any+any
```

### ANT Neuro eego

Use ANT Neuro eego hardware through the dedicated
[`ros2neuro_acquisition_antneuro`](antneuro.md) package and plugin
[`ros2neuro::acquisition::EEGODevice`](antneuro.md). This `eegdev` plugin intentionally keeps
no eego-specific setup path.

### `barv`

Backend for BrainAmp Recorder / RecView RDA servers.

Supported options:

- `host`
- `port`

The documented default `port` values distinguish different stream formats:

- `51234`
- `51244`
- `51254`

### `tobiia`

Backend for Tobi Interface A.

Supported options:

- `host`
- `port`

### `neurone`

A `neurone` backend is installed in the local `libeegdev` plugin directory,
but no corresponding local man page was found during this pass, so its accepted
options are not documented here yet.

## Open-string handling

The plugin takes a driver/file name (`acquisition.device`) and an optional full eegdev open string
(`acquisition.open_options`, `name|key1|value1|key2|value2|...`: an odd number of tokens, otherwise `configure()`
fails). When `open_options` has a name, it replaces `acquisition.device`.

Example:

```yaml
acquisition.device: "gtec"
acquisition.open_options: "gtec|deviceid|any"
acquisition.samplerate: 512
```

This becomes an eegdev open string like (options are written in alphabetical order):

```text
gtec|deviceid|any|samplerate|512
```

For `.gdf` and `.bdf` paths, it switches to the `datafile|path|...` backend (the file must exist; any other
extension is rejected).

## Launch file

The package installs a ready-to-use launch file for replaying biosignal files
through the generic acquisition node:

- `eegdev_file_acquisition.launch.py`

Run it with:

```bash
ros2 launch ros2neuro_acquisition_eegdev eegdev_file_acquisition.launch.py \
  file_path:=/path/to/data.gdf
```

It accepts the launch arguments:

- `file_path` (required)
- `framerate` (default `16.0`)
- `samplerate` (default `0`)
- `eeg_name`, `exg_name`, `trigger_name` (defaults `EEG`, `EXG`, `TRI`)
- `enable_exg`, `enable_trigger` (default `true`)
- `acquisition.autostart` (default `true`), `acquisition.reopen` (default `false`)

With the default acquisition node configuration, data are published on:

- `/acquisition/neurodata`
- `/acquisition/neurodata_info`

## Data mapping

The plugin currently maps:

- `EGD_EEG` to a `NeuroSensor` block with type `TYPE_EEG`
- `EGD_SENSOR` to a `NeuroSensor` block with type `TYPE_MISC`
- `EGD_TRIGGER` to a `NeuroTrigger` block

The exact presence of these blocks depends on the device capabilities and on:

- `acquisition.sensors.eeg.enable`
- `acquisition.sensors.exg.enable`
- `acquisition.triggers.trigger.enable`

## Build

Inside a ROS 2 workspace:

```bash
colcon build --packages-select ros2neuro_acquisition_eegdev
```

The package requires `libeegdev` development files to be installed.

## Tests

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
lives in the [`ros2neuro_recorder_xdf`](../recorder/xdf.md) package, because it exercises recorder
behavior in addition to acquisition.

The `.gdf` integration tests use a short temporary path under `/tmp` before
opening the file, because some `libeegdev` setups are sensitive to long file paths.

## Notes

- `libeegdev` can expose richer metadata than the current [`ros2neuro_data`](../msgs-data.md#ros2neuro_data)
  containers store.
- Units, labels and min/max ranges are queried from eegdev and reach `NeuroFrameInfo`;
  transducer details and hardware filters are not queried, and `NeuroFrameInfo` carries them empty.
- If you want those fields to reach `NeuroFrameInfo`, the next clean step is
  extending [`ros2neuro_data`](../msgs-data.md#ros2neuro_data) to carry them explicitly.
