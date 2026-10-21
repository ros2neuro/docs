# eegdev device

!!! info ""
    Package: [`ros2neuro_acquisition_eegdev`](https://github.com/ros2neuro/ros2neuro_acquisition_eegdev) · pluginlib class: `ros2neuro::acquisition::EGDDevice` · part of [Acquisition](index.md)

`ros2neuro_acquisition_eegdev` is a `libeegdev`-based plugin for the
[`ros2neuro_acquisition`](index.md) framework.

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
plugin: "ros2neuro::acquisition::EGDDevice"
```

## Parameters

All parameters are expected under the acquisition node device prefix.
With the default acquisition configuration, that prefix is `device`.

Supported parameters:

- `device.device`
- `device.open_options`
- `device.samplerate`
- `device.framerate`
- `device.sensors.eeg.enable`
- `device.sensors.eeg.name`
- `device.sensors.eeg.labels`
- `device.sensors.exg.enable`
- `device.sensors.exg.name`
- `device.sensors.exg.labels`
- `device.triggers.trigger.enable`
- `device.triggers.trigger.name`
- `device.triggers.trigger.labels`

Example:

```yaml
device:
  device: "gtec"
  open_options: "serial|UA-1234"
  samplerate: 512
  framerate: 16.0
  sensors.eeg.enable: true
  sensors.eeg.name: "EEG"
  sensors.eeg.labels: []
  sensors.exg.enable: true
  sensors.exg.name: "EXG"
  sensors.exg.labels: []
  triggers.trigger.enable: true
  triggers.trigger.name: "TRI"
  triggers.trigger.labels: []
```

Behavior notes:

- `samplerate = 0` means "accept the device default"
- `framerate` is the requested publication rate
- `samples_per_frame` is derived internally from `samplerate / framerate`

## libeegdev backend options

The plugin passes `device.open_options` through to `libeegdev`, so the actual
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

The plugin accepts a driver/file name plus an optional eegdev option tail.

Example:

```yaml
device:
  name: "gtec"
  open_options: "port|usb0|serial|UA-1234"
```

This becomes an eegdev open string like:

```text
gtec|port|usb0|serial|UA-1234|samplerate|512
```

For `.gdf` and `.bdf` paths, it switches to the `datafile|path|...` backend.

## Launch file

The package installs a ready-to-use launch file for replaying biosignal files
through the generic acquisition node:

- `eegdev_file_acquisition.launch.py`

Run it with:

```bash
ros2 launch ros2neuro_acquisition_eegdev eegdev_file_acquisition.launch.py \
  file_path:=/path/to/data.gdf
```

It accepts launch arguments such as:

- `file_path`
- `framerate`
- `samplerate`
- `enable_exg`
- `enable_trigger`

With the default acquisition node configuration, data are published on:

- `/acquisition/neurodata`
- `/acquisition/neurodata_info`

## Data mapping

The plugin currently maps:

- `EGD_EEG` to a `NeuroSensor` block with type `TYPE_EEG`
- `EGD_SENSOR` to a `NeuroSensor` block with type `TYPE_MISC`
- `EGD_TRIGGER` to a `NeuroTrigger` block

The exact presence of these blocks depends on the device capabilities and on:

- `device.sensors.eeg.enable`
- `device.sensors.exg.enable`
- `device.triggers.trigger.enable`

## Dependencies

Current direct dependencies:

- `ament_cmake`
- `rclcpp`
- `pluginlib`
- [`ros2neuro_acquisition`](index.md)
- [`ros2neuro_data`](../msgs-data.md#ros2neuro_data)
- [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)
- `libeegdev`

## Build

Inside a ROS 2 workspace:

```bash
colcon build --packages-select ros2neuro_acquisition_eegdev
```

The package requires `libeegdev` development files to be installed.

## Tests

The package currently includes:

- unit tests for `EGDOpenOptions`
- a file-based integration test using `test/test_short.gdf`

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
- Transducer details, hardware filters, and min/max ranges are queried internally
  where possible, but are not yet fully persisted in the published metadata model.
- If you want those fields to reach `NeuroFrameInfo`, the next clean step is
  extending [`ros2neuro_data`](../msgs-data.md#ros2neuro_data) to carry them explicitly.
