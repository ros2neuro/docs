# Processing

!!! info ""
    Package: [`ros2neuro_processing`](https://github.com/ros2neuro/ros2neuro_processing) · plugins: [`ros2neuro_processing_spectral`](https://github.com/ros2neuro/ros2neuro_processing_spectral) · [`ros2neuro_processing_buffer`](https://github.com/ros2neuro/ros2neuro_processing_buffer) · [`ros2neuro_processing_fbcsp`](https://github.com/ros2neuro/ros2neuro_processing_fbcsp) · part of [Packages](../index.md)

Processing is the stage between the [filters](../filters/index.md) and the [decoder](../decoder/index.md). It takes the
filtered signal, a `NeuroFrame` (or a group of them, or, for a plugin that chains on another processing, a `NeuroFeature`), and turns it into a
**`NeuroFeature`**: the kind of data the decoder knows how to read. The package `ros2neuro_processing` provides the
`Processing` plugin interface and `processing_node`.

!!! important "Select one plugin"
    Set `processing.plugin` to one of the classes below. What runs here depends on what the decoder expects, so the stack
    has several processing plugins and leaves room for new ones.

## What is in this menu

| Page | What you find |
|---|---|
| [Base class: `ros2neuro_processing`](base.md) | the node, its topics and parameters, the plugin interface and how to write a new plugin |
| [Available plugins](#available-plugins) | the plugins of the family, each with its own page |

## Available plugins

| Plugin | pluginlib class | Reads | Publishes |
|---|---|---|---|
| [Welch](spectral.md) | [`ros2neuro::processing::Welch`](spectral.md) | `NeuroFrame` | `TYPE_SPECTRUM`, the PSD `[channels, frequency]` |
| [FFT](spectral.md) | [`ros2neuro::processing::FFT`](spectral.md) | `NeuroFrame` | `TYPE_SPECTRUM`, the amplitude spectrum |
| [Spectrogram](spectral.md) | [`ros2neuro::processing::Spectrogram`](spectral.md) | `NeuroFrame` | `TYPE_TIME_FREQUENCY`, `[time, frequency, channel]` |
| [Buffer](buffer.md) | [`ros2neuro::processing::Buffer`](buffer.md) | `NeuroFrame` | `TYPE_TIME_SERIES`, a window `[samples, channels]` |
| [Fbcsp](fbcsp.md) | [`ros2neuro::processing::Fbcsp`](fbcsp.md) | a group of `NeuroFrame`, one per band | `TYPE_MATRIX`, `[band, component]` |

The first three are in [`ros2neuro_processing_spectral`](spectral.md), the others in [`ros2neuro_processing_buffer`](buffer.md) and [`ros2neuro_processing_fbcsp`](fbcsp.md).
