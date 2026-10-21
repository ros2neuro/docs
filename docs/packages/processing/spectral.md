# Spectral processing

!!! info ""
    Package: [`ros2neuro_processing_spectral`](https://github.com/ros2neuro/ros2neuro_processing_spectral) · part of [Packages](../index.md)

!!! note "Where it fits"
    This is the processing stage for the **classic decoders** (LDA, QDA, SVM, Gaussian): `welch_node` sits between the
    filters and the decoder and publishes the PSD they read. The same processors are also used **inside the
    [visualizer](../visualizer.md)** (its *Spectrum* tab), without running a node. The deep-learning decoders use the
    [buffer](buffer.md) instead. See [Processing](index.md) for the whole picture.

ROS 2 spectral processing package for `ros2neuro`.

This package implements frequency-domain and time-frequency processing on top of
`ros2neuro_msgs/msg/NeuroFrame`, publishing the results as
`ros2neuro_msgs/msg/NeuroFeature`.

It is designed as a domain package:

- reusable spectral processors live in C++
- ROS 2 nodes handle topics, parameters, buffering and message conversion
- downstream consumers such as the visualizer can read a consistent `NeuroFeature` contract

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
- FFT and Welch shapes are `[frequency, channel]`
- spectrogram shape is `[time, frequency, channel]`
- axis order always matches the order in `shape`
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
- the package is intentionally independent from the visualizer UI layer; consumers should rely on the
  `NeuroFeature` contract rather than internal implementation details
