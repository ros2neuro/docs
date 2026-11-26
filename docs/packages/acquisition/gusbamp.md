# g.USBamp device

!!! info ""
    Package: [`ros2neuro_acquisition_gusbamp`](https://github.com/ros2neuro/ros2neuro_acquisition_gusbamp) · pluginlib class: `ros2neuro::acquisition::GUSBampDevice` · part of [Acquisition](index.md)

The direct backend for g.tec g.USBamp amplifiers, using the g.USBamp API. It configures the amplifier (sample rate, channels, filters, trigger line) from the acquisition parameters and publishes the signal and the trigger line.

| | |
|---|---|
| **Layer** | Acquisition |
| **Kind** | Plugin of [`ros2neuro_acquisition`](index.md) (pluginlib class `ros2neuro::acquisition::GUSBampDevice`) |
| **Reads** | a g.tec g.USBamp amplifier (hardware and proprietary driver required) |
| **Publishes** | `NeuroFrame` and `NeuroFrameInfo` through the acquisition node |
| **Run** | `ros2 run ros2neuro_acquisition_gusbamp acquisition_gusbamp`<br>`ros2 launch ros2neuro_acquisition_gusbamp gusbamp_acquisition.launch.xml` |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_acquisition`](index.md), [`ros2neuro_data`](../msgs-data.md#ros2neuro_data), [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)
- **ROS 2 packages** (run only): `launch`, `launch_ros`
- **External libraries**:
    - g.tec g.USBamp API (`libgusbampapi`): **loaded at run time** with `dlopen`, never linked: the package builds, installs and loads **without** the SDK (and without its headers); opening the amplifier fails with a clear error if the library is missing (the unversioned `libgusbampapi.so` comes with the development package, the runtime package has `libgusbampapi.so.1.14`: both are tried)

## Messages and topics

Default node name: `acquisition`.

| | Default topic | Type | Changed by |
|---|---|---|---|
| publishes | `~/neurodata`, `~/neurodata_info` | `NeuroFrame`, `NeuroFrameInfo` | through the acquisition node (`acquisition.topic_data`, `acquisition.topic_info`) |

Messages used:

- `NeuroFrame`, `NeuroFrameInfo`: published through the acquisition node

## Example configuration

The configuration shipped with the package (`config/gusbamp_configuration.yaml`). `$(var samplerate)` and `$(var framerate)` are launch substitutions: pass the file to a node started by a launch file with `allow_substs="true"`, or replace them with numbers:

```yaml
/acquisition:
    ros__parameters:
        acquisition.plugin: ros2neuro::acquisition::GUSBampDevice
        acquisition.autostart: true
        acquisition.reopen: true
        acquisition.samplerate: $(var samplerate)
        acquisition.framerate: $(var framerate)
        acquisition.device: ""
        acquisition.channels: 16
        acquisition.enable_trigger_line: true
        acquisition.scan_dio: true
        acquisition.slave_mode: false
        acquisition.enable_sc: false
        acquisition.bandpass_filter: -1
        acquisition.notch_filter: -1
        acquisition.bipolar_derivation: -2
        acquisition.sensors.eeg.enable: true
        acquisition.sensors.eeg.name: EEG
        acquisition.sensors.eeg.labels: [Fz, FC3, FC1, FCz, FC2, FC4, C3, C1, Cz, C2, C4, CP3, CP1, CPz, CP2, CP4]
        acquisition.triggers.trigger.enable: true
        acquisition.triggers.trigger.name: TRI
```

<!-- /interfaces -->
Use g.USBamp hardware through this package and plugin:

```text
ros2neuro::acquisition::GUSBampDevice
```

## The SDK is not needed to install

The package declares in `gusbamp_sdk_wrapper.h` only what the plugin uses of the g.USBamp API (the types, the constants and 11 functions) and loads `libgusbampapi` when the amplifier is opened. Without the library the plugin is there and opening the amplifier fails with:

```text
Cannot open the gUSBamp amplifier: the g.USBamp SDK (libgusbampapi.so) was not found: install the g.tec driver (libgusbampapi) to use this amplifier
```

When the SDK header `gAPI.h` is installed at build time, the test `test_sdk_layout` compares every size, offset and constant of the wrapper with it, so a wrong layout is found when the package is built and not as a misconfigured amplifier. `test_gusbamp_without_sdk` checks that the plugin is configured and cannot be opened when the library does not exist.

## Verified on a real amplifier

Tried on 2026-11-26 in a clean Docker container (Ubuntu 24.04, ROS 2 Jazzy, `ros-jazzy-ros2neuro-full` and this package installed from the `.deb`, no library of the host visible):

* **without the SDK**: the plugin loads and opening the amplifier fails with `Cannot open the gUSBamp amplifier: the g.USBamp SDK (libgusbampapi.so) was not found: install the g.tec driver (libgusbampapi) to use this amplifier` (the node tries again because `acquisition.reopen` is true);
* **with the SDK** (`libgusbampapi1` 1.24 installed in the image) and a g.USBamp plugged in: `Opened device 'gusbamp'`, `Configured gUSBamp device id='UB-2011.07.23' samplerate=512 Hz frame_rate=16.000000 Hz samples_per_frame=32 channels=16 trigger=true`, `Started device 'gusbamp'`. The same works from the development container (Distrobox).

Not checked: the signal on screen (the visualizer window closed by itself in that run) and the frame rate with `ros2 topic hz`, and the SDK 1.14 (the 1.24 is the one the layout test of `gusbamp_sdk_wrapper.h` was run against). To use the amplifier from Docker pass the device (`--device /dev/bus/usb`, with the amplifier plugged in **before** the container starts).

## Executable

```bash
ros2 run ros2neuro_acquisition_gusbamp acquisition_gusbamp
```

The package also installs a convenience launch file that uses the generic
[`ros2neuro_acquisition`](index.md) runtime:

```bash
ros2 launch ros2neuro_acquisition_gusbamp gusbamp_acquisition.launch.xml
```

## Parameters

All parameters are expected under the acquisition node device prefix. With the
current plugin runtime that prefix is `acquisition`.

- `acquisition.name` (default `gusbamp`)
- `acquisition.samplerate` (default `512`)
- `acquisition.framerate` (default `16.0`; samples per frame = `round(samplerate / framerate)`)
- `acquisition.device` (name of the amplifier as listed by the g.USBamp API; empty = the first one found)
- `acquisition.sdk_library` (the library to load with `dlopen`; empty = the usual names of `libgusbampapi`)
- `acquisition.channels` (1..16, default 16)
- `acquisition.number_of_scans` (default: the API autoset value)
- `acquisition.enable_trigger_line`
- `acquisition.scan_dio`
- `acquisition.slave_mode`
- `acquisition.enable_sc`
- `acquisition.bandpass_filter`
- `acquisition.notch_filter`
- `acquisition.bipolar_derivation`
- `acquisition.sensors.eeg.enable`
- `acquisition.sensors.eeg.name`
- `acquisition.sensors.eeg.labels`
- `acquisition.triggers.trigger.enable`
- `acquisition.triggers.trigger.name`
- `acquisition.triggers.trigger.labels`

The EEG labels are cut or padded (`ch<N>`) to `acquisition.channels`. The trigger block is published only when both
`acquisition.triggers.trigger.enable` and `acquisition.scan_dio` are true.
