# Acquisition

!!! info ""
    Package: [`ros2neuro_acquisition`](https://github.com/ros2neuro/ros2neuro_acquisition)

The acquisition package is the entry point of the signal chain. It provides the generic `acquisition` node, the
`NeuroDevice` plugin interface and the state machine that turns a device into ROS 2 topics and services. It knows
nothing about a specific amplifier: the device driver is a **plugin that you must select**.

!!! important "Select one plugin"
    The node does nothing useful until the parameter `acquisition.plugin` names one of the plugins below.

## Available plugins

| Plugin | pluginlib class | Use it to |
|---|---|---|
| [Dummy](dummy.md) | [`ros2neuro::acquisition::DummyDevice`](dummy.md) | generate synthetic EEG/EMG/trigger data, no hardware |
| [XDF / GDF replay](xdf.md) | [`ros2neuro::acquisition::XDFDevice`](xdf.md) | replay a recorded file as if it were live |
| [LSL](lsl.md) | [`ros2neuro::acquisition::LSLDevice`](lsl.md) | read a Lab Streaming Layer stream |
| [eegdev](eegdev.md) | [`ros2neuro::acquisition::EGDDevice`](eegdev.md) | read a device supported by the eegdev library |
| [ANT Neuro](antneuro.md) | [`ros2neuro::acquisition::EEGODevice`](antneuro.md) | ANT Neuro amplifiers (hardware required) |
| [g.USBamp](gusbamp.md) | [`ros2neuro::acquisition::GUSBampDevice`](gusbamp.md) | g.tec g.USBamp (hardware required) |

## Topics and services

| | Name | Type |
|---|---|---|
| publishes | `~/neurodata` | `NeuroFrame` |
| publishes | `~/neurodata_info` | `NeuroFrameInfo` (`transient_local`) |
| service | `~/start`, `~/stop`, `~/quit` | `std_srvs/Empty` |

With the node named `acquisition` these are `/acquisition/neurodata`, `/acquisition/neurodata_info` and
`/acquisition/start|stop|quit`.

## Minimal example

Replay a GDF file at 16 frames per second, looping:

```yaml
/acquisition:
  ros__parameters:
    acquisition.plugin: ros2neuro::acquisition::XDFDevice
    acquisition.autostart: true
    acquisition.filename: "/path/to/recording.gdf"
    acquisition.framerate: 16.0
    acquisition.loop: true
```

```bash
ros2 run ros2neuro_acquisition acquisition --ros-args --params-file acquisition.yaml
```

Or, with no file and no hardware:

```bash
ros2 launch ros2neuro_acquisition_dummy dummy_acquisition.launch.py
```

## Writing a new backend

Derive from `ros2neuro::acquisition::NeuroDevice`, register the class with `PLUGINLIB_EXPORT_CLASS` and export it
with `pluginlib_export_plugin_description_file(ros2neuro_acquisition plugins.xml)`. The
[dummy plugin](dummy.md) is the reference implementation, and [Plugins](../../concepts/plugins.md) explains the
mechanism.

---

## Reference (from the package README)

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `rclcpp`, `std_srvs`, `pluginlib`, [`ros2neuro_data`](../msgs-data.md#ros2neuro_data), [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)
- **ROS 2 packages** (run only): [`ros2neuro_visualizer`](../visualizer.md)
- **At run time**: one acquisition plugin package (`ros2neuro_acquisition_*`); [`ros2neuro_visualizer`](../visualizer.md) is an optional run-time dependency of the launch file

## Messages and topics

Default node name: `acquisition`.

| | Default topic | Type | Changed by |
|---|---|---|---|
| publishes | `~/neurodata` | `NeuroFrame` | `acquisition.topic_data` |
| publishes | `~/neurodata_info` | `NeuroFrameInfo` (`transient_local`) | `acquisition.topic_info` |

| | Service | Type | Note |
|---|---|---|---|
| provides | `~/start`, `~/stop`, `~/quit` | `std_srvs/Empty` | control the device |

Messages used:

- `NeuroFrame`: published, one chunk of samples
- `NeuroFrameInfo`: published, the description of the stream
- `std_srvs/Empty`: the start, stop and quit services

## Example configuration

The acquisition node reads its parameters from a YAML file. The plugin and the parameters of the device share the prefix `acquisition.`:

```yaml
/acquisition:
  ros__parameters:
    acquisition.plugin: ros2neuro::acquisition::XDFDevice   # the backend to load (required)
    acquisition.autostart: true                              # start streaming right after the setup
    acquisition.reopen: true                                 # reopen the device after a read or setup failure
    acquisition.framerate: 16.0                              # NeuroFrame messages per second
    acquisition.topic_data: ~/neurodata                      # optional, these are the defaults
    acquisition.topic_info: ~/neurodata_info
    # the parameters of the plugin follow, under the same prefix, for example:
    acquisition.filename: /path/to/recording.gdf
```

```bash
ros2 run ros2neuro_acquisition acquisition --ros-args --params-file acquisition.yaml
```

<!-- /interfaces -->
The package is meant to sit between:

- concrete hardware drivers or acquisition plugins
- the [`ros2neuro_data`](../msgs-data.md#ros2neuro_data) runtime data structures
- the [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs) transport interfaces published on the ROS graph

## Purpose

The package defines a common execution model for acquisition devices.

Typical flow:

1. a plugin implementing `NeuroDevice` is selected through parameters
2. the node loads the plugin through `pluginlib`
3. the plugin is configured and opened
4. frame metadata are built once and published on `~/neurodata_info`
5. runtime data frames are acquired and published on `~/neurodata`

This keeps hardware-specific code isolated inside plugins while the ROS-facing
logic remains reusable across devices.

## Main components

The package currently provides:

- `ros2neuro::acquisition::NeuroDevice`
- `ros2neuro::acquisition::NeuroAcquisitionNode`
- the executable `acquisition`

### `NeuroDevice`

`NeuroDevice` is the abstract plugin interface implemented by each acquisition backend.

It defines the following responsibilities:

- configure device-specific parameters from a ROS node
- open and close the device
- setup and start the acquisition stream
- stop the stream
- build static frame metadata
- read one runtime `NeuroFrame`

### `NeuroAcquisitionNode`

`NeuroAcquisitionNode` is the generic ROS 2 node that owns the acquisition state machine.

It is responsible for:

- loading a plugin by class name
- publishing `ros2neuro_msgs::msg::NeuroFrame`
- publishing `ros2neuro_msgs::msg::NeuroFrameInfo`
- exposing runtime control services

## Runtime model

The node uses a simple internal state machine:

- `Idle`
- `Open`
- `Setup`
- `Ready`
- `Start`
- `Running`
- `Stop`
- `Close`
- `Quit`

The plugin provides the device-specific behavior for the transitions, while the node
handles ROS publishers, timers, and services.

## Topics and services

Default topics:

- `~/neurodata`
- `~/neurodata_info`

Default services:

- `~/start`
- `~/stop`
- `~/quit`

With the default node name `acquisition`, these resolve to:

- `/acquisition/neurodata`
- `/acquisition/neurodata_info`
- `/acquisition/start`
- `/acquisition/stop`
- `/acquisition/quit`

## Parameters

Core node parameters:

- `acquisition.plugin`: pluginlib class name of the acquisition backend
- `acquisition.topic_data`: runtime frame topic, defaults to `~/neurodata`
- `acquisition.topic_info`: metadata topic, defaults to `~/neurodata_info`
- `acquisition.prefix`: prefix of the plugin parameters, used **only** when no plugin class is set (the default is `device`); whenever `acquisition.plugin` / `plugin` is set the prefix is `acquisition`
- `acquisition.autostart`: start streaming automatically after setup
- `acquisition.reopen`: reopen the device after read/setup failures
- `acquisition.framerate`: fallback frame rate if the plugin does not provide one

Legacy names such as `plugin`, `topic_data`, `topic_info`, `device_prefix`,
`autostart`, `reopen`, and `framerate` are still accepted as
fallback parameters.

Plugin-specific parameters are delegated to the selected `NeuroDevice` implementation
under the configured prefix, for example:

- `acquisition.samplerate`
- `acquisition.framerate`
- `acquisition.device`
- `acquisition.sensors.eeg.labels`

## Build

Inside a ROS 2 workspace:

```bash
colcon build --packages-select ros2neuro_acquisition
```

To source the workspace after build:

```bash
source install/setup.bash
```

## Tests

The package includes unit tests for basic node behavior, including:

- configuration failure when `plugin` is empty
- configuration failure when the requested plugin does not exist

Run them with:

```bash
colcon test --packages-select ros2neuro_acquisition
```

## Minimal usage

Run the generic acquisition executable with parameters selecting a plugin:

```bash
ros2 run ros2neuro_acquisition acquisition --ros-args \
  -p acquisition.plugin:=ros2neuro::acquisition::DummyDevice \
  -p acquisition.samplerate:=512 \
  -p acquisition.framerate:=16.0
```

The concrete plugin must be provided by another package, such as
[`ros2neuro_acquisition_dummy`](dummy.md).

The same generic runtime is available through:

```bash
ros2 launch ros2neuro_acquisition acquisition.launch.xml \
  config_file:=/path/to/acquisition_configuration.yaml
```

## Notes

- This package defines the acquisition framework, not a concrete device.
- The actual hardware or simulated backends are expected to live in separate plugin packages.
- Plugins exchange runtime data using [`ros2neuro_data`](../msgs-data.md#ros2neuro_data) and publish transport messages through [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs).
