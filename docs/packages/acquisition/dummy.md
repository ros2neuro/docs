# Dummy device

!!! info ""
    Package: [`ros2neuro_acquisition_dummy`](https://github.com/ros2neuro/ros2neuro_acquisition_dummy) · pluginlib class: `ros2neuro::acquisition::DummyDevice` · part of [Acquisition](index.md)

A synthetic acquisition device that needs no hardware: it generates sinusoidal EEG and EMG blocks and a periodic trigger at a configurable sample rate and frame rate. It is meant for tests and bring-up, and as the reference implementation of an acquisition plugin.

| | |
|---|---|
| **Layer** | Acquisition |
| **Kind** | Plugin of [`ros2neuro_acquisition`](index.md) (pluginlib class `ros2neuro::acquisition::DummyDevice`) |
| **Reads** | nothing (generated data: 16 EEG channels, 8 EMG channels, 1 trigger channel by default) |
| **Publishes** | `NeuroFrame` and `NeuroFrameInfo` through the acquisition node |
| **Run** | `ros2 launch ros2neuro_acquisition_dummy dummy_acquisition.launch.py` |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `rclcpp`, `pluginlib`, [`ros2neuro_acquisition`](index.md), [`ros2neuro_data`](../msgs-data.md#ros2neuro_data), [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)
- **ROS 2 packages** (run only): `launch`, `launch_ros`

## Messages and topics

Default node name: `acquisition` (the node of [`ros2neuro_acquisition`](index.md)).

| | Default topic | Type | Changed by |
|---|---|---|---|
| publishes | `~/neurodata`, `~/neurodata_info` | `NeuroFrame`, `NeuroFrameInfo` | through the acquisition node (`acquisition.topic_data`, `acquisition.topic_info`) |

Messages used:

- `NeuroFrame`, `NeuroFrameInfo`: published through the acquisition node

## Example configuration

The plugin reads its parameters under the prefix `acquisition.` (the prefix of the acquisition node when a plugin is set); all of them are optional:

```yaml
/acquisition:
  ros__parameters:
    acquisition.plugin: ros2neuro::acquisition::DummyDevice
    acquisition.autostart: true
    acquisition.name: dummy_device
    acquisition.id: dummy0
    acquisition.model: dummy
    acquisition.samplerate: 512      # Hz
    acquisition.framerate: 16.0      # frames per second: 32 samples per frame at 512 Hz
```

<!-- /interfaces -->
The package is intended for:

- testing the generic acquisition node without hardware
- validating topic and service behavior
- providing a simple example of how to implement a new acquisition plugin

## Purpose

The dummy plugin acts like a small self-contained virtual device.

It:

- exposes configurable acquisition parameters
- publishes one frame info description
- generates runtime sample blocks at a configurable sampling rate and frame rate
- emits simple digital trigger events at predictable frame intervals

This makes it useful both for automated tests and for manual bring-up of the acquisition stack.

## Main components

The package currently provides:

- `ros2neuro::acquisition::DummyDevice`
- `plugins.xml` for `pluginlib` registration
- `dummy_acquisition.launch.py` for quick startup

## Generated data model

Each acquired frame contains:

- one EEG sensor block named `EEG`
- one EMG sensor block named `EMG`
- one trigger block named `TRIGGER`

Default signal layout:

- EEG: 16 channels
- EMG: 8 channels
- trigger: 1 channel

The plugin generates sinusoidal sensor data and periodic trigger markers so that
downstream consumers can be exercised with realistic-looking synchronized frames.

## Parameters

The plugin reads its parameters from the acquisition node under the prefix `acquisition.` (the prefix the node uses
whenever `acquisition.plugin` is set; a `acquisition.*` prefix is ignored in that case).

Supported parameters:

- `acquisition.name`
- `acquisition.id`
- `acquisition.model`
- `acquisition.samplerate`
- `acquisition.framerate`

Default values:

- `acquisition.name = dummy_device`
- `acquisition.id = dummy0`
- `acquisition.model = dummy`
- `acquisition.samplerate = 512`
- `acquisition.framerate = 16.0`

The number of samples per frame is derived internally as:

```text
samples_per_frame = round(samplerate / framerate)
```

The actual published frame rate is then recomputed from:

```text
actual_framerate = samplerate / samples_per_frame
```

## Launch file

The package installs a ready-to-use launch file:

- `dummy_acquisition.launch.py`

It starts the generic `acquisition` executable from [`ros2neuro_acquisition`](index.md) and configures it
to load the dummy plugin.

Run it with:

```bash
ros2 launch ros2neuro_acquisition_dummy dummy_acquisition.launch.py
```

With the default configuration, the node publishes:

- `/acquisition/neurodata`
- `/acquisition/neurodata_info`

and exposes:

- `/acquisition/start`
- `/acquisition/stop`
- `/acquisition/quit`

## Build

Inside a ROS 2 workspace:

```bash
colcon build --packages-select ros2neuro_acquisition_dummy
```

To source the workspace after build:

```bash
source install/setup.bash
```

## Tests

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

## Notes

- This package is not meant to model a specific real device.
- Its main role is to provide a stable plugin example and a hardware-free acquisition target.
- New acquisition backends can use `DummyDevice` as a small reference implementation.
