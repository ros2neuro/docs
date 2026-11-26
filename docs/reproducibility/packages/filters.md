# Filters: tests and replication

!!! info ""
    Plugins: [Filters](../../packages/filters/index.md) · part of [Reproducibility](../index.md) › [Packages](index.md)

How the filters is checked: every filter is run by the real `filter_chain_node` and compared, sample by sample, with the same filter written with the native functions of MATLAB; three chains check the order and the state.

| Test (`ros2neuro_devel_test`) | What it checks | Check | MATLAB functions | Python functions |
|---|---|---|---|---|
| `filters/single_filter/` | each of the nine filters alone | `check_filters_single` | [`r2n_dc`](../matlab.md#r2n_dc), [`r2n_car`](../matlab.md#r2n_car), [`r2n_laplacian`](../matlab.md#r2n_laplacian), [`r2n_window`](../matlab.md#r2n_window), [`r2n_butterworth`](../matlab.md#r2n_butterworth) | [`r2n_dc`](../python.md#r2n_dc), [`r2n_car`](../python.md#r2n_car), [`r2n_laplacian`](../python.md#r2n_laplacian), [`r2n_window`](../python.md#r2n_window), [`r2n_butterworth`](../python.md#r2n_butterworth) |
| `filters/chain/` | three chains: hp-lp, hp-lp-laplacian, all | `check_filters_chains` | [`r2n_dc`](../matlab.md#r2n_dc), [`r2n_car`](../matlab.md#r2n_car), [`r2n_laplacian`](../matlab.md#r2n_laplacian), [`r2n_window`](../matlab.md#r2n_window), [`r2n_butterworth`](../matlab.md#r2n_butterworth) | [`r2n_dc`](../python.md#r2n_dc), [`r2n_car`](../python.md#r2n_car), [`r2n_laplacian`](../python.md#r2n_laplacian), [`r2n_window`](../python.md#r2n_window), [`r2n_butterworth`](../python.md#r2n_butterworth) |

How to run a test: [Packages](index.md#run-the-checks). Every function is explained, with its code, in [MATLAB](../matlab.md) and [Python](../python.md); [download them](../download.md).

## Filters (base package)

### Testing Notes

Each filter package contains dedicated unit tests. The tests verify either:

- an exact numerical reference
- or a defining property of the algorithm

This is especially useful for regression checking after future refactors.

#### Full chain round-trip test (ROS vs MATLAB)

`test/` also contains an end-to-end check of the full `eeg_preprocessing` chain
defined in `config/filter_chain.full_example.yaml` (`dc -> hp -> lp -> car -> hann`),
mirroring the per-filter round-trip tests:

1. `csv_publisher.py` streams `test/rawdata.csv` (32 EEG channels, sample-major) onto
   `/neurodata` as `NeuroFrame` messages, 32 samples/frame at 512 Hz.
2. `filter_chain_node` is launched with `config/filter_chain.full_example.yaml`
   (`configname: eeg_preprocessing`), applying `dc`, then a `highpass` Butterworth
   (`order=4`, `cutoff=1.0`), then a `lowpass` Butterworth (`order=4`, `cutoff=40.0`),
   then `car`, then `hann`, and publishes on `/filter_chain/filtered`.
3. `topic_saver.py` writes the filtered stream to `test/output_data.csv`.
4. `compare_filter_chain_full.m` re-applies the same five stages in MATLAB, in the
   same order and precision (float32 between stages, matching each `Filter<float>`),
   and compares the result sample-by-sample with `output_data.csv`.

This test requires the plugin packages used by the chain to be built in the same
workspace: [`ros2neuro_filters_dc`](../../packages/filters/dc.md), [`ros2neuro_filters_butterworth`](../../packages/filters/butterworth.md),
[`ros2neuro_filters_car`](../../packages/filters/car.md), [`ros2neuro_filters_hann`](../../packages/filters/hann.md).

ROS and MATLAB are run separately (e.g. ROS inside the dev container, MATLAB on the
host where the license and a display are available):

1. Run the ROS pipeline (requires a sourced workspace; produces `test/output_data.csv`):

   ```bash
   ./test/run_ros_pipeline.sh
   ```

2. Run the MATLAB comparison manually, in MATLAB:

   ```matlab
   cd('<workspace>/src/ros2neuro_filters/test')
   compare_filter_chain_full
   ```

   This prints PASSED/FAILED (fails if the maximum absolute difference between ROS
   and MATLAB output exceeds `5e-3`) and shows/saves a debug plot to
   `test/compare_filter_chain_full.png`.

   Note: the threshold here is looser than the `1e-3` used by the window, Laplacian
   and Butterworth round-trip tests, because this chain cascades 2 stateful IIR filters
   (Butterworth hp + lp). float32 rounding at each stage propagates through
   the recursion and can produce occasional error spikes higher than in the
   stateless filters (window/car/dc/laplacian), even though the mean error
   stays around 1e-4.

Step 1 is also wired into `colcon test` as an opt-in test:

```bash
colcon build --packages-select ros2neuro_filters ros2neuro_filters_dc ros2neuro_filters_butterworth ros2neuro_filters_car ros2neuro_filters_hann --cmake-args -DBUILD_ROUNDTRIP_TESTS=ON
colcon test --packages-select ros2neuro_filters
```


### Tests of the whole stack

[`ros2neuro_devel_test`](https://github.com/ros2neuro/ros2neuro_devel_test) (`filters/`) runs EVERY filter (dc, hp, lp, car, laplacian, hann, hamming, blackman, flattop) alone and three chains, and compares them with MATLAB (`butter` + `filter`, the native windows, `mean`) to a few ULP of float32, with one figure per filter (MATLAB and ros2neuro, and their difference). Run: `filters/single_filter/filters_single.launch.py` then `check_filters_single`; `filters/chain/filters_chain.launch.py` then `check_filters_chains`; the check is a MATLAB file you read from the top (see the README of that package).

## Blackman window

### Unit tests (gtest)

`test/test_blackman.cpp` exercises `Blackman<float>`/`Blackman<double>` directly (no
ROS graph) and verifies:

- the known Blackman coefficients for a fixed small window
- the exposed reusable API (`initialize`, `coefficients`, `mean_square`)

Run with:

```bash
colcon test --packages-select ros2neuro_filters_blackman
colcon test-result --verbose
```

### Round-trip test (ROS vs MATLAB)

`test/` also contains an end-to-end check that the *real* `filter_chain_node`,
configured with this plugin, produces the same output as a MATLAB reference filter:

1. `csv_publisher.py` streams `test/rawdata.csv` (32 EEG channels, sample-major) onto
   `/neurodata` as `NeuroFrame` messages, 32 samples/frame at 512 Hz.
2. `filter_chain_node` applies `ros2neuro_filters_blackman/BlackmanFloat` and
   publishes on `/filter_chain/filtered`.
3. `topic_saver.py` writes the filtered stream to `test/output_data.csv`.
4. `compare_blackman.m` builds the reference 32-point Blackman window
   (`blackman(32, 'symmetric')`-equivalent) and applies it **block by block** (32
   samples per block, matching `samples_per_frame` — the window is created from the
   size of the first `NeuroFrame`), then compares the result sample-by-sample with
   `output_data.csv`.

The launch file (`test_blackman.launch.py`) shuts itself down automatically once the
publisher finishes, so the whole pipeline can run unattended.

ROS and MATLAB are run separately (e.g. ROS inside the dev container, MATLAB on the
host where the license and a display are available):

1. Run the ROS pipeline (requires a sourced workspace; produces `test/output_data.csv`):

   ```bash
   ./test/run_ros_pipeline.sh
   ```

2. Run the MATLAB comparison manually, in MATLAB:

   ```matlab
   cd('<workspace>/src/ros2neuro_filters_blackman/test')
   compare_blackman
   ```

   This prints PASSED/FAILED (fails if the maximum absolute difference between ROS
   and MATLAB output exceeds `1e-3`) and shows/saves a debug plot to
   `test/compare_blackman.png`.

Step 1 is also wired into `colcon test` as an opt-in test:

```bash
colcon build --packages-select ros2neuro_filters_blackman --cmake-args -DBUILD_ROUNDTRIP_TESTS=ON
colcon test --packages-select ros2neuro_filters_blackman
```

## Butterworth filter

### Unit tests (gtest)

`test/test_butterworth.cpp` exercises `Butterworth<float>` directly (no ROS graph):

- `RejectsUnknownType`: `configure()` fails for an unsupported `type` (e.g. `bandstop`)
- `LowpassPreservesConstantSignal`: a 40 Hz low-pass leaves a constant (DC) input unchanged
- `HighpassRejectsConstantSignal`: a 1 Hz high-pass drives a constant input towards zero

Run with:

```bash
colcon test --packages-select ros2neuro_filters_butterworth
colcon test-result --verbose
```

### Round-trip test (ROS vs MATLAB)

`test/` also contains an end-to-end check that the *real* `filter_chain_node`,
configured with this plugin, produces the same output as a MATLAB reference filter.
Both the `lowpass` and `highpass` configurations are exercised:

1. `csv_publisher.py` streams `test/rawdata.csv` (32 EEG channels, sample-major) onto
   `/neurodata` as `NeuroFrame` messages, 32 samples/frame at 512 Hz.
2. `filter_chain_node` applies:
   - a `lowpass` Butterworth filter (`order=4`, `cutoff=40.0`, `samplerate=512.0`),
     publishing on `/filter_chain/filtered` (`test_butterworth_lowpass.launch.py`);
   - a `highpass` Butterworth filter (`order=4`, `cutoff=1.0`, `samplerate=512.0`),
     publishing on `/filter_chain/filtered` (`test_butterworth_highpass.launch.py`).
3. `topic_saver.py` writes the filtered streams to `test/output_data_lowpass.csv`
   (low-pass) and `test/output_data_highpass.csv` (high-pass).
4. `compare_butterworth_lowpass.m` / `compare_butterworth_highpass.m` re-apply the same
   filter design (`butter(..., 'low')` / `butter(..., 'high')` + `filter`) to
   `rawdata.csv` in MATLAB and compare it sample-by-sample with the corresponding
   `output_data_*.csv`.

The launch files (`test_butterworth_lowpass.launch.py`, `test_butterworth_highpass.launch.py`)
shut themselves down automatically once the publisher finishes, so the whole pipeline
can run unattended.

ROS and MATLAB are run separately (e.g. ROS inside the dev container, MATLAB on the
host where the license and a display are available):

1. Run the ROS pipeline (requires a sourced workspace; produces
   `test/output_data_lowpass.csv` and `test/output_data_highpass.csv`):

   ```bash
   ./test/run_ros_pipeline.sh
   ```

2. Run the MATLAB comparisons manually, in MATLAB:

   ```matlab
   cd('<workspace>/src/ros2neuro_filters_butterworth/test')
   compare_butterworth_lowpass
   compare_butterworth_highpass
   ```

   Each prints PASSED/FAILED (fails if the maximum absolute difference between ROS
   and MATLAB output exceeds `1e-3`) and shows/saves a debug plot to
   `test/compare_butterworth_lowpass.png` / `test/compare_butterworth_highpass.png`.

Step 1 is also wired into `colcon test` as an opt-in test:

```bash
colcon build --packages-select ros2neuro_filters_butterworth --cmake-args -DBUILD_ROUNDTRIP_TESTS=ON
colcon test --packages-select ros2neuro_filters_butterworth
```

## CAR filter

### Unit tests (gtest)

`test/test_car.cpp` exercises `Car<float>` directly (no ROS graph):

- `RemovesPerSampleSpatialAverage`: each output row has zero mean across channels,
  and the per-element values match the expected CAR result for a known input matrix.

Run with:

```bash
colcon test --packages-select ros2neuro_filters_car
colcon test-result --verbose
```

### Round-trip test (ROS vs MATLAB)

`test/` also contains an end-to-end check that the *real* `filter_chain_node`,
configured with this plugin, produces the same output as a MATLAB reference filter:

1. `csv_publisher.py` streams `test/rawdata.csv` (32 EEG channels, sample-major) onto
   `/neurodata` as `NeuroFrame` messages, 32 samples/frame at 512 Hz.
2. `filter_chain_node` applies `ros2neuro_filters_car/CarFloat` and publishes on
   `/filter_chain/filtered`.
3. `topic_saver.py` writes the filtered stream to `test/output_data.csv`.
4. `compare_car.m` re-applies `x - mean(x, 2)` to `rawdata.csv` in MATLAB and compares
   it sample-by-sample with `output_data.csv`.

The launch file (`test_car.launch.py`) shuts itself down automatically once the
publisher finishes, so the whole pipeline can run unattended.

ROS and MATLAB are run separately (e.g. ROS inside the dev container, MATLAB on the
host where the license and a display are available):

1. Run the ROS pipeline (requires a sourced workspace; produces `test/output_data.csv`):

   ```bash
   ./test/run_ros_pipeline.sh
   ```

2. Run the MATLAB comparison manually, in MATLAB:

   ```matlab
   cd('<workspace>/src/ros2neuro_filters_car/test')
   compare_car
   ```

   This prints PASSED/FAILED (fails if the maximum absolute difference between ROS
   and MATLAB output exceeds 4 float32 ULP of the largest input sample (about 4e-3 for the test data)) and shows/saves a debug plot to
   `test/compare_car.png`.

Step 1 is also wired into `colcon test` as an opt-in test:

```bash
colcon build --packages-select ros2neuro_filters_car --cmake-args -DBUILD_ROUNDTRIP_TESTS=ON
colcon test --packages-select ros2neuro_filters_car
```

## DC filter

### Unit tests (gtest)

`test/test_dc.cpp` exercises `Dc<float>` directly (no ROS graph):

- `RemovesPerChannelOffset`: each output column has zero mean, and individual
  values match the expected result for a known input matrix.

Run with:

```bash
colcon test --packages-select ros2neuro_filters_dc
colcon test-result --verbose
```

### Round-trip test (ROS vs MATLAB)

`test/` also contains an end-to-end check that the *real* `filter_chain_node`,
configured with this plugin, produces the same output as a MATLAB reference filter:

1. `csv_publisher.py` streams `test/rawdata.csv` (32 EEG channels, sample-major) onto
   `/neurodata` as `NeuroFrame` messages, 32 samples/frame at 512 Hz.
2. `filter_chain_node` applies `ros2neuro_filters_dc/DcFloat` and publishes on
   `/filter_chain/filtered`.
3. `topic_saver.py` writes the filtered stream to `test/output_data.csv`.
4. `compare_dc.m` re-applies the filter in MATLAB **block by block** (32 samples per
   block, matching `samples_per_frame`) — since DC removal subtracts the mean of the
   current `NeuroFrame`, not of the whole recording — and compares the result
   sample-by-sample with `output_data.csv`.

The launch file (`test_dc.launch.py`) shuts itself down automatically once the
publisher finishes, so the whole pipeline can run unattended.

ROS and MATLAB are run separately (e.g. ROS inside the dev container, MATLAB on the
host where the license and a display are available):

1. Run the ROS pipeline (requires a sourced workspace; produces `test/output_data.csv`):

   ```bash
   ./test/run_ros_pipeline.sh
   ```

2. Run the MATLAB comparison manually, in MATLAB:

   ```matlab
   cd('<workspace>/src/ros2neuro_filters_dc/test')
   compare_dc
   ```

   This prints PASSED/FAILED (fails if the maximum absolute difference between ROS
   and MATLAB output exceeds `5e-3`) and shows/saves a debug plot to
   `test/compare_dc.png`.

   Note: the threshold here is wider than the `1e-3` used by the window, Laplacian and Butterworth
   round-trip tests, because the DC filter subtracts a per-block mean computed in
   single precision: a few ULP of float32 rounding in that mean, at the signal
   magnitudes in `rawdata.csv` (~1e4), already amount to a few `1e-3` of
   absolute error.

Step 1 is also wired into `colcon test` as an opt-in test:

```bash
colcon build --packages-select ros2neuro_filters_dc --cmake-args -DBUILD_ROUNDTRIP_TESTS=ON
colcon test --packages-select ros2neuro_filters_dc
```

## Flattop window

### Unit tests (gtest)

`test/test_flattop.cpp` exercises `Flattop<float>`/`Flattop<double>` directly (no
ROS graph) and verifies:

- the known flattop coefficients for a fixed small window
- the exposed reusable API (`initialize`, `coefficients`, `mean_square`)

Run with:

```bash
colcon test --packages-select ros2neuro_filters_flattop
colcon test-result --verbose
```

### Round-trip test (ROS vs MATLAB)

`test/` also contains an end-to-end check that the *real* `filter_chain_node`,
configured with this plugin, produces the same output as a MATLAB reference filter:

1. `csv_publisher.py` streams `test/rawdata.csv` (32 EEG channels, sample-major) onto
   `/neurodata` as `NeuroFrame` messages, 32 samples/frame at 512 Hz.
2. `filter_chain_node` applies `ros2neuro_filters_flattop/FlattopFloat` and
   publishes on `/filter_chain/filtered`.
3. `topic_saver.py` writes the filtered stream to `test/output_data.csv`.
4. `compare_flattop.m` builds the reference 32-point five-term flattop window and
   applies it **block by block** (32 samples per block, matching `samples_per_frame` —
   the window is created from the size of the first `NeuroFrame`), then compares the
   result sample-by-sample with `output_data.csv`.

The launch file (`test_flattop.launch.py`) shuts itself down automatically once the
publisher finishes, so the whole pipeline can run unattended.

ROS and MATLAB are run separately (e.g. ROS inside the dev container, MATLAB on the
host where the license and a display are available):

1. Run the ROS pipeline (requires a sourced workspace; produces `test/output_data.csv`):

   ```bash
   ./test/run_ros_pipeline.sh
   ```

2. Run the MATLAB comparison manually, in MATLAB:

   ```matlab
   cd('<workspace>/src/ros2neuro_filters_flattop/test')
   compare_flattop
   ```

   This prints PASSED/FAILED (fails if the maximum absolute difference between ROS
   and MATLAB output exceeds `1e-3`) and shows/saves a debug plot to
   `test/compare_flattop.png`.

Step 1 is also wired into `colcon test` as an opt-in test:

```bash
colcon build --packages-select ros2neuro_filters_flattop --cmake-args -DBUILD_ROUNDTRIP_TESTS=ON
colcon test --packages-select ros2neuro_filters_flattop
```

## Hamming window

### Unit tests (gtest)

`test/test_hamming.cpp` exercises `Hamming<float>`/`Hamming<double>` directly (no ROS
graph) and verifies:

- the known Hamming coefficients for a fixed small window
- the exposed reusable API (`initialize`, `coefficients`, `mean_square`)

Run with:

```bash
colcon test --packages-select ros2neuro_filters_hamming
colcon test-result --verbose
```

### Round-trip test (ROS vs MATLAB)

`test/` also contains an end-to-end check that the *real* `filter_chain_node`,
configured with this plugin, produces the same output as a MATLAB reference filter:

1. `csv_publisher.py` streams `test/rawdata.csv` (32 EEG channels, sample-major) onto
   `/neurodata` as `NeuroFrame` messages, 32 samples/frame at 512 Hz.
2. `filter_chain_node` applies `ros2neuro_filters_hamming/HammingFloat` and publishes
   on `/filter_chain/filtered`.
3. `topic_saver.py` writes the filtered stream to `test/output_data.csv`.
4. `compare_hamming.m` builds the reference 32-point Hamming window
   (`hamming(32, 'symmetric')`-equivalent) and applies it **block by block** (32
   samples per block, matching `samples_per_frame` — the window is created from the
   size of the first `NeuroFrame`), then compares the result sample-by-sample with
   `output_data.csv`.

The launch file (`test_hamming.launch.py`) shuts itself down automatically once the
publisher finishes, so the whole pipeline can run unattended.

ROS and MATLAB are run separately (e.g. ROS inside the dev container, MATLAB on the
host where the license and a display are available):

1. Run the ROS pipeline (requires a sourced workspace; produces `test/output_data.csv`):

   ```bash
   ./test/run_ros_pipeline.sh
   ```

2. Run the MATLAB comparison manually, in MATLAB:

   ```matlab
   cd('<workspace>/src/ros2neuro_filters_hamming/test')
   compare_hamming
   ```

   This prints PASSED/FAILED (fails if the maximum absolute difference between ROS
   and MATLAB output exceeds `1e-3`) and shows/saves a debug plot to
   `test/compare_hamming.png`.

Step 1 is also wired into `colcon test` as an opt-in test:

```bash
colcon build --packages-select ros2neuro_filters_hamming --cmake-args -DBUILD_ROUNDTRIP_TESTS=ON
colcon test --packages-select ros2neuro_filters_hamming
```

## Hann window

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

## Laplacian filter

### Unit tests (gtest)

`test/test_laplacian.cpp` exercises `Laplacian<float>` directly (no ROS graph) and
verifies:

- the cross-neighbour averaging on a small 5-channel layout
- that a layout with duplicated channel indexes is rejected by `configure()`

Run with:

```bash
colcon test --packages-select ros2neuro_filters_laplacian
colcon test-result --verbose
```

### Round-trip test (ROS vs MATLAB)

`test/` also contains an end-to-end check that the *real* `filter_chain_node`,
configured with this plugin, produces the same output as a MATLAB reference filter:

1. `csv_publisher.py` streams `test/rawdata.csv` (9 EEG channels, sample-major, the
   first 9 channels of the butterworth test data) onto `/neurodata` as `NeuroFrame`
   messages, 32 samples/frame at 512 Hz.
2. `filter_chain_node` applies `ros2neuro_filters_laplacian/LaplacianFloat` configured
   with a 3x3 grid layout (`"1 2 3; 4 5 6; 7 8 9"`, `nchannels: 9`) and publishes on
   `/filter_chain/filtered`.
3. `topic_saver.py` writes the filtered stream to `test/output_data.csv`.
4. `compare_laplacian.m` builds the reference Laplacian mask in MATLAB from the same
   3x3 layout (diagonal = 1, cardinal neighbours W/E/N/S get weight `-1/numneighbours`,
   mirroring `Laplacian<T>::create_mask`/`get_neighbours`), applies it as
   `raw_data * mask` (the filter is stateless, so no block-wise processing is needed),
   and compares the result sample-by-sample with `output_data.csv`.

The launch file (`test_laplacian.launch.py`) shuts itself down automatically once the
publisher finishes, so the whole pipeline can run unattended.

ROS and MATLAB are run separately (e.g. ROS inside the dev container, MATLAB on the
host where the license and a display are available):

1. Run the ROS pipeline (requires a sourced workspace; produces `test/output_data.csv`):

   ```bash
   ./test/run_ros_pipeline.sh
   ```

2. Run the MATLAB comparison manually, in MATLAB:

   ```matlab
   cd('<workspace>/src/ros2neuro_filters_laplacian/test')
   compare_laplacian
   ```

   This prints PASSED/FAILED (fails if the maximum absolute difference between ROS
   and MATLAB output exceeds `1e-3`) and shows/saves a debug plot to
   `test/compare_laplacian.png`.

Step 1 is also wired into `colcon test` as an opt-in test:

```bash
colcon build --packages-select ros2neuro_filters_laplacian --cmake-args -DBUILD_ROUNDTRIP_TESTS=ON
colcon test --packages-select ros2neuro_filters_laplacian
```
