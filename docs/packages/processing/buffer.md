# Processing buffer

!!! info ""
    Package: [`ros2neuro_processing_buffer`](https://github.com/ros2neuro/ros2neuro_processing_buffer) · part of [Packages](../index.md)

`ros2neuro_processing_buffer` is designed to accumulate continuous `NeuroFrame` or incoming data streams into fixed-size buffers (e.g., for feature extraction, signal processing, or feeding into decoders).

## Overview

This node subscribes to a data topic, buffers the samples according to the specified size (e.g., buffering a certain number of samples like 512), and publishes the resulting buffer once it is full. This is useful for creating feature windows for machine learning models and decoders.

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
