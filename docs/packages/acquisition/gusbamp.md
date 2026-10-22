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
    - g.tec g.USBamp API (`gusbampapi`): found at build time: the package does **not** build without it (on Ubuntu `libgusbampapi1` and `libgusbampapi-dev`)
    - Boost: `thread`, `system`, `regex`, `date_time`

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

- `acquisition.samplerate`
- `acquisition.framerate`
- `acquisition.device`
- `acquisition.channels`
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
