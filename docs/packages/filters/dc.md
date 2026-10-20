# DC filter

!!! info ""
    Package: [`ros2neuro_filters_dc`](https://github.com/ros2neuro/ros2neuro_filters_dc) · pluginlib class: `ros2neuro_filters_dc/DcFloat` · part of [Filters](index.md)

DC removal filter for `ros2neuro`.

## Algorithm

For each channel, the filter subtracts the mean computed over the current time window:

`x_out(:, c) = x(:, c) - mean(x(:, c))`

This removes the per-channel DC component while preserving the matrix shape `[samples x channels]`.

## Plugin

- `ros2neuro_filters_dc/DcFloat`

## Parameters

No extra parameters.

Example:

```yaml
filter_chain:
  ros__parameters:
    configname: filterchain
    filterchain.filters: [dc]
    filterchain.dc.class: ros2neuro_filters_dc/DcFloat
```

## Tests

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

   Note: the threshold here is wider than the `1e-3` used by other single-stage
   filters, because the DC filter subtracts a per-block mean computed in
   single precision: a few ULP of float32 rounding in that mean, at the signal
   magnitudes in `rawdata.csv` (~1e4), already amount to a few `1e-3` of
   absolute error.

Step 1 is also wired into `colcon test` as an opt-in test:

```bash
colcon build --packages-select ros2neuro_filters_dc --cmake-args -DBUILD_ROUNDTRIP_TESTS=ON
colcon test --packages-select ros2neuro_filters_dc
```
