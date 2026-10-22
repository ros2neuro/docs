# Butterworth filter

!!! info ""
    Package: [`ros2neuro_filters_butterworth`](https://github.com/ros2neuro/ros2neuro_filters_butterworth) · pluginlib class: `ros2neuro_filters_butterworth/ButterworthFloat` · part of [Filters](index.md)

A real-time Butterworth IIR filter, low-pass or high-pass (chain one of each for a band-pass), built on `librtfilter`; it keeps its state from one frame to the next. A temporal filter for the [`ros2neuro_filters`](index.md) chain.

| | |
|---|---|
| **Layer** | Filters |
| **Kind** | Plugin of [`ros2neuro_filters`](index.md) (pluginlib class `ros2neuro_filters_butterworth/ButterworthFloat`) |
| **Reads** | the `[samples x channels]` matrix of the previous filter in the chain |
| **Publishes** | a matrix of the same size, for the next filter |
| **Run** | in the chain YAML: `<configname>.<name>.class: ros2neuro_filters_butterworth/ButterworthFloat` |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_filters`](index.md)
- **External libraries**:
    - Eigen3: matrices
    - `librtfilter`: the IIR filter implementation (found with `find_library`)

## Messages and topics

Default node name: (none: it runs inside `filter_chain_node`).

Messages used:

- none: it works on a `[samples x channels]` matrix, not on messages

<!-- /interfaces -->
## Algorithm

The plugin builds a stateful low-pass or high-pass Butterworth filter. Internal state is allocated on first use, once the number of channels is known.

## Plugin

- `ros2neuro_filters_butterworth/ButterworthFloat`

## Parameters

- `order` (`integer`, required)
- `samplerate` (`double`, required)
- `cutoff` (`double`, required)
- `type` (`string`, required): `lowpass` or `highpass`

Example:

```yaml
filter_chain:
  ros__parameters:
    configname: filterchain
    filterchain.filters: [hp, lp]

    filterchain.hp.class: ros2neuro_filters_butterworth/ButterworthFloat
    filterchain.hp.order: 4
    filterchain.hp.samplerate: 512.0
    filterchain.hp.cutoff: 1.0
    filterchain.hp.type: highpass

    filterchain.lp.class: ros2neuro_filters_butterworth/ButterworthFloat
    filterchain.lp.order: 4
    filterchain.lp.samplerate: 512.0
    filterchain.lp.cutoff: 40.0
    filterchain.lp.type: lowpass
```

## Tests

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
