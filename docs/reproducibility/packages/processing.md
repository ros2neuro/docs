# Processing: tests and replication

!!! info ""
    Plugins: [Processing](../../packages/processing/index.md) · part of [Reproducibility](../index.md) › [Packages](index.md)

How the processing is checked: every processing plugin is run on the raw frames (the samples of the GDF) and compared with the function that redoes it.

| Test (`ros2neuro_devel_test`) | What it checks | Check | MATLAB functions | Python functions |
|---|---|---|---|---|
| `processing/welch/` | Welch | `check_processing_welch` | [`r2n_welch`](../matlab.md#r2n_welch), [`r2n_spectral_window`](../matlab.md#r2n_spectral_window) | [`r2n_welch`](../python.md#r2n_welch), [`r2n_spectral_window`](../python.md#r2n_spectral_window) |
| `processing/fft/` | FFT | `check_processing_fft` | [`r2n_fft`](../matlab.md#r2n_fft), [`r2n_spectral_window`](../matlab.md#r2n_spectral_window) | [`r2n_fft`](../python.md#r2n_fft), [`r2n_spectral_window`](../python.md#r2n_spectral_window) |
| `processing/spectrogram/` | spectrogram | `check_processing_spectrogram` | [`r2n_spectrogram`](../matlab.md#r2n_spectrogram), [`r2n_spectral_window`](../matlab.md#r2n_spectral_window) | [`r2n_spectrogram`](../python.md#r2n_spectrogram), [`r2n_spectral_window`](../python.md#r2n_spectral_window) |
| `processing/buffer/` | Buffer | `check_processing_buffer` | none | none |
| `processing/fbcsp/` | nine band chains, then the Fbcsp plugin | `check_processing_fbcsp` | [`r2n_butterworth`](../matlab.md#r2n_butterworth), [`r2n_fbcsp`](../matlab.md#r2n_fbcsp), [`r2n_fbcsp_weights`](../matlab.md#r2n_fbcsp_weights) | [`r2n_butterworth`](../python.md#r2n_butterworth), [`r2n_fbcsp`](../python.md#r2n_fbcsp), [`r2n_fbcsp_weights`](../python.md#r2n_fbcsp_weights) |

How to run a test: [Packages](index.md#run-the-checks). Every function is explained, with its code, in [MATLAB](../matlab.md) and [Python](../python.md); [download them](../download.md).

## Processing (base package)

### Tests of the whole stack

[`ros2neuro_devel_test`](https://github.com/ros2neuro/ros2neuro_devel_test) (`processing/`) tests EVERY processing plugin on the raw frames against MATLAB (`pwelch` for Welch), with one figure per plugin. Run: `processing/<plugin>/processing_<plugin>.launch.py` then `check_processing_<plugin>`, for `welch`, `fft`, `spectrogram`, `buffer`, `fbcsp`; the check is a MATLAB file you read from the top (see the README of that package).

## Processing FBCSP

```bash
colcon test --packages-select ros2neuro_processing_fbcsp && colcon test-result --verbose
```

`test/test_fbcsp.cpp` (no ROS graph; the plugin is loaded with pluginlib) uses the reference data in `test/reference/` (`reference_band_<k>.csv`: the signal of band *k* already filtered, what its filter chain gives to the plugin): the features equal the reference for every frame (tolerance 1e-5), bad configurations are rejected (also a parameter with the wrong type, and a configuration without `samplerate` and with the bands not in ascending order is accepted), the plugin gives the reference features for every group of frames, the topics are checked against the bands (swapped, other band, other name), a group with a missing band, another number of channels, other channel labels, another sensor or another number of samples is refused, and the message has the documented type, shape and axes.

The reference data come from the Python implementation (`mi_training/mi_training/computing/features/fbcsp.py`). To regenerate them:

```bash
cd mi_training && python3 scripts/make_fbcsp_reference.py ../src/ros2neuro_processing_fbcsp/test/reference
```

The whole chain was also checked by hand: four `filter_chain_node` (the chains written by `mi_training`) and the processing node on the reference input give the 81 features of the reference, with a maximum difference of 1.3e-7.
