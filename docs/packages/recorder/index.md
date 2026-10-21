# Recorder

!!! info ""
    Package: [`ros2neuro_recorder`](https://github.com/ros2neuro/ros2neuro_recorder)

The recorder writes the data and the events of a session to a file. The package provides the `NeuroRecorder`
plugin interface and the `recorder` node, which manages the open / setup / run / close lifecycle. The storage
format belongs to the plugin.

!!! important "Select one plugin"
    Set the parameter `plugin`. Today the only backend is [XDF / GDF](xdf.md),
    `ros2neuro::recorder::XDFRecorder`, which writes GDF or BDF through `xdffileio`.

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

---

## Reference (from the package README)

Core recorder node and plugin interface for ROS2neuro.

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
delegated to plugins such as `ros2neuro_recorder_xdf`.

## Main Parameters

- `plugin`: pluginlib class name of the recorder backend
- `topic_data`: topic carrying `ros2neuro_msgs/msg/NeuroFrame`, defaults to `/neurodata`
- `topic_info`: topic carrying `ros2neuro_msgs/msg/NeuroFrameInfo`, defaults to `/neurodata_info`
- `topic_event`: topic carrying `ros2neuro_msgs/msg/NeuroEvent`, defaults to `/neuroevent`
- `output`: output folder
- `filename`: explicit output filename; if empty, the node generates one
- `max_queue_size`: bounded queue size for incoming frames before the recorder loop consumes them
- `subject`, `session`, `modality`, `task`, `extra`: fields used to build the generated filename

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

For a ready-to-use launch file with the XDF backend, see `ros2neuro_recorder_xdf`.
