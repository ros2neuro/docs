# CAR filter

!!! info ""
    Package: [`ros2neuro_filters_car`](https://github.com/ros2neuro/ros2neuro_filters_car) · pluginlib class: `ros2neuro_filters_car/CarFloat` · part of [Filters](index.md)

Common Average Reference filter for `ros2neuro`.

## Algorithm

For each sample, the filter subtracts the average across channels:

`x_out(s, :) = x(s, :) - mean(x(s, :))`

This is the classic CAR spatial re-referencing step.

## Plugin

- `ros2neuro_filters_car/CarFloat`

## Parameters

No extra parameters.

Example:

```yaml
filter_chain:
  ros__parameters:
    configname: filterchain
    filterchain.filters: [car]
    filterchain.car.class: ros2neuro_filters_car/CarFloat
```

## Tests

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
   and MATLAB output exceeds `1e-3`) and shows/saves a debug plot to
   `test/compare_car.png`.

Step 1 is also wired into `colcon test` as an opt-in test:

```bash
colcon build --packages-select ros2neuro_filters_car --cmake-args -DBUILD_ROUNDTRIP_TESTS=ON
colcon test --packages-select ros2neuro_filters_car
```
