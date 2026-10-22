# Processing buffer

!!! info ""
    Package: [`ros2neuro_processing_buffer`](https://github.com/ros2neuro/ros2neuro_processing_buffer) · part of [Packages](../index.md)

A sliding-window buffer: it keeps the last `buffer_samples` samples of one sensor and publishes that window as a `NeuroFeature` at every incoming frame. It is the processing stage of the deep-learning decoders, which take a window of the filtered signal as input.

| | |
|---|---|
| **Layer** | Processing |
| **Kind** | Node (`buffer_node`); not a plugin |
| **Reads** | `neurodata_filtered` (`NeuroFrame`; remap it to the filter output) |
| **Publishes** | `features` (`NeuroFeature`, `TYPE_TIME_SERIES`, shape `[samples, channels]`, name `buffered_<sensor>`) |
| **Run** | `ros2 run ros2neuro_processing_buffer buffer_node --ros-args -p sensor_name:=EEG -p buffer_samples:=512` |
| **Used by** | the EEGNet pipelines of [`ros2neuro_devel_test`](../devel-test.md), in front of [`ros2neuro_decoder_py`](../decoder/python.md) |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `rclcpp`, [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)

## Messages and topics

Default node name: `processing_buffer`.

| | Default topic | Type | Changed by |
|---|---|---|---|
| subscribes | `neurodata_filtered` (relative, `/neurodata_filtered`) | `NeuroFrame` | remap it |
| publishes | `features` (relative, `/features`) | `NeuroFeature` | remap it |

Messages used:

- `NeuroFrame`, `NeuroSensor`: read
- `NeuroFeature`, `NeuroAxis`: published

## Example configuration

From the EEGNet pipeline of [`ros2neuro_devel_test`](../devel-test.md):

```yaml
/buffer:
  ros__parameters:
    sensor_name: EEG        # the name of the block in the frame (the default is `eeg`)
    buffer_samples: 512     # length of the window, in samples
```

<!-- /interfaces -->
## How it works

`buffer_node` subscribes to the filtered `NeuroFrame` stream and keeps a **sliding window** of the last `buffer_samples`
samples of one sensor block (`sensor_name`, for example `EEG`).

- At every incoming frame the old samples are shifted out, the new ones are appended and **the whole window is published**.
  With 32-sample frames at 16 frames per second the node publishes 16 windows per second, each overlapping the previous one.
  If a frame is longer than the buffer, only its last `buffer_samples` samples are kept.
- The buffer starts filled with zeros, so the first windows contain zeros until `buffer_samples` samples have arrived (one
  second with 512 samples at 512 Hz). A decoder should ignore that first second.
- `sensor_name` is matched **exactly** against the name of the block in the frame. The default is `eeg`, while most streams call
  the block `EEG`: set it, otherwise the node logs `Sensor '...' not found in NeuroFrame` once and publishes nothing.
- The data are **sample-major**, as in `NeuroFrame`: `index = sample * channels + channel`.

## Parameters

| Parameter | Type | Default | Meaning |
|---|---|---|---|
| `sensor_name` | string | `eeg` | name of the `NeuroSensor` block to buffer (case sensitive) |
| `buffer_samples` | int | `512` | length of the window, in samples |

## Topics

Both topic names are **relative**, so with the node at the root they are `/neurodata_filtered` and `/features`: remap them in
the launch file.

| Direction | Topic | Type | Meaning |
|---|---|---|---|
| subscribes | `neurodata_filtered` | `NeuroFrame` | the filtered signal |
| publishes | `features` | `NeuroFeature` | the window |

## What it publishes

| `NeuroFeature` field | Value |
|---|---|
| `name` | `buffered_<sensor_name>` |
| `type` | `TYPE_TIME_SERIES` |
| `shape` | `[buffer_samples, channels]` |
| `axes` | `time` (unit `s`, values `0 ... (buffer_samples-1)/samplerate`) and `channels` (the channel labels of the sensor) |
| `window_length` | `buffer_samples / samplerate`, in seconds |
| `unit` | `uV` |
| `header` | copied from the latest frame that arrived |

## Example

From the EEGNet (deep-learning) pipeline of [`ros2neuro_devel_test`](../devel-test.md): a 512-sample window, one second at 512 Hz, between the
filter chain and the Python decoder.

```xml
<node pkg="ros2neuro_processing_buffer" exec="buffer_node" name="buffer" output="screen">
    <param name="sensor_name" value="EEG"/>
    <param name="buffer_samples" value="512"/>
    <remap from="/neurodata_filtered" to="/processing/filtered"/>
    <remap from="/features" to="/processing/buffered_features"/>
</node>
```

## Where it fits

Processing is the stage between the filters and the decoder, and what runs there depends on the decoder: the **classic
decoders** (LDA, QDA, SVM, Gaussian) read a power spectrum, produced by [`ros2neuro_processing_spectral`](spectral.md); the **deep-learning
decoders** read a window of the filtered signal, produced by this package. There is no common base class for processing: each
one is an ordinary node that publishes a `NeuroFeature`.
