# Processing buffer

!!! info ""
    Package: [`ros2neuro_processing_buffer`](https://github.com/ros2neuro/ros2neuro_processing_buffer) · part of [Packages](../index.md)

A sliding-window buffer: a plugin of [`ros2neuro_processing`](index.md) (`ros2neuro::processing::Buffer`) that keeps the last `buffer` samples of one sensor and publishes that window as a `NeuroFeature` at every incoming frame. It is the processing stage of the deep-learning decoders, which take a window of the filtered signal as input.

| | |
|---|---|
| **Layer** | Processing |
| **Kind** | Plugin of [`ros2neuro_processing`](index.md) (pluginlib class `ros2neuro::processing::Buffer`) |
| **Reads** | `NeuroFrame` (`/neurodata`, parameter `input_topic`; remap or set it to the filter output), through the processing node |
| **Publishes** | `NeuroFeature` (`/features`, parameter `output_topic`; `TYPE_TIME_SERIES`, shape `[samples, channels]`, name `buffered_<sensor>`) through the processing node |
| **Run** | in the YAML of the processing node: `processing.plugin: ros2neuro::processing::Buffer`, `processing.params.sensor: EEG`, `processing.params.buffer: 512` |
| **Used by** | the tests of [`ros2neuro_devel_test`](../../reproducibility/packages/index.md) (`processing/buffer`, and `decoder/shallow` in front of [`ros2neuro_decoder_braindecode`](../decoder/braindecode.md)) |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs), [`ros2neuro_processing`](index.md)

## Messages and topics

Default node name: `processing` (the node of [`ros2neuro_processing`](index.md); a launch file names it, for example `buffer`, and that name is the section of the parameter file).

| | Default topic | Type | Changed by |
|---|---|---|---|
| subscribes | `/neurodata` | `NeuroFrame` | `input_topic` of the node, or a remap |
| publishes | `/features` | `NeuroFeature` | `output_topic` of the node, or a remap |

Messages used:

- `NeuroFrame`, `NeuroSensor`: read
- `NeuroFeature`, `NeuroAxis`: published

## Example configuration

From the ShallowNet test of [`ros2neuro_devel_test`](../../reproducibility/packages/index.md) (`decoder/shallow/decoder_shallow.launch.py`):

```yaml
/buffer:
  ros__parameters:
    processing.plugin: ros2neuro::processing::Buffer
    processing.params.sensor: EEG       # the name of the block in the frame (the default is `eeg`)
    processing.params.buffer: 512       # length of the window, in samples
```

<!-- /interfaces -->
## How it works

The `Buffer` plugin reads the filtered `NeuroFrame` stream (through the processing node) and keeps a **sliding window** of the last `buffer`
samples of one sensor block (`sensor`, for example `EEG`).

- At every incoming frame the old samples are shifted out, the new ones are appended and **the whole window is published**.
  With 32-sample frames at 16 frames per second the node publishes 16 windows per second, each overlapping the previous one.
  If a frame is longer than the buffer, only its last `buffer` samples are kept.
- The buffer starts filled with zeros, so the first windows contain zeros until `buffer` samples have arrived (one
  second with 512 samples at 512 Hz). A decoder should ignore that first second.
- `sensor` is matched **exactly** against the name of the block in the frame. The default is `eeg`, while most streams call
  the block `EEG`: set it, otherwise every frame is dropped with the warning `sensor '...' not found in the NeuroFrame` and nothing is published.
- The data are **sample-major**, as in `NeuroFrame`: `index = sample * channels + channel`.

## Parameters

| Parameter | Type | Default | Meaning |
|---|---|---|---|
| `sensor` | string | `eeg` | name of the `NeuroSensor` block to buffer (case sensitive) |
| `buffer` | int | `512` | length of the window, in samples (at least 1: otherwise the node stops at start) |

Given as `processing.params.sensor` and `processing.params.buffer`. The old names `sensor_name` and `buffer_samples` do not exist any more. A parameter with the wrong type (`buffer: 512.0`) or a `buffer` below 1 stops the node.

## Topics

Set by the processing node: `input_topic` (default `/neurodata`) and `output_topic` (default `/features`), or remap them in the launch file.

| Direction | Topic | Type | Meaning |
|---|---|---|---|
| subscribes | `/neurodata` | `NeuroFrame` | the filtered signal |
| publishes | `/features` | `NeuroFeature` | the window |

## What it publishes

| `NeuroFeature` field | Value |
|---|---|
| `name` | `buffered_<sensor>` |
| `type` | `TYPE_TIME_SERIES` |
| `shape` | `[buffer, channels]` |
| `axes` | `time` (unit `s`, values `0 ... (buffer-1)/samplerate`) and `channels` (the channel labels of the sensor) |
| `window_length` | `buffer / samplerate`, in seconds |
| `unit` | `uV` |
| `header` | copied from the latest frame that arrived |

## Example

From the ShallowNet (deep-learning) test of [`ros2neuro_devel_test`](../../reproducibility/packages/index.md): a 512-sample window, one second at 512 Hz, between the
filter chain and the `Braindecode` decoder.

```xml
<node pkg="ros2neuro_processing" exec="processing_node" name="buffer" output="screen">
    <param from="$(var config)/pipeline.yaml" allow_substs="true"/>
    <remap from="/neurodata" to="/processing/filtered"/>
    <remap from="/features" to="/processing/buffered_features"/>
</node>
```

with the `/buffer` section of the example configuration above in `pipeline.yaml`.

## Where it fits

Processing is the stage between the filters and the decoder, and what runs there depends on the decoder: the **classic
decoders** (LDA, QDA, SVM, Gaussian) read a power spectrum, produced by the `Welch` plugin of [`ros2neuro_processing_spectral`](spectral.md); the **deep-learning
decoders** read a window of the filtered signal, produced by this package. All of them are plugins of the same host,
[`ros2neuro_processing`](index.md), and publish a `NeuroFeature`.
