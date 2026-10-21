# Processing buffer

!!! info ""
    Package: [`ros2neuro_processing_buffer`](https://github.com/ros2neuro/ros2neuro_processing_buffer) · part of [Packages](../index.md)

!!! note "Where it fits"
    This is the processing stage for the **deep-learning decoders**: `buffer_node` sits between the filters and the Python
    decoder and gives it a window of the signal, which is what a neural network takes as input. The classic decoders use the
    [spectral](spectral.md) processing instead. See [Processing](index.md) for the whole picture.

`ros2neuro_processing_buffer` is designed to accumulate continuous `NeuroFrame` or incoming data streams into fixed-size buffers (e.g., for feature extraction, signal processing, or feeding into decoders).

## Overview

This node subscribes to a data topic, keeps the most recent samples in a buffer of the specified size (e.g., 512 samples) and publishes that window. This is useful for creating feature windows for machine learning models and decoders. How exactly it behaves is described in the next section.

## How it behaves

Read from the code of `buffer_node`:

- The buffer is a **sliding window** of the last `buffer_samples` samples of the sensor `sensor_name`. At every incoming frame the
  old samples are shifted out, the new ones are appended, and **the whole window is published**: with 32-sample frames at 16 Hz
  you get 16 windows per second, each overlapping the previous one.
- At the start the buffer is filled with zeros, so the first windows contain zeros until `buffer_samples` samples have arrived
  (one second with 512 samples at 512 Hz). A decoder should ignore that first second.
- `sensor_name` is matched **exactly** against the name of the block in the frame. The default is `eeg` while most streams call
  the block `EEG`: set it, otherwise the node only warns that the sensor was not found and publishes nothing.

What it publishes, a `NeuroFeature`:

| Field | Value |
|---|---|
| `name` | `buffered_<sensor_name>` |
| `type` | `TYPE_TIME_SERIES` |
| `shape` | `[buffer_samples, channels]` (the first axis is `time`) |
| `window_length` | `buffer_samples / samplerate`, in seconds |
| `unit` | `uV` |
| `header` | copied from the latest frame that arrived |

Topics: it subscribes to `neurodata_filtered` and publishes `features`, both relative names (so `/neurodata_filtered` and
`/features` with the node at the root): remap them to your filter output and to the topic the decoder reads.

## Example Launch File

You can integrate this node into your launch pipeline easily. Below is an example extracted from a typical decoder pipeline, showcasing how to configure and run the `buffer_node`:

```xml
<launch>
    <!-- Feature Extraction (Buffer for 512 samples) -->
    <node pkg="ros2neuro_processing_buffer"
          exec="buffer_node"
          name="buffer"
          output="screen">

        <!-- Configure the target sensor grouping -->
        <param name="sensor_name" value="EEG"/>
        <!-- Define how many samples to buffer before publishing -->
        <param name="buffer_samples" value="512"/>
    </node>
</launch>
```

### Parameters

- **`sensor_name`** (string): The target sensor payload name to read from the incoming stream (e.g., `"EEG"`).
- **`buffer_samples`** (int): The number of samples to accumulate before emitting a buffered message (e.g., `512`).

### Subscriptions and Publications

Ensure to use `<remap>` to properly link this node's inputs and outputs with the rest of your `ros2neuro` pipeline (e.g., from filters and to the decoder). Example:
```xml
<remap from="/neurodata_filtered" to="/processing/filtered"/>
```

- **Input**: `NeuroFrame`: Typically a filtered neuro stream.
- **Output**: `NeuroFeature`: An aggregated feature/data frame output.
