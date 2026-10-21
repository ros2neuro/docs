# Writing a filter plugin

In this tutorial you write a new filter for the ROS2neuro [filter chain](../../packages/filters/index.md), build it
as a plugin package, test it, and load it in a running chain.

The filter is called **Clip**: it limits every sample to the range `[-limit, +limit]`, which bounds the effect of
large artifacts on the filters that follow.

**You will learn**

- the interface a filter implements and how its parameters arrive;
- how a plugin is registered (`plugins.xml`, `PLUGINLIB_EXPORT_CLASS`, CMake);
- how to test a filter without ROS running;
- how to put the filter in a chain from a YAML file.

**You need** a built ROS2neuro workspace and about 20 minutes. Read
[Plugins](../../concepts/plugins.md) first if the pluginlib mechanism is new to you.

The complete package is in the repository, under `docs/tutorials/filter-plugin/tutorial_filter_plugin/`, and it is
compiled by the CI of the repository, so the code below is the code that builds.

## 1. How a filter works

The chain gives every `NeuroFrame` to each filter as a matrix of floats shaped `[samples x channels]`, and the
filter returns a matrix of the same shape. A filter derives from [`ros2neuro::filters::Filter<float>`](../../packages/filters/index.md) and
implements two methods:

| Method | Called | Job |
|---|---|---|
| `bool configure()` | once | read the parameters of this filter with `getParam`, return `false` if they are invalid |
| `DynamicMatrix<T> apply(const DynamicMatrix<T>& input)` | for every frame | transform the data |

`DynamicMatrix<T>` is an Eigen dynamic matrix. A filter must not change the dimensions of the data.

## 2. Package layout

```text
tutorial_filter_plugin/
├── CMakeLists.txt
├── package.xml
├── plugins.xml                      # registers the class for pluginlib
├── include/tutorial_filter_plugin/Clip.h
├── src/Clip.cpp                     # exports the class
├── test/test_clip.cpp
└── config/filter_chain_clip.yaml    # example chain
```

You can create it with `ros2 pkg create --build-type ament_cmake tutorial_filter_plugin`, then replace the generated
files with the ones below.

## 3. The filter

```cpp title="include/tutorial_filter_plugin/Clip.h"
--8<-- "filter-plugin/tutorial_filter_plugin/include/tutorial_filter_plugin/Clip.h"
```

Things to notice:

- The class is a **template** on the sample type, like the filters of the workspace, and the concrete type is
  created in the next step. `T` is `float` in a real chain.
- `getParam("limit", limit)` reads the parameter `limit` of **this** filter (the chain passes each filter only
  its own parameters, with the prefix removed). It returns `false` when the parameter is missing, so the default
  stays.
- `configure()` returns `false` for an invalid value. The chain then refuses to start, which is better than
  silently running with a wrong setting.
- `apply()` is a one-liner with Eigen. Keep it free of allocations when you can: it runs on every frame.

## 4. Register the class

```cpp title="src/Clip.cpp"
--8<-- "filter-plugin/tutorial_filter_plugin/src/Clip.cpp"
```

`PLUGINLIB_EXPORT_CLASS(Derived, Base)` makes the class creatable by the class loader. The base class must be
exactly the one the chain loads, [`ros2neuro::filters::Filter<float>`](../../packages/filters/index.md).

```xml title="plugins.xml"
--8<-- "filter-plugin/tutorial_filter_plugin/plugins.xml"
```

- `path` is the library built by the package (the `add_library` name).
- `name` is what users write in the YAML (`tutorial_filter_plugin/ClipFloat`).
- `type` is the C++ class, `base_class_type` the interface (with `<` and `>` escaped).

## 5. Build files

```xml title="package.xml"
--8<-- "filter-plugin/tutorial_filter_plugin/package.xml"
```

```cmake title="CMakeLists.txt"
--8<-- "filter-plugin/tutorial_filter_plugin/CMakeLists.txt"
```

The two lines that make this a plugin are the shared `add_library` and
`pluginlib_export_plugin_description_file(ros2neuro_filters plugins.xml)`: the second one tells
[`ros2neuro_filters`](../../packages/filters/index.md) where to find your `plugins.xml`.

## 6. Test it

A filter is plain C++, so it can be tested without a running ROS graph:

```cpp title="test/test_clip.cpp"
--8<-- "filter-plugin/tutorial_filter_plugin/test/test_clip.cpp"
```

The test calls the public `configure(name, type, params, logger)` of the base class, which is what the chain
does, and checks both the result and the rejection of an invalid limit.

## 7. Build

From the root of your workspace, with ROS 2 and the ROS2neuro workspace sourced:

```bash
colcon build --packages-select tutorial_filter_plugin
colcon test  --packages-select tutorial_filter_plugin
colcon test-result --verbose
source install/setup.bash
```

If the package lives outside `src/`, add its path: `colcon build --paths path/to/tutorial_filter_plugin`.

Check that the package is installed:

```bash
ros2 pkg prefix tutorial_filter_plugin
```

## 8. Use it in a chain

```yaml title="config/filter_chain_clip.yaml"
--8<-- "filter-plugin/tutorial_filter_plugin/config/filter_chain_clip.yaml"
```

The chain applies `dc` first (removes the offset of each channel) and then `clip`. The order of the list is the
order of execution. Run it on the synthetic acquisition, no hardware needed:

```bash
# terminal 1: a synthetic EEG source (16 channels, 512 Hz)
ros2 launch ros2neuro_acquisition_dummy dummy_acquisition.launch.py

# terminal 2: the chain with the new filter
ros2 run ros2neuro_filters filter_chain_node --ros-args \
  --params-file $(ros2 pkg prefix tutorial_filter_plugin)/share/tutorial_filter_plugin/config/filter_chain_clip.yaml \
  -r /neurodata:=/acquisition/neurodata
```

The chain logs `FilterChain configured. chain='clipchain'`. Now look at the output:

```bash
# terminal 3
ros2 topic echo /filter_chain/filtered --field sensors --once
```

The values never exceed `50.0`: the large excursions of the sinusoid are flat at the limit, for example

```text
data=[-22.26, -13.39, -4.22, 5.03, 14.18, 23.02, 31.33, 38.94, 45.67, 50.0, 50.0, 50.0, ...
```

You can also open the scope with `ros2 run ros2neuro_visualizer neuroviz` and select
`/filter_chain/filtered`.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `class ... does not exist` | the workspace is not sourced after the build, or the YAML class name differs from `name` in `plugins.xml` |
| the chain starts but nothing is published | the input topic: the chain reads `/neurodata`, remap it to your acquisition topic |
| `configure` fails | the parameter has the wrong type; `limit` must be a number (`50.0`) |

## Exercises

1. Add a parameter `mode` (`hard` or `soft`) and implement a soft clip with `tanh`.
2. Make `limit` a per-channel vector read with `getParam("limits", std::vector<double>&)`.
3. Read how [`ros2neuro_filters_butterworth`](../../packages/filters/butterworth.md) keeps a state between frames,
   and write a filter that needs one.

Next: [Writing an integrator plugin](../integrator-plugin/index.md).
