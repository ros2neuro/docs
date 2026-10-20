# XDF / GDF recorder

!!! info ""
    Package: [`ros2neuro_recorder_xdf`](https://github.com/ros2neuro/ros2neuro_recorder_xdf) · pluginlib class: `ros2neuro::recorder::XDFRecorder` · part of [Recorder](index.md)

`pluginlib` recorder plugin for `ros2neuro_recorder` based on `xdffileio`.

The plugin supports:
- `gdf` output
- `bdf` output
- event export through the recorder event stream
- subject/session metadata through `xdf.*` parameters
- end-to-end round-trip validation against `ros2neuro_acquisition_eegdev` fixtures

The test suite is split between:
- focused plugin/unit coverage in `test_xdf_recorder`
- integration/e2e coverage in `test_xdf_recorder_integration_eegdev_roundtrip_gdf`

## Plugin Class

Use the following plugin name in `ros2neuro_recorder`:

`ros2neuro::recorder::XDFRecorder`

## Parameters

Recorder-level parameters are declared by `ros2neuro_recorder`. This package adds:

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
