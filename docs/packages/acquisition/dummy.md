# Dummy device

!!! info ""
    Package: [`ros2neuro_acquisition_dummy`](https://github.com/ros2neuro/ros2neuro_acquisition_dummy) · pluginlib class: `ros2neuro::acquisition::DummyDevice` · part of [Acquisition](index.md)

`ros2neuro_acquisition_dummy` is a reference acquisition plugin for the ROS2neuro stack.
It implements the `ros2neuro::acquisition::NeuroDevice` interface with a synthetic device
that generates deterministic EEG-, EMG-, and trigger-like data.

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

The plugin reads its parameters from the acquisition node using the configured prefix,
which defaults to `device`.

Supported parameters:

- `device.name`
- `device.id`
- `device.model`
- `device.samplerate`
- `device.framerate`

Default values:

- `device.name = dummy_device`
- `device.id = dummy0`
- `device.model = dummy`
- `device.samplerate = 512`
- `device.framerate = 16.0`

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

It starts the generic `acquisition` executable from `ros2neuro_acquisition` and configures it
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

## Dependencies

Current direct dependencies:

- `ament_cmake`
- `rclcpp`
- `pluginlib`
- `ros2neuro_acquisition`
- `ros2neuro_data`
- `ros2neuro_msgs`
- `launch`
- `launch_ros`

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
