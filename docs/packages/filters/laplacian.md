# Laplacian filter

!!! info ""
    Package: [`ros2neuro_filters_laplacian`](https://github.com/ros2neuro/ros2neuro_filters_laplacian) · pluginlib class: `ros2neuro_filters_laplacian/LaplacianFloat` · part of [Filters](index.md)

Laplacian spatial filter for `ros2neuro`.

## Algorithm

For each channel, the filter subtracts the average of the cardinal neighbours defined by the electrode layout:

```text
    N
W [C] E
    S
```

Only non-zero entries in the layout are treated as valid channels.

## Plugin

- `ros2neuro_filters_laplacian/LaplacianFloat`

## Parameters

- `layout` (`string`, required): matrix serialized row-by-row with `;` between rows
- `nchannels` (`integer`, optional): number of channels; if omitted, the highest channel id in the layout is used

Example:

```yaml
filter_chain:
  ros__parameters:
    configname: laplacian_chain
    laplacian_chain.filters: [laplacian]
    laplacian_chain.laplacian.class: ros2neuro_filters_laplacian/LaplacianFloat
    laplacian_chain.laplacian.nchannels: 16
    laplacian_chain.laplacian.layout: "0 0 1 0 0; 2 3 4 5 6; 7 8 9 10 11; 12 13 14 15 16"
```

## Tests

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
