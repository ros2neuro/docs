# ros2neuro_filters: the node and the base class

!!! info ""
    Package: [`ros2neuro_filters`](https://github.com/ros2neuro/ros2neuro_filters)

The node and the plugin interface (the parent class) of the filters family, with what is common to all its plugins. For what the family does and its list of plugins see the [overview](index.md); each plugin has its own page.

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
given the node uses `filters`, which is why the launch files of [`ros2neuro_devel_test`](../../reproducibility/packages/index.md) write `filters.chain` and
`filters.laplacian.class`.

## Writing a new filter

Derive from `ros2neuro::filters::Filter<float>`, override `configure()` and `apply()`, register the class and
export `plugins.xml` to `ros2neuro_filters`. The tutorial
[Writing a filter plugin](../../tutorials/filter-plugin/index.md) does this step by step.

---

## Reference (from the package README)

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_data`](../msgs-data.md#ros2neuro_data), [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)
- **ROS 2 packages** (run only): `launch_ros`
- **External libraries**:
    - Eigen3: matrices
- **At run time**: the filter plugin packages named in the chain

## Messages and topics

Default node name: `filter_chain`.

| | Default topic | Type | Changed by |
|---|---|---|---|
| subscribes | `/neurodata` | `NeuroFrame` | `input_topic` |
| publishes | `~/filtered` | `NeuroFrame` | `output_topic` |

Messages used:

- `NeuroFrame`, `NeuroSensor`: read, filtered and published again with the same structure

<!-- /interfaces -->
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

Every `NeuroSensor` block of the frame goes through the same chain, that is through the same filter instances, one block
after the other. Stateful filters (Butterworth) and the windows keep the shape of the first matrix they receive, so feed the
node frames with a single sensor block (or chains without such filters).

Main parameters:

- `configname` (`string`, default `filters`): the prefix of the chain parameters
- `definitionsname` (`string`, default `filters`): the prefix under which the filters are *defined* (class and
  parameters), when it must differ from the one of the chain; a filter whose `class` (or whose parameters) are not found under
  it is looked up under `configname`, so by default the chain prefix is used
- `input_topic` (`string`, default `/neurodata`)
- `output_topic` (`string`, default `~/filtered`)

## Configuration Format

In ROS2 the chain is configured with flattened parameters. The root prefix is selected by `configname`. The ordered list of filters
is read from `<configname>.filters` (or from `<configname>.chain`, which is accepted as well), and every filter `<name>` is
configured by the parameters under `<configname>.<name>.*`, with `<configname>.<name>.class` giving its plugin class. The examples
below set `configname` explicitly; without it the prefix is `filters`.

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
