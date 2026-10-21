# Filters

!!! info ""
    Package: [`ros2neuro_filters`](https://github.com/ros2neuro/ros2neuro_filters)

The filters package provides the **filter chain**: one node, `filter_chain_node`, that applies an ordered list of
filters to every `NeuroFrame`. Each filter is a plugin working on a matrix shaped `[samples x channels]`, and the
chain is described entirely in YAML.

## Available plugins

| Kind | Plugin | pluginlib class |
|---|---|---|
| Temporal | [DC](dc.md) | [`ros2neuro_filters_dc/DcFloat`](dc.md) |
| Temporal | [Butterworth](butterworth.md) | [`ros2neuro_filters_butterworth/ButterworthFloat`](butterworth.md) |
| Spatial | [CAR](car.md) | [`ros2neuro_filters_car/CarFloat`](car.md) |
| Spatial | [Laplacian](laplacian.md) | [`ros2neuro_filters_laplacian/LaplacianFloat`](laplacian.md) |
| Window | [Hann](hann.md) | [`ros2neuro_filters_hann/HannFloat`](hann.md) |
| Window | [Hamming](hamming.md) | [`ros2neuro_filters_hamming/HammingFloat`](hamming.md) |
| Window | [Blackman](blackman.md) | [`ros2neuro_filters_blackman/BlackmanFloat`](blackman.md) |
| Window | [Flattop](flattop.md) | [`ros2neuro_filters_flattop/FlattopFloat`](flattop.md) |

Filters never change the dimensionality of the data.

## Topics

| | Topic | Type |
|---|---|---|
| subscribes | `/neurodata` (`input_topic`) | `NeuroFrame` |
| publishes | `~/filtered` (`output_topic`) | `NeuroFrame` |

## Minimal example

A Butterworth band, then a common average reference:

```yaml
filter_chain:
  ros__parameters:
    configname: eeg_preprocessing

    eeg_preprocessing.filters: [hp, lp, car]

    eeg_preprocessing.hp.class: ros2neuro_filters_butterworth/ButterworthFloat
    eeg_preprocessing.hp.order: 4
    eeg_preprocessing.hp.samplerate: 512.0
    eeg_preprocessing.hp.cutoff: 1.0
    eeg_preprocessing.hp.type: highpass

    eeg_preprocessing.lp.class: ros2neuro_filters_butterworth/ButterworthFloat
    eeg_preprocessing.lp.order: 4
    eeg_preprocessing.lp.samplerate: 512.0
    eeg_preprocessing.lp.cutoff: 40.0
    eeg_preprocessing.lp.type: lowpass

    eeg_preprocessing.car.class: ros2neuro_filters_car/CarFloat
```

```bash
ros2 run ros2neuro_filters filter_chain_node --ros-args --params-file my_chain.yaml
```

The list of filters is read from `<configname>.filters` (the key `<configname>.chain` is accepted as well), and
each filter `<name>` is configured by the parameters under `<configname>.<name>.*`. When `configname` is not
given the node uses `filters`, which is why the launch files of [`ros2neuro_devel_test`](../devel-test.md) write `filters.chain` and
`filters.laplacian.class`.

## Writing a new filter

Derive from `ros2neuro::filters::Filter<float>`, override `configure()` and `apply()`, register the class and
export `plugins.xml` to `ros2neuro_filters`. The tutorial
[Writing a filter plugin](../../tutorials/filter-plugin/index.md) does this step by step.

---

## Reference (from the package README)

`ros2neuro_filters` provides the ROS2 filter-chain core for `ros2neuro`.

It includes:

- the base interface `ros2neuro::filters::Filter<T>`
- the plugin loader `ros2neuro::filters::FilterChain<T>`
- the executable `filter_chain_node`
- helpers to apply a filter chain directly to `ros2neuro_msgs/msg/NeuroFrame`

The design keeps the original ROS1 philosophy:

- each filter is an independent `pluginlib` plugin
- the chain works on matrices shaped as `[samples x channels]`
- filters do not change the input dimensionality
- chains are configured declaratively through parameters

## Available Plugins

Temporal filters:

- [`ros2neuro_filters_dc`](dc.md)
- [`ros2neuro_filters_butterworth`](butterworth.md)

Spatial filters:

- [`ros2neuro_filters_car`](car.md)
- [`ros2neuro_filters_laplacian`](laplacian.md)

Windows:

- [`ros2neuro_filters_blackman`](blackman.md)
- [`ros2neuro_filters_flattop`](flattop.md)
- [`ros2neuro_filters_hamming`](hamming.md)
- [`ros2neuro_filters_hann`](hann.md)

## Node Interface

Executable:

- `filter_chain_node`

Subscribed topic:

- `/neurodata` (`ros2neuro_msgs/msg/NeuroFrame`)

Published topic:

- `~/filtered` (`ros2neuro_msgs/msg/NeuroFrame`)

Main parameters:

- `configname` (`string`, default `filterchain`)
- `input_topic` (`string`, default `/neurodata`)
- `output_topic` (`string`, default `~/filtered`)

## Configuration Format

In ROS2 the chain is configured with flattened parameters. The root prefix is selected by `configname`.

Minimal example:

```yaml
filter_chain:
  ros__parameters:
    configname: filterchain

    filterchain.filters:
      - dc
      - car
      - hann

    filterchain.dc.class: ros2neuro_filters_dc/DcFloat
    filterchain.car.class: ros2neuro_filters_car/CarFloat
    filterchain.hann.class: ros2neuro_filters_hann/HannFloat
```

Example with parameters:

```yaml
filter_chain:
  ros__parameters:
    configname: eeg_preprocessing

    eeg_preprocessing.filters:
      - hp
      - lp
      - car

    eeg_preprocessing.hp.class: ros2neuro_filters_butterworth/ButterworthFloat
    eeg_preprocessing.hp.order: 4
    eeg_preprocessing.hp.samplerate: 512.0
    eeg_preprocessing.hp.cutoff: 1.0
    eeg_preprocessing.hp.type: highpass

    eeg_preprocessing.lp.class: ros2neuro_filters_butterworth/ButterworthFloat
    eeg_preprocessing.lp.order: 4
    eeg_preprocessing.lp.samplerate: 512.0
    eeg_preprocessing.lp.cutoff: 40.0
    eeg_preprocessing.lp.type: lowpass

    eeg_preprocessing.car.class: ros2neuro_filters_car/CarFloat
```

Ready-to-use files:

- `filter_chain.example.yaml`
- `filter_chain.full_example.yaml`

## Launch

```bash
ros2 launch ros2neuro_filters filter_chain.launch.py
```

If you want a different config file, pass your own `parameters` list in a custom launch file or run the node directly:

```bash
ros2 run ros2neuro_filters filter_chain_node --ros-args --params-file my_chain.yaml
```

## C++ Usage

```cpp
#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "ros2neuro_filters/FilterChain.h"

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);

  rclcpp::NodeOptions options;
  options.allow_undeclared_parameters(true);
  options.automatically_declare_parameters_from_overrides(true);

  auto node = std::make_shared<rclcpp::Node>("filter_chain_client", options);

  ros2neuro::filters::FilterChain<float> chain;
  if (!chain.configure("filterchain", *node)) {
    return 1;
  }

  ros2neuro::filters::DynamicMatrix<float> data(32, 8);
  data.setRandom();

  const auto output = chain.apply(data);
  (void)output;

  rclcpp::shutdown();
  return 0;
}
```

## Mini Tutorial: Custom Filter

Create a new package, for example `ros2neuro_filters_myfilter`, with:

```text
ros2neuro_filters_myfilter/
|- include/ros2neuro_filters_myfilter/MyFilter.hpp
|- src/MyFilter.cpp
|- plugins.xml
|- CMakeLists.txt
|- package.xml
```

Implement the filter by deriving from `ros2neuro::filters::Filter<float>`:

```cpp
#include "ros2neuro_filters/Filter.h"

namespace ros2neuro::filters {

class MyFilter : public Filter<float> {
  public:
    MyFilter() {
      this->name_ = "my_filter";
    }

    bool configure() override {
      if (!this->getParam("gain", gain_)) {
        gain_ = 1.0;
      }
      return true;
    }

    DynamicMatrix<float> apply(const DynamicMatrix<float>& input) override {
      return static_cast<float>(gain_) * input;
    }

  private:
    double gain_{1.0};
};

}  // namespace ros2neuro::filters
```

Export it with `pluginlib`:

```cpp
#include "pluginlib/class_list_macros.hpp"
#include "ros2neuro_filters_myfilter/MyFilter.hpp"

PLUGINLIB_EXPORT_CLASS(ros2neuro::filters::MyFilter, ros2neuro::filters::Filter<float>)
```

Describe the plugin in `plugins.xml`:

```xml
<library path="ros2neuro_filters_myfilter">
  <class
      name="ros2neuro_filters_myfilter/MyFilter"
      type="ros2neuro::filters::MyFilter"
      base_class_type="ros2neuro::filters::Filter&lt;float&gt;">
    <description>Example custom filter.</description>
  </class>
</library>
```

Then configure it in the chain:

```yaml
filter_chain:
  ros__parameters:
    configname: filterchain
    filterchain.filters: [my_filter]
    filterchain.my_filter.class: ros2neuro_filters_myfilter/MyFilter
    filterchain.my_filter.gain: 2.0
```

## Testing Notes

Each filter package contains dedicated unit tests. The tests verify either:

- an exact numerical reference
- or a defining property of the algorithm

This is especially useful for regression checking after future refactors.

### Full chain round-trip test (ROS vs MATLAB)

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
workspace: [`ros2neuro_filters_dc`](dc.md), [`ros2neuro_filters_butterworth`](butterworth.md),
[`ros2neuro_filters_car`](car.md), [`ros2neuro_filters_hann`](hann.md).

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

   Note: the threshold here is looser than the `1e-3` used by the per-filter
   round-trip tests, because this chain cascades 2 stateful IIR filters
   (Butterworth hp + lp). float32 rounding at each stage propagates through
   the recursion and can produce occasional error spikes higher than in the
   stateless filters (window/car/dc/laplacian), even though the mean error
   stays around 1e-4.

Step 1 is also wired into `colcon test` as an opt-in test:

```bash
colcon build --packages-select ros2neuro_filters ros2neuro_filters_dc ros2neuro_filters_butterworth ros2neuro_filters_car ros2neuro_filters_hann --cmake-args -DBUILD_ROUNDTRIP_TESTS=ON
colcon test --packages-select ros2neuro_filters
```
