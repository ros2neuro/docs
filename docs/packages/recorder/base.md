# ros2neuro_recorder: the node and the base class

!!! info ""
    Package: [`ros2neuro_recorder`](https://github.com/ros2neuro/ros2neuro_recorder)

The node and the plugin interface (the parent class) of the recorder family, with what is common to all its plugins. For what the family does and its list of plugins see the [overview](index.md); each plugin has its own page.

## Topics

| | Topic (default) | Type |
|---|---|---|
| subscribes | `/neurodata` (`topic_data`) | `NeuroFrame` |
| subscribes | `/neurodata_info` (`topic_info`) | `NeuroFrameInfo` |
| subscribes | `/neuroevent` (`topic_event`) | `NeuroEvent` |

Recording `/neuroevent` is what puts the manager's trial events in the same file as the signal.

## Minimal example

```bash
ros2 run ros2neuro_recorder recorder --ros-args \
  -p plugin:=ros2neuro::recorder::XDFRecorder \
  -p output:=/tmp/recordings \
  -p subject:=sub-01 -p task:=rest
```

or, with the ready launch file of the XDF backend:

```bash
ros2 launch ros2neuro_recorder_xdf xdf_recorder.launch.py output:=/tmp/recordings subject:=sub-01 task:=rest xdf_file_type:=gdf
```

(the launch file does not set the output folder yet: the file goes to the working directory, see [XDF / GDF](xdf.md#launch)).

---

## Reference (from the package README)

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_data`](../msgs-data.md#ros2neuro_data), [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)
- **At run time**: a recorder plugin package ([`ros2neuro_recorder_xdf`](xdf.md))

## Messages and topics

Default node name: `recorder`.

| | Default topic | Type | Changed by |
|---|---|---|---|
| subscribes | `/neurodata` | `NeuroFrame` | `topic_data` |
| subscribes | `/neurodata_info` | `NeuroFrameInfo` | `topic_info` |
| subscribes | `/neuroevent` | `NeuroEvent` | `topic_event` |

Messages used:

- `NeuroFrame`, `NeuroFrameInfo`, `NeuroEvent`: read and written to the file

## Example configuration

An example of the parameters of the recorder (the Gaussian launchers of [`ros2neuro_devel_test`](../../reproducibility/packages/index.md) used it before 2026-11-16; its tests now record the topics as CSV instead). `$(var ...)` are launch substitutions (`allow_substs="true"`); replace them with values when the node is not started by a launch file:

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
The package provides:
- `ros2neuro::recorder::NeuroRecorder`, the abstract plugin interface
- `ros2neuro::recorder::NeuroRecorderNode`, the ROS 2 node managing recorder lifecycle
- the `recorder` executable

Recorder plugins are discovered through `pluginlib` and can provide their own default
output extension and recorder-specific parameters.

## Responsibilities

`ros2neuro_recorder` is the runtime package that:
- subscribes to `NeuroFrameInfo`, `NeuroFrame`, and `NeuroEvent`
- loads a concrete recorder plugin through `pluginlib`
- manages recorder open/setup/run/close lifecycle
- builds the output filename when one is not explicitly provided

The package does not implement a storage backend by itself. Actual file writing is
delegated to plugins such as [`ros2neuro_recorder_xdf`](xdf.md).

## Main Parameters

- `plugin`: pluginlib class name of the recorder backend (required)
- `topic_data`: topic carrying `ros2neuro_msgs/msg/NeuroFrame`, defaults to `/neurodata`
- `topic_info`: topic carrying `ros2neuro_msgs/msg/NeuroFrameInfo` (`transient_local`), defaults to `/neurodata_info`
- `topic_event`: topic carrying `ros2neuro_msgs/msg/NeuroEvent`, defaults to `/neuroevent`
- `output`: output folder, defaults to `.` (created if missing)
- `filename`: explicit output filename; if empty, the node generates one
- `max_queue_size`: bounded queue size for incoming frames before the recorder loop consumes them, defaults to `32`
  (when full, the oldest frame is dropped with a warning)
- `subject` (default `unknown`), `session`, `modality`, `task`, `extra` (default empty): fields used to build the generated filename

Every parameter except the three topics is also accepted with the `recorder.` prefix (`recorder.plugin`,
`recorder.output`, ...), which wins when set.

The node waits for `NeuroFrameInfo`, opens the file, then writes every frame it receives. Events are written only
once the first frame has been recorded: an event that arrives earlier is dropped. The file is closed when the node
stops (or after a write error, after which the node shuts down).

## Generated Filename

If `filename` is empty, the recorder builds a filename as:

`<subject>[_ses-<session>][_<modality>][_task-<task>][_<extra>]_<timestamp><plugin_extension>`

The final extension is provided by the selected recorder plugin.

## Example

```bash
ros2 run ros2neuro_recorder recorder --ros-args \
  -p plugin:=ros2neuro::recorder::XDFRecorder \
  -p output:=/tmp/recordings \
  -p subject:=sub-01 \
  -p session:=01 \
  -p task:=rest
```

For a ready-to-use launch file with the XDF backend, see [`ros2neuro_recorder_xdf`](xdf.md).
