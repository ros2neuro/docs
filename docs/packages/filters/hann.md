# Hann window

!!! info ""
    Package: [`ros2neuro_filters_hann`](https://github.com/ros2neuro/ros2neuro_filters_hann) · pluginlib class: `ros2neuro_filters_hann/HannFloat` · part of [Filters](index.md)

Hann window filter package for `ros2neuro`.

This package serves two related purposes:

- it exports a [`ros2neuro_filters`](index.md) plugin that applies a Hann window to an input matrix
- it exposes a small reusable C++ API that can be used by other packages needing Hann
  coefficients and normalization terms, such as spectral estimators

## Window definition

For a window length `N`, the Hann coefficients are:

```text
w[n] = 0.5 * (1 - cos(2*pi*n/(N-1)))
```

for `n = 0, ..., N-1`.

## Plugin

- plugin id: `ros2neuro_filters_hann/HannFloat`
- header: `Hann.hpp`

The plugin applies the window row-wise to the incoming matrix, independently for each channel.

## Reusable C++ API

The `ros2neuro::filters::Hann<T>` class now exposes:

- `initialize(int nsamples)`: explicitly create the window coefficients
- `coefficients()`: read the cached coefficient vector
- `mean_square()`: read the average squared coefficient value
- `apply(...)`: multiply an input matrix by the window

This makes the class usable both as a filter plugin and as a utility inside packages such as
[`ros2neuro_processing_spectral`](../processing/spectral.md).

Example:

```cpp
ros2neuro::filters::Hann<double> window;
window.initialize(256);

const auto& coeffs = window.coefficients();
double mean_square = window.mean_square();
```

## Parameters

No extra runtime parameters.

## Tests

### Unit tests (gtest)

`test/test_hann.cpp` exercises `Hann<float>`/`Hann<double>` directly (no ROS graph)
and verifies:

- the known Hann coefficients for a fixed small window
- the exposed reusable API (`initialize`, `coefficients`, `mean_square`)

Run with:

```bash
colcon test --packages-select ros2neuro_filters_hann
colcon test-result --verbose
```

### Round-trip test (ROS vs MATLAB)

`test/` also contains an end-to-end check that the *real* `filter_chain_node`,
configured with this plugin, produces the same output as a MATLAB reference filter:

1. `csv_publisher.py` streams `test/rawdata.csv` (32 EEG channels, sample-major) onto
   `/neurodata` as `NeuroFrame` messages, 32 samples/frame at 512 Hz.
2. `filter_chain_node` applies `ros2neuro_filters_hann/HannFloat` and publishes on
   `/filter_chain/filtered`.
3. `topic_saver.py` writes the filtered stream to `test/output_data.csv`.
4. `compare_hann.m` builds the reference 32-point symmetric Hann window
   (`hann(32, 'symmetric')`-equivalent) and applies it **block by block** (32 samples
   per block, matching `samples_per_frame` — the window is created from the size of
   the first `NeuroFrame`), then compares the result sample-by-sample with
   `output_data.csv`.

The launch file (`test_hann.launch.py`) shuts itself down automatically once the
publisher finishes, so the whole pipeline can run unattended.

ROS and MATLAB are run separately (e.g. ROS inside the dev container, MATLAB on the
host where the license and a display are available):

1. Run the ROS pipeline (requires a sourced workspace; produces `test/output_data.csv`):

   ```bash
   ./test/run_ros_pipeline.sh
   ```

2. Run the MATLAB comparison manually, in MATLAB:

   ```matlab
   cd('<workspace>/src/ros2neuro_filters_hann/test')
   compare_hann
   ```

   This prints PASSED/FAILED (fails if the maximum absolute difference between ROS
   and MATLAB output exceeds `1e-3`) and shows/saves a debug plot to
   `test/compare_hann.png`.

Step 1 is also wired into `colcon test` as an opt-in test:

```bash
colcon build --packages-select ros2neuro_filters_hann --cmake-args -DBUILD_ROUNDTRIP_TESTS=ON
colcon test --packages-select ros2neuro_filters_hann
```
