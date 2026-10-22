# XDF / GDF replay device

!!! info ""
    Package: [`ros2neuro_acquisition_xdf`](https://github.com/ros2neuro/ros2neuro_acquisition_xdf) · pluginlib class: `ros2neuro::acquisition::XDFDevice` · part of [Acquisition](index.md)

Replays a recorded GDF or BDF file as if it were a live amplifier, using `xdffileio` directly. The sample rate comes from the file header; the file can be looped. It is the way to test the whole pipeline without hardware.

| | |
|---|---|
| **Layer** | Acquisition |
| **Kind** | Plugin of [`ros2neuro_acquisition`](index.md) (pluginlib class `ros2neuro::acquisition::XDFDevice`) |
| **Reads** | a GDF/BDF file (`acquisition.filename`) |
| **Publishes** | `NeuroFrame` and `NeuroFrameInfo` through the acquisition node |
| **Run** | `ros2 launch ros2neuro_acquisition_xdf xdf_acquisition.launch.xml filename:=<file>.gdf`<br>`ros2 run ros2neuro_acquisition_xdf acquisition_xdf --ros-args -p acquisition.filename:=<file>.gdf` |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_acquisition`](index.md), [`ros2neuro_data`](../msgs-data.md#ros2neuro_data), [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)
- **ROS 2 packages** (run only): `launch`, `launch_ros`
- **External libraries**:
    - `xdffileio`: reading GDF/BDF files (found with `pkg-config`)

## Messages and topics

Default node name: `acquisition`.

| | Default topic | Type | Changed by |
|---|---|---|---|
| publishes | `~/neurodata`, `~/neurodata_info` | `NeuroFrame`, `NeuroFrameInfo` | through the acquisition node (`acquisition.topic_data`, `acquisition.topic_info`) |

Messages used:

- `NeuroFrame`, `NeuroFrameInfo`: published through the acquisition node

<!-- /interfaces -->
Plugin:

```text
ros2neuro::acquisition::XDFDevice
```

## Run

```bash
ros2 launch ros2neuro_acquisition_xdf xdf_acquisition.launch.xml \
  filename:=/path/to/file.gdf
```

The launch file reads `acquisition.loop` from the selected YAML configuration.
It does not override it with a launch argument.

The package also installs a dedicated executable:

```bash
ros2 run ros2neuro_acquisition_xdf acquisition_xdf --ros-args \
  -p acquisition.filename:=/path/to/file.gdf
```

## Samplerate

The samplerate is read from the file header and used as the source of truth.
`acquisition.framerate` only controls the size/rate of emitted `NeuroFrame`
chunks:

```text
samples_per_frame = round(file_samplerate / acquisition.framerate)
actual_framerate = file_samplerate / samples_per_frame
```

## Parameters

- `acquisition.filename`: input file path
- `acquisition.framerate`: requested ROS frame rate for replay chunks
- `acquisition.loop`: rewind and replay again when the file ends

The acquisition node should generally run with `acquisition.reopen: false` for
finite file replay unless looping is enabled.

Looping reopens the file at end-of-file and prepares the XDF transfer again.
This avoids relying on `xdf_seek`, which is not reliable with all xdffileio
versions after a read transfer has reached EOF.

## Group Overrides

Sensor and trigger groups are inferred from the XDF channel metadata by default.
Every group can be overridden from ROS parameters, either by zero-based group
index or by the normalized group name:

```yaml
acquisition.sensors.eeg.name: "EEG"
acquisition.sensors.eeg.unit: "uV"
acquisition.sensors.eeg.type: 1
acquisition.sensors.eeg.labels: [Fz, FC3, C3]

acquisition.sensors.0.name: "EEG"
acquisition.sensors.0.unit: "uV"
acquisition.sensors.0.labels: [Fz, FC3, C3]

acquisition.triggers.tri.name: "TRI"
acquisition.triggers.tri.unit: "code"
acquisition.triggers.tri.labels: [trigger]
```

Supported optional fields are:

- sensors: `name`, `unit`, `labels`, `type`, `min_value`, `max_value`
- triggers: `name`, `unit`, `labels`, `min_value`, `max_value`

Name-based overrides are applied first, then index-based overrides. If `labels`
is provided, its size must match the number of channels in that group.
