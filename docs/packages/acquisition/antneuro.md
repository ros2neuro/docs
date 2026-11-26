# ANT Neuro device

!!! info ""
    Package: [`ros2neuro_acquisition_antneuro`](https://github.com/ros2neuro/ros2neuro_acquisition_antneuro) · pluginlib class: `ros2neuro::acquisition::EEGODevice` · part of [Acquisition](index.md)

The dedicated backend for ANT Neuro eego amplifiers, using the eego SDK directly. Use it, and not [`ros2neuro_acquisition_eegdev`](eegdev.md), for eego hardware.

| | |
|---|---|
| **Layer** | Acquisition |
| **Kind** | Plugin of [`ros2neuro_acquisition`](index.md) (pluginlib class `ros2neuro::acquisition::EEGODevice`) |
| **Reads** | an ANT Neuro eego amplifier (hardware and SDK required) |
| **Publishes** | `NeuroFrame` and `NeuroFrameInfo` through the acquisition node |
| **Run** | `ros2 run ros2neuro_acquisition_antneuro acquisition_antneuro`<br>`ros2 launch ros2neuro_acquisition_antneuro eego_acquisition.launch.xml` |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_acquisition`](index.md), [`ros2neuro_data`](../msgs-data.md#ros2neuro_data), [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)
- **External libraries**:
    - ANT Neuro eego SDK (`libeego-SDK.so`): **loaded at run time** with `dlopen`: the package builds without it, but opening the device fails if the library is missing

## Messages and topics

Default node name: `acquisition`.

| | Default topic | Type | Changed by |
|---|---|---|---|
| publishes | `~/neurodata`, `~/neurodata_info` | `NeuroFrame`, `NeuroFrameInfo` | through the acquisition node (`acquisition.topic_data`, `acquisition.topic_info`) |

Messages used:

- `NeuroFrame`, `NeuroFrameInfo`: published through the acquisition node

<!-- /interfaces -->
Use eego hardware through this package and plugin:

```text
ros2neuro::acquisition::EEGODevice
```

Do not route eego through [`ros2neuro_acquisition_eegdev`](eegdev.md): the eegdev package is
kept generic and no longer contains eego-specific SDK setup.

## Executable

```bash
ros2 run ros2neuro_acquisition_antneuro acquisition_antneuro
```

The package also installs a convenience launch file that uses the generic
[`ros2neuro_acquisition`](index.md) runtime:

```bash
ros2 launch ros2neuro_acquisition_antneuro eego_acquisition.launch.xml
```

Launch arguments: `samplerate` (default `512`), `framerate` (default `16.0`), `config` (default: the installed
`config/eego_configuration.yaml`, read with `allow_substs`), `visualizer` (default `false`: start `neuroviz`).

## Verified on a real amplifier

Tried on 2026-11-26 in a clean Docker container (Ubuntu 24.04, ROS 2 Jazzy, the package installed from the `.deb`, no library of the host visible):

* **without the SDK**: the plugin loads and opening fails with `Cannot load eego SDK: libeego-SDK.so: cannot open shared object file` (the node tries again because `acquisition.reopen` is true);
* **with the SDK** (`libeego-sdk` 1.3.19 installed in the image) and an eego plugged in: the SDK is initialized, the amplifier is opened and the visualizer shows the signal of all the **64 EEG channels** of the cap `200` (every label of the cap listed in the configuration).

To use the amplifier from Docker pass the device (`--device /dev/bus/usb`, with the amplifier plugged in **before** the container starts) and, to change the channels, a configuration file of yours with `config:=` (mounted in the container).

## Parameters

Device parameters are read under the prefix passed by the acquisition runtime.
The installed `eego_acquisition.launch.xml` uses the generic
[`ros2neuro_acquisition`](index.md) executable with the `acquisition` prefix, so the bundled
configuration file uses `acquisition.*` parameter names. If the plugin is loaded
with a different prefix, use the same keys under that prefix.

- `acquisition.samplerate`
- `acquisition.framerate`
- `acquisition.cap`
- `acquisition.eeg_mask`
- `acquisition.bip_mask`
- `acquisition.max_buffered_samples`
- `acquisition.sensors.eeg.enable`
- `acquisition.sensors.eeg.name`
- `acquisition.sensors.eeg.labels`
- `acquisition.sensors.exg.enable`
- `acquisition.sensors.exg.name`
- `acquisition.sensors.exg.labels`
- `acquisition.triggers.trigger.enable`
- `acquisition.triggers.trigger.name`
- `acquisition.triggers.trigger.labels`

Defaults: `samplerate` 512 (must be one of the rates the amplifier supports), `framerate` 16.0, `cap` `"200"` (the
other supported cap is `"209"`; any other value is treated as `"200"`), `eeg_mask` and `bip_mask` empty,
`max_buffered_samples` 4096, EEG and trigger blocks enabled, **EXG block disabled**, block names `EEG`, `EXG`, `TRI`.

Example:

```yaml
/acquisition:
  ros__parameters:
    acquisition.plugin: ros2neuro::acquisition::EEGODevice
    acquisition.autostart: true
    acquisition.reopen: true
    acquisition.samplerate: 512
    acquisition.framerate: 16.0
    acquisition.cap: "200"
    acquisition.sensors.eeg.enable: true
    acquisition.sensors.eeg.name: EEG
    acquisition.sensors.eeg.labels: [Fz, FC3, FC1, FCz]
    acquisition.sensors.exg.enable: true
    acquisition.sensors.exg.name: EXG
    acquisition.sensors.exg.labels: [EXG1, EXG2]
    acquisition.triggers.trigger.enable: true
    acquisition.triggers.trigger.name: TRI
```

## EEG Selection

EEG channels can be selected by labels or by SDK mask.

When `acquisition.sensors.eeg.labels` is not empty, the driver builds
`acquisition.eeg_mask` automatically from the configured cap labels and publishes
the EEG channels in the same order as the label list. In this mode
`acquisition.eeg_mask` is ignored.

When `acquisition.sensors.eeg.labels` is empty, `acquisition.eeg_mask` is used
directly. If both labels and mask are empty, all reference EEG channels for the
configured cap are requested.

> **To take every channel of the cap, leave the `acquisition.sensors.eeg.labels` key out of the yaml.** Do not write `labels: []`: an empty list has no type in a ROS 2 parameter
> file and the node stops with `parameter_value_from failed for parameter 'acquisition.sensors.eeg.labels': No parameter value set`. To take only some channels, write their names
> (they are published in that order).

## EXG Selection

EXG channels correspond to eego bipolar channels. The SDK wrapper exposes their
channel type and numeric index, but not stable text names, so the driver uses
the conventional labels `EXG1` through `EXG24`.

When `acquisition.sensors.exg.labels` contains labels such as `EXG1`, `EXG2`, or
`BIP1`, the driver builds `acquisition.bip_mask` automatically and publishes the
EXG channels in the same order as the label list. In this mode
`acquisition.bip_mask` is ignored.

When `acquisition.sensors.exg.labels` is empty, `acquisition.bip_mask` is used
directly. If both labels and mask are empty and EXG is enabled, all bipolar
channels available from the amplifier are requested. If EXG is disabled, the
default bipolar mask is zero.

The EXG mask is a bit mask:

```text
EXG1 -> bit 0 -> 0x000001
EXG2 -> bit 1 -> 0x000002
EXG3 -> bit 2 -> 0x000004
EXG4 -> bit 3 -> 0x000008
EXG5 -> bit 4 -> 0x000010
```

For example, `[EXG1, EXG2]` is equivalent to `acquisition.bip_mask: "0x000003"`.

## Installed Configuration

The launch file resolves the default configuration with `$(find-pkg-share
ros2neuro_acquisition_antneuro)`, so it reads the file installed under
`install/`, not the source copy in `src/`. After editing the bundled YAML in
`src/ros2neuro_acquisition_antneuro/config`, rebuild and source the workspace:

```bash
colcon build --packages-select ros2neuro_acquisition_antneuro
source install/setup.bash
```

Alternatively, pass an explicit source-tree config path to the launch argument
while iterating.
