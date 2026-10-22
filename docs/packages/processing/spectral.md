# Spectral processing

!!! info ""
    Package: [`ros2neuro_processing_spectral`](https://github.com/ros2neuro/ros2neuro_processing_spectral) · part of [Packages](../index.md)

Frequency-domain processing: nodes that turn the filtered signal into a spectrum (FFT), a power spectral density (Welch) or a spectrogram, published as `NeuroFeature`. The Welch node is the processing stage of the classic decoders (LDA, QDA, SVM, Gaussian); the C++ processors of the package are also used inside the visualizer.

| | |
|---|---|
| **Layer** | Processing |
| **Kind** | Nodes (`fft_node`, `welch_node`, `spectrogram_node`) and a C++ library; not plugins |
| **Reads** | `/neurodata` (`NeuroFrame`, parameter `input_topic`) |
| **Publishes** | `~/fft`, `~/psd`, `~/spectrogram` (`NeuroFeature`; FFT and Welch have shape `[channels, frequency]`, the spectrogram `[time, frequency, channel]`) |
| **Run** | `ros2 launch ros2neuro_processing_spectral spectral_processing.launch.py`<br>`ros2 run ros2neuro_processing_spectral welch_node --ros-args --params-file <file>.yaml` |
| **Used by** | the Gaussian, QDA and `mi_loop` pipelines of [`ros2neuro_devel_test`](../devel-test.md) (Welch node) and [`ros2neuro_visualizer`](../visualizer.md) (the processors) |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `rclcpp`, [`ros2neuro_data`](../msgs-data.md#ros2neuro_data), [`ros2neuro_filters_blackman`](../filters/blackman.md), [`ros2neuro_filters_flattop`](../filters/flattop.md), [`ros2neuro_filters_hamming`](../filters/hamming.md), [`ros2neuro_filters_hann`](../filters/hann.md), [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)
- **ROS 2 packages** (run only): `launch`, `launch_ros`
- **External libraries**:
    - Eigen3: matrices
    - FFTW3: the transforms (found with `find_library`)

## Messages and topics

Default node name: `fft_node`, `welch_node`, `spectrogram_node`.

| | Default topic | Type | Changed by |
|---|---|---|---|
| subscribes | `/neurodata` | `NeuroFrame` | `input_topic` |
| publishes | `~/fft` | `NeuroFeature` | `output_topic` of `fft_node` |
| publishes | `~/psd` | `NeuroFeature` | `output_topic` of `welch_node` |
| publishes | `~/spectrogram` | `NeuroFeature` | `output_topic` of `spectrogram_node` |

Messages used:

- `NeuroFrame`, `NeuroSensor`: read
- `NeuroFeature`: published (with `NeuroAxis`)

## Example configuration

The Welch node of the Gaussian pipeline of [`ros2neuro_devel_test`](../devel-test.md): a PSD in dB/Hz at 4, 6, ... 48 Hz of the `EEG` block (the node also reads the `welch_node:` section of `config/spectral_nodes.yaml`, with the long parameter names):

```yaml
/welch:
  ros__parameters:
    welch.feature: psd
    welch.sensor: EEG
    welch.samplerate: 512
    welch.wlength: 256
    welch.wtype: hamming
    welch.overlap: 128
    welch.buffer: 512
    welch.frequencies: "4:2:48"
    welch.log: true
```

The node is usually started from a launch file with remaps: `/neurodata` to the filtered signal and `~/psd` to the topic the decoder reads.

<!-- /interfaces -->
## Where it fits

Processing is the stage between the filters and the decoder, and what runs there depends on the decoder: the **classic
decoders** (LDA, QDA, SVM, Gaussian) read a power spectrum, produced by `welch_node` of this package; the **deep-learning
decoders** read a window of the filtered signal, produced by [`ros2neuro_processing_buffer`](buffer.md). There is no common base class for
processing: each one is an ordinary node that publishes a `NeuroFeature`. The processors of this package are also a dependency of
[`ros2neuro_visualizer`](../visualizer.md).

This package implements frequency-domain and time-frequency processing on top of
`ros2neuro_msgs/msg/NeuroFrame`, publishing the results as
`ros2neuro_msgs/msg/NeuroFeature`.

It is designed as a domain package:

- reusable spectral processors live in C++
- ROS 2 nodes handle topics, parameters, buffering and message conversion
- downstream consumers, the decoders and anything else that reads a `NeuroFeature`, rely on a consistent contract

## What it provides

- `FFTProcessor`: one-sided amplitude spectrum
- `WelchProcessor`: one-sided Welch power spectral density
- `SpectrogramProcessor`: rolling time-frequency representation
- `fft_node`
- `welch_node`
- `spectrogram_node`

## Package structure

- headers: `include/ros2neuro_processing_spectral`
- node implementations: `src`
- default config: `spectral_nodes.yaml`
- launch file: `spectral_processing.launch.py`
- tests: `test_spectral_processors.cpp`

## Input and output contract

### Input

Each node subscribes to `ros2neuro_msgs/msg/NeuroFrame`.

By default:

- input topic: `/neurodata`

The selected sensor is converted to a matrix with shape:

```text
[samples, channels]
```

If `sensor_name` is empty, the first sensor in the frame is used.

### Output

Each node publishes `ros2neuro_msgs/msg/NeuroFeature`.

Default topics:

- FFT: `~/fft`
- Welch: `~/psd`
- spectrogram: `~/spectrogram`

Default `feature_name` values:

- FFT: `fft`
- Welch: `welch`
- spectrogram: `spectrogram`

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
- Welch: `power/Hz` or `dB/Hz`
- spectrogram: `power/Hz` or `dB/Hz`

## Nodes

### `fft_node`

Publishes a rolling one-sided amplitude spectrum computed over the latest `window_length` samples.

Default output topic:

- `~/fft`

Useful when you want a compact snapshot of the current frequency content.

### `welch_node`

Publishes a one-sided Welch PSD over a rolling buffer.

Default output topic:

- `~/psd`

Useful when you want a smoother and more stable spectral estimate than a single-window FFT.

### `spectrogram_node`

Publishes a rolling time-frequency feature over a buffered signal segment.

Default output topic:

- `~/spectrogram`

Useful when you want to visualize spectral evolution over time.

## Parameters

Shared parameters:

- `input_topic`: source `NeuroFrame` topic
- `output_topic`: destination `NeuroFeature` topic
- `feature_name`: value written to `NeuroFeature.name`
- `sensor_name`: sensor to extract from the frame, empty means first sensor
- `sample_rate`: optional override, `0.0` means use `frame.samplerate`
- `window_length`: analysis window length in samples
- `window_type`: `rectangular`, `hann`, `hamming`, `blackman`, `flattop`
- `apply_log`: publish logarithmic values

The spectral nodes do not subscribe to `NeuroFrameInfo`; channel labels are taken
from the incoming `NeuroFrame` payload.

`welch_node` accepts each of these under three names: with the `welch.` prefix used by the launchers of [`ros2neuro_devel_test`](../devel-test.md)
(`welch.feature`, `welch.sensor`, `welch.samplerate`, `welch.wlength` for the window length, `welch.wtype`, `welch.overlap`,
`welch.buffer` for the rolling buffer length, `welch.frequencies`, `welch.log`), with the short name (`feature`, `sensor`,
`wlength`...) or with the long name listed here. It also accepts `welch.frequencies`: a range such as `"4:2:48"` (from 4 to 48
Hz in steps of 2) or a list, to publish only those frequencies.

Additional parameters for `welch_node` and `spectrogram_node`:

- `overlap`: overlap between adjacent windows, in samples
- `analysis_length`: rolling buffer length, in samples

Default parameter values are provided in `spectral_nodes.yaml`.

## Launch

Run all spectral nodes:

```bash
ros2 launch ros2neuro_processing_spectral spectral_processing.launch.py
```

Run only FFT and Welch:

```bash
ros2 launch ros2neuro_processing_spectral spectral_processing.launch.py run_spectrogram:=false
```

Use a custom config file:

```bash
ros2 launch ros2neuro_processing_spectral spectral_processing.launch.py \
  config_file:=/path/to/your_spectral_nodes.yaml
```

## Window reuse

The package does not maintain its own runtime implementation of Hann, Hamming, Blackman and flattop
windows. Instead, it reuses the existing window classes from:

- [`ros2neuro_filters_hann`](../filters/hann.md)
- [`ros2neuro_filters_hamming`](../filters/hamming.md)
- [`ros2neuro_filters_blackman`](../filters/blackman.md)
- [`ros2neuro_filters_flattop`](../filters/flattop.md)

Those window packages now expose reusable C++ APIs for:

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

This is covered in `test_spectral_processors.cpp`.

## Notes

- `sample_rate=0.0` means “read the sample rate from the incoming frame”
- rectangular windows are implemented locally because they are trivial and do not need a separate package
- the C++ processors (`FFTProcessor`, `WelchProcessor`, `SpectrogramProcessor`) do not depend on ROS or on any UI: they are reused by
  [`ros2neuro_visualizer`](../visualizer.md), whose Spectrum tab computes the spectrum itself with them, while consumers that run in the pipeline
  rely on the `NeuroFeature` contract of the nodes
