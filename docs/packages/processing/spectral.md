# Spectral processing

!!! info ""
    Package: [`ros2neuro_processing_spectral`](https://github.com/ros2neuro/ros2neuro_processing_spectral) · part of [Packages](../index.md)

Frequency-domain processing: three plugins of [`ros2neuro_processing`](index.md) that turn the filtered signal into a spectrum (`FFT`), a power spectral density (`Welch`) or a spectrogram (`Spectrogram`), published as `NeuroFeature`. `Welch` is the processing stage of the classic decoders (LDA, QDA, SVM, Gaussian); the C++ cores of the package are also used inside the visualizer.

| | |
|---|---|
| **Layer** | Processing |
| **Kind** | Plugins of [`ros2neuro_processing`](index.md) (pluginlib classes `ros2neuro::processing::FFT`, `ros2neuro::processing::Welch`, `ros2neuro::processing::Spectrogram`) and a C++ library of cores |
| **Reads** | `NeuroFrame` (`/neurodata`, parameter `input_topic`), through the processing node |
| **Publishes** | `NeuroFeature` (`/features`, parameter `output_topic`) through the processing node; FFT and Welch have shape `[channels, frequency]`, the spectrogram `[time, frequency, channel]` |
| **Run** | in the YAML of the processing node: `processing.plugin: ros2neuro::processing::Welch`, `processing.params.*` (`ros2 run ros2neuro_processing processing_node --ros-args --params-file <file>.yaml`) |
| **Used by** | the tests of [`ros2neuro_devel_test`](../devel-test.md) (`processing/welch`, `fft`, `spectrogram`, and the decoders on the PSD) and [`ros2neuro_visualizer`](../visualizer.md) (the cores) |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_data`](../msgs-data.md#ros2neuro_data), [`ros2neuro_filters_blackman`](../filters/blackman.md), [`ros2neuro_filters_flattop`](../filters/flattop.md), [`ros2neuro_filters_hamming`](../filters/hamming.md), [`ros2neuro_filters_hann`](../filters/hann.md), [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs), [`ros2neuro_processing`](index.md)
- **External libraries**:
    - Eigen3: matrices
    - FFTW3: the transforms (found with `find_library`)

## Messages and topics

Default node name: `processing` (the node of [`ros2neuro_processing`](index.md); a launch file gives it the name of the plugin, for example `welch`, and that name is the section of the parameter file).

| | Default topic | Type | Changed by |
|---|---|---|---|
| subscribes | `/neurodata` | `NeuroFrame` | `input_topic` of the node |
| publishes | `/features` | `NeuroFeature` | `output_topic` of the node |

Messages used:

- `NeuroFrame`, `NeuroSensor`: read
- `NeuroFeature`: published (with `NeuroAxis`)

## Example configuration

The Welch plugin of the Gaussian pipeline of [`ros2neuro_devel_test`](../devel-test.md) (`data/config/psd_pipeline.yaml`): a PSD, as natural logarithm (ln), at 4, 6, ... 48 Hz of the `EEG` block (the plugin parameters live under `processing.params.`):

```yaml
/welch:
  ros__parameters:
    processing.plugin: ros2neuro::processing::Welch
    processing.params.feature: psd
    processing.params.sensor: EEG
    processing.params.samplerate: 512
    processing.params.wlength: 256
    processing.params.wtype: hamming
    processing.params.overlap: 128
    processing.params.buffer: 512
    processing.params.frequencies: "4:2:48"
    processing.params.log: true
```

The node is usually started from a launch file with remaps: `/neurodata` to the filtered signal and `/features` to the topic the decoder reads:

```xml
<node pkg="ros2neuro_processing" exec="processing_node" name="welch" output="screen">
    <param from="$(var config)/pipeline.yaml" allow_substs="true"/>
    <remap from="/neurodata" to="/processing/filtered"/>
    <remap from="/features" to="/processing/psd"/>
</node>
```

`config/spectral_nodes.yaml` has one section for each plugin (`fft`, `welch`, `spectrogram`).

<!-- /interfaces -->
## Where it fits

Processing is the stage between the filters and the decoder, and what runs there depends on the decoder: the **classic
decoders** (LDA, QDA, SVM, Gaussian) read a power spectrum, produced by the `Welch` plugin of this package; the **deep-learning
decoders** read a window of the filtered signal, produced by the `Buffer` plugin of [`ros2neuro_processing_buffer`](buffer.md). All of them are
plugins of the same host, [`ros2neuro_processing`](index.md), and publish a `NeuroFeature`. The cores of this package are also a dependency of
[`ros2neuro_visualizer`](../visualizer.md).

This package implements frequency-domain and time-frequency processing on top of
`ros2neuro_msgs/msg/NeuroFrame`, publishing the results as
`ros2neuro_msgs/msg/NeuroFeature`.

It is designed as a domain package:

- the numerical cores live in C++ and know nothing of ROS (`FFTCore`, `WelchCore`, `SpectrogramCore`, namespace `ros2neuro::processing::spectral`)
- the plugins (`ros2neuro::processing::FFT`, `Welch`, `Spectrogram`) read their parameters, accumulate the frames in a window and build the message; the processing node owns the topics
- downstream consumers, the decoders and anything else that reads a `NeuroFeature`, rely on a consistent contract

## What it provides

- `FFT`: one-sided amplitude spectrum
- `Welch`: one-sided Welch power spectral density
- `Spectrogram`: rolling time-frequency representation
- `FFTCore`, `WelchCore`, `SpectrogramCore`: the same computations as plain C++ classes (no ROS)

The three plugins share a small base (`spectral::SpectralBase`, not a plugin) with the parameters, the accumulation of the frames and the sample rate, and the selection of the frequencies (`FrequencySelection.h`).

## Package structure

- headers: `include/ros2neuro_processing_spectral`
- plugin implementations: `src`, registered in `plugins.xml`
- example config: `config/spectral_nodes.yaml`
- tests: `test/test_spectral_processors.cpp` (cores), `test/test_spectral_plugins.cpp` (plugins)

## Input and output contract

### Input

The plugins read `ros2neuro_msgs/msg/NeuroFrame` (`input_kind()` is `Frame`: the processing node subscribes to `NeuroFrame` only).

By default:

- input topic: `/neurodata` (parameter `input_topic` of the node)

The selected sensor is converted to a matrix with shape:

```text
[samples, channels]
```

If `sensor` is empty (the default), the first sensor in the frame is used.

### Output

Each plugin publishes `ros2neuro_msgs/msg/NeuroFeature`, through the processing node, on `/features` by default (`output_topic`). The header is the one of the last frame. Nothing is published until the window is full.

Default `feature` values:

- `FFT`: `fft`
- `Welch`: `psd`
- `Spectrogram`: `spectrogram`

## Feature conventions

The package follows these conventions consistently:

- FFT and Welch publish `TYPE_SPECTRUM`
- spectrogram publishes `TYPE_TIME_FREQUENCY`
- FFT and Welch publish `shape = [channels, frequency]`, with the axes named `channels` and `frequency` (in this order) and the
  data **channel-major**: `index = channel * n_frequencies + frequency`
- the spectrogram publishes `shape = [time, frequency, channel]`
- axis order always matches the order in `shape`: read `shape` and `axes` instead of assuming an order
- frequency values are in Hz
- time values are in seconds
- channel labels are read from the selected runtime `NeuroSensor.labels` field
- if runtime labels are missing or incomplete, labels are generated as `sensor_name:N`
  when a sensor name is available

Units:

- FFT: `amplitude` or `dB`
- Welch: `power/Hz` or `ln(power/Hz)`
- spectrogram: `power/Hz` or `dB/Hz`

### Scale of the Welch PSD: natural logarithm

With `log: true` (the default) `Welch` publishes the **natural logarithm** of the PSD, `ln(power/Hz)`: it does **not**
publish decibels. This is the scale of the Matlab SMR Gaussian classifiers (they are trained on `log` of the PSD), so a classifier converted
with [`ros2neuro_decoder_converters`](../decoder/converters.md) receives the features it was trained with. The unit written in the `NeuroFeature` is
`ln(power/Hz)`, and a decoder refuses a model whose `input.unit` is different.

- `log: false` publishes the linear PSD (`power/Hz`).
- To get decibels (`10*log10`) use `log: false` and apply `10*log10(PSD)` in your own node, which publishes the `NeuroFeature`
  with `unit: dB/Hz`; a decoder trained on dB (model converted with `--feature-unit "dB/Hz"`) reads that one. The relation is
  `dB = 10/ln(10) * ln = 4.3429 * ln`, and a classifier is **not** invariant to it: never mix the two scales.
- `FFT` (`20*log10` of the amplitude) and `Spectrogram` (`10*log10` of the power) still publish dB when `log` is true:
  they are not used by the decoders.

## Plugins

### `FFT`

Publishes a rolling one-sided amplitude spectrum computed over the latest `wlength` samples.

Useful when you want a compact snapshot of the current frequency content.

### `Welch`

Publishes a one-sided Welch PSD over a rolling buffer.

Useful when you want a smoother and more stable spectral estimate than a single-window FFT.

### `Spectrogram`

Publishes a rolling time-frequency feature over a buffered signal segment.

Useful when you want to visualize spectral evolution over time.

## Parameters

Given to the processing node as `processing.plugin` (the pluginlib class) and `processing.params.<name>`. The node itself has
`input_topic`, `output_topic` and `processing.name` (see [`ros2neuro_processing`](index.md)).

Shared by the three plugins:

| Parameter | Default | Meaning |
|---|---|---|
| `feature` | `fft` / `psd` / `spectrogram` | value written to `NeuroFeature.name` |
| `sensor` | `""` | sensor to extract from the frame, empty means the first sensor |
| `samplerate` | `0` | optional override in Hz, `0` means use `frame.samplerate` |
| `wlength` | `256` | analysis window length in samples (at least 2) |
| `wtype` | `hann` (`hamming` for `Welch`) | `rectangular`, `hann`, `hamming`, `blackman`, `flattop`; an unknown name stops the node at start |
| `log` | `false` for `FFT`, `true` for the others | publish logarithmic values: `Welch` the **natural logarithm** (`ln`) of the PSD, the scale of the Matlab SMR Gaussian classifiers; `FFT` (`20*log10`, amplitude) and `Spectrogram` (`10*log10`) dB |
| `frequencies` | all | a range such as `"4:2:48"` (from 4 to 48 Hz in steps of 2), a list (`"8,10,12"`) or a numeric array, to publish only those frequencies; a frequency that is not a bin of the transform is an error for that frame |

Additional parameters for `Welch` and `Spectrogram`:

| Parameter | Default | Meaning |
|---|---|---|
| `overlap` | `128` | overlap between adjacent windows, in samples (kept below `wlength`) |
| `buffer` | `1024` | rolling buffer length, in samples (at least `wlength`) |

The old names (`welch.*`, `window_length`, `sample_rate`, `sensor_name`, `apply_log`, `analysis_length`, ...) do not exist any more:
there is one set of names, those of the table. A parameter with the wrong type (`wlength: 256.0`, `log: "true"`; an integer is accepted for `samplerate`), an unknown `wtype` or a `wlength` below 2 stops the node, instead of being ignored. The plugins do not subscribe to `NeuroFrameInfo`; channel labels are taken from
the incoming `NeuroFrame` payload.

Example sections for the three plugins: `config/spectral_nodes.yaml`.

## Launch

Start one processing node for each plugin you need, each with its own name and parameter section:

```bash
ros2 run ros2neuro_processing processing_node --ros-args -r __node:=welch \
  --params-file $(ros2 pkg prefix ros2neuro_processing_spectral)/share/ros2neuro_processing_spectral/config/spectral_nodes.yaml
```

(`-r __node:=welch` selects the `welch:` section of the file.) In a launch file use `name="welch"` as in the example above.

## Window reuse

The package does not maintain its own runtime implementation of Hann, Hamming, Blackman and flattop
windows. Instead, it reuses the existing window classes from:

- [`ros2neuro_filters_hann`](../filters/hann.md)
- [`ros2neuro_filters_hamming`](../filters/hamming.md)
- [`ros2neuro_filters_blackman`](../filters/blackman.md)
- [`ros2neuro_filters_flattop`](../filters/flattop.md)

Those window packages expose reusable C++ APIs for:

- explicit initialization
- coefficient access
- mean-square normalization

This keeps the signal-processing logic centralized while still letting the spectral package use the
same window definitions as the filter packages.

## Numerical validation

The package includes numerical tests that compare the implemented algorithms against manual
reference calculations:

- FFT against a direct reference DFT
- Welch against a manual Welch reference across different overlaps and resolutions
- spectrogram slices against per-window reference spectral estimates
- frequency-axis resolution checks for different window sizes

This is covered in `test/test_spectral_processors.cpp` (the cores). `test/test_spectral_plugins.cpp` checks the plugins: the frequency selection (`"4:2:48"`, lists, errors), a known sine at the right frequency, shapes and axes, the window filling (nothing is published until the buffer is full) and the wrong configurations.

## Notes

- `samplerate: 0` means “read the sample rate from the incoming frame”
- rectangular windows are implemented locally because they are trivial and do not need a separate package
- the C++ cores (`FFTCore`, `WelchCore`, `SpectrogramCore`, in `ros2neuro::processing::spectral`) do not depend on ROS or on any UI: they are
  reused by [`ros2neuro_visualizer`](../visualizer.md), whose Spectrum tab computes the spectrum itself with them, while consumers that run in the pipeline
  rely on the `NeuroFeature` contract of the plugins
