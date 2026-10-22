# XDF / GDF recorder

!!! info ""
    Package: [`ros2neuro_recorder_xdf`](https://github.com/ros2neuro/ros2neuro_recorder_xdf) · pluginlib class: `ros2neuro::recorder::XDFRecorder` · part of [Recorder](index.md)

The recorder plugin that writes GDF or BDF files using `xdffileio`: the signal and the events of the session end up in one file that can be replayed with [`ros2neuro_acquisition_xdf`](../acquisition/xdf.md).

| | |
|---|---|
| **Layer** | Recorder |
| **Kind** | Plugin of [`ros2neuro_recorder`](index.md) (pluginlib class `ros2neuro::recorder::XDFRecorder`) |
| **Reads** | frames, stream info and events, through the recorder node |
| **Publishes** | a `.gdf` / `.bdf` file |
| **Run** | `ros2 launch ros2neuro_recorder_xdf xdf_recorder.launch.py output:=<folder> subject:=<id> task:=<name> xdf_file_type:=gdf` |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_data`](../msgs-data.md#ros2neuro_data), [`ros2neuro_recorder`](index.md)
- **ROS 2 packages** (run only): `launch`, `launch_ros`
- **External libraries**:
    - `xdffileio`: writing GDF/BDF (found with `find_library`)
    - `libeegdev`: optional, used by the round-trip tests

## Messages and topics

Default node name: `recorder` (the node of [`ros2neuro_recorder`](index.md)).

Messages used:

- `NeuroFrame`, `NeuroFrameInfo`, `NeuroEvent`: read through the recorder node

## Example configuration

From the Gaussian pipeline of [`ros2neuro_devel_test`](../devel-test.md) (`config/recorder.yaml`). `$(var ...)` are launch substitutions (`allow_substs="true"`); replace them with values when the node is not started by a launch file:

```yaml
/recorder:
    ros__parameters:
        plugin: ros2neuro::recorder::XDFRecorder
        topic_data: /acquisition/neurodata
        topic_info: /acquisition/neurodata_info
        topic_event: /neuroevent
        output: "$(var recordings_dir)"    # launch argument recordings_dir (created if missing)
        subject: "test"
        session: ""
        modality: "$(var protocol)"
        xdf.file_type: gdf
```

<!-- /interfaces -->
The plugin supports:
- `gdf` output
- `bdf` output
- event export through the recorder event stream
- subject/session metadata through `xdf.*` parameters
- end-to-end round-trip validation against [`ros2neuro_acquisition_eegdev`](../acquisition/eegdev.md) fixtures

The test suite is split between:
- focused plugin/unit coverage in `test_xdf_recorder`
- integration/e2e coverage in `test_xdf_recorder_integration_eegdev_roundtrip_gdf`

## Plugin Class

Use the following plugin name in [`ros2neuro_recorder`](index.md):

`ros2neuro::recorder::XDFRecorder`

## Parameters

Recorder-level parameters are declared by [`ros2neuro_recorder`](index.md). This package adds:

- `xdf.file_type`: output format, currently `gdf` or `bdf`
- `xdf.session_id`: session metadata stored in the file header
- `xdf.addiction`
- `xdf.birthday`: expected format `YYYY.MM.DD`
- `xdf.height`
- `xdf.weight`
- `xdf.gender`
- `xdf.handness`
- `xdf.visual_impairment`
- `xdf.icd_classification`
- `xdf.headsize`: three doubles
- `xdf.reference_position`: three doubles
- `xdf.ground_position`: three doubles
- `xdf.location`: three doubles

The plugin also consumes the recorder-level `subject` parameter and uses it as the
subject identifier in the exported file metadata.

## Launch

This package ships a ready-to-use launch file:

```bash
ros2 launch ros2neuro_recorder_xdf xdf_recorder.launch.py
```

It starts `ros2neuro_recorder/recorder` preconfigured with the XDF backend.

## Example

```bash
ros2 launch ros2neuro_recorder_xdf xdf_recorder.launch.py \
  output:=/tmp/recordings \
  subject:=sub-01 \
  session:=01 \
  task:=rest \
  xdf_file_type:=gdf
```

## Notes

- Generated filenames use the extension returned by the plugin, so `gdf` and `bdf`
  recordings keep a coherent filename suffix.
- `NeuroEvent` messages are interpreted using `onset`; XDF event duration is
  currently written as `0.0`.
- The current `xdffileio` integration supports up to 16 sensor/trigger groups.
