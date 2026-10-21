# Writing an integrator plugin

In this tutorial you write a new integrator for ROS2neuro, build it as a plugin package, test it, and run it in
the real [integrator node](../../packages/integrator/index.md).

An integrator turns the noisy stream of `NeuroPrediction` messages of the decoder into a smoother
`NeuroControl`. The [exponential integrator](../../packages/integrator/exponential.md) forgets the past with a
decaying weight. The one you write here, **MovingAverage**, uses a different rule: the output is the mean of the
last `window` predictions, and anything older counts for nothing.

**You will learn**

- the interface of an integrator (`configure`, `apply`, `reset`, runtime parameters);
- what the node does for you (topics, rejection, reset service) and what the plugin does;
- how to register, test and load the plugin.

**You need** a built ROS2neuro workspace and about 25 minutes. It helps to have done
[Writing a filter plugin](../filter-plugin/index.md), because the registration steps are the same.

The complete package is in the repository, under `docs/tutorials/integrator-plugin/tutorial_integrator_plugin/`,
and it is compiled by the CI of the repository.

## 1. Who does what

| The integrator node ([`ros2neuro_integrator`](../../packages/integrator/index.md)) | Your plugin |
|---|---|
| subscribes to `NeuroPrediction`, publishes `NeuroControl` | computes the integrated values from one prediction |
| holds the previous output when the input confidence is below `integrator.rejection` | says what the neutral state is after a reset |
| offers the `reset` service and resets on `integrator.reset_event` | forgets its history when `reset()` is called |
| loads the plugin by `integrator.type` and passes it `integrator.params.*` | reads its parameters in `configure()` |

The interface:

```cpp
class Integrator {
  public:
    virtual bool configure() = 0;                                   // read parameters
    virtual IntegrationResult apply(const NeuroPrediction&) = 0;     // one prediction in, state out
    virtual IntegrationResult reset(std::size_t class_count) = 0;    // back to the neutral state
    virtual rcl_interfaces::msg::SetParametersResult
        set_runtime_parameter(const rclcpp::Parameter&);             // optional, live parameter changes
};

struct IntegrationResult {
    std::vector<float> integrated;   // one value per class
    int32_t decision;                // index of the winning class, -1 if none
};
```

!!! note "After a reset the output is 1/K"
    Every reset must return the **neutral vector** with all values equal to `1/K`. The
    [manager](../../concepts/protocols.md#reset) waits for exactly that message to know that the reset
    happened.

## 2. Package layout

```text
tutorial_integrator_plugin/
├── CMakeLists.txt
├── package.xml
├── plugins.xml
├── include/tutorial_integrator_plugin/MovingAverage.h
├── src/MovingAverage.cpp
├── test/test_moving_average.cpp
└── config/integrator_moving_average.yaml
```

## 3. The header

```cpp title="include/tutorial_integrator_plugin/MovingAverage.h"
--8<-- "integrator-plugin/tutorial_integrator_plugin/include/tutorial_integrator_plugin/MovingAverage.h"
```

`using ros2neuro::integrator::Integrator::configure;` keeps the base-class overload
`configure(name, type, params, logger)` visible. The node calls that overload, and it in turn calls your
parameterless `configure()`.

## 4. The implementation

```cpp title="src/MovingAverage.cpp"
--8<-- "integrator-plugin/tutorial_integrator_plugin/src/MovingAverage.cpp"
```

Things to notice:

- **Parameters.** `getParam("window", window)` reads `integrator.params.window` (the node strips the
  `integrator.params.` prefix). `configure()` returns `false` for an invalid value and the node refuses to start.
- **State.** The plugin keeps the last `window` predictions in a `std::deque`. `apply()` pushes the new one,
  drops the oldest ones and returns the mean.
- **Validation.** `apply()` throws `std::runtime_error` for an empty prediction or a change in the number of
  classes. The node catches the exception and logs it.
- **Reset.** `reset(K)` clears the history and stores one neutral sample, so that the output is `1/K` for every
  class.
- **Runtime parameter.** `set_runtime_parameter()` lets you change the window while the node runs. It must
  reject unknown names and invalid values, as it does here.
- The last line exports the class: `PLUGINLIB_EXPORT_CLASS(Derived, ros2neuro::integrator::Integrator)`.

## 5. Register the plugin

```xml title="plugins.xml"
--8<-- "integrator-plugin/tutorial_integrator_plugin/plugins.xml"
```

The `name` is the string that users put in `integrator.type`.

```cmake title="CMakeLists.txt"
--8<-- "integrator-plugin/tutorial_integrator_plugin/CMakeLists.txt"
```

The key line is `pluginlib_export_plugin_description_file(ros2neuro_integrator plugins.xml)`: it registers your
`plugins.xml` with the package that loads integrators.

```xml title="package.xml"
--8<-- "integrator-plugin/tutorial_integrator_plugin/package.xml"
```

## 6. Test it

```cpp title="test/test_moving_average.cpp"
--8<-- "integrator-plugin/tutorial_integrator_plugin/test/test_moving_average.cpp"
```

The tests cover the four behaviours that matter: the mean over the window, old predictions leaving it, the
neutral vector after a reset and the rejection of an invalid parameter.

## 7. Build

From the root of your workspace:

```bash
colcon build --packages-select tutorial_integrator_plugin
colcon test  --packages-select tutorial_integrator_plugin
colcon test-result --verbose
source install/setup.bash
```

If the package lives outside `src/`, add its path: `colcon build --paths path/to/tutorial_integrator_plugin`.

## 8. Run it

```yaml title="config/integrator_moving_average.yaml"
--8<-- "integrator-plugin/tutorial_integrator_plugin/config/integrator_moving_average.yaml"
```

Start the node:

```bash
ros2 run ros2neuro_integrator integrator_node --ros-args \
  --params-file $(ros2 pkg prefix tutorial_integrator_plugin)/share/tutorial_integrator_plugin/config/integrator_moving_average.yaml
```

The log says `type='tutorial::integrator::MovingAverage'`. In a second terminal watch the output:

```bash
ros2 topic echo /integrated/raw --field values
```

In a third one send predictions for two classes. Four vote for the first class, then two for the second:

```bash
for p in "[0.9,0.1]" "[0.9,0.1]" "[0.9,0.1]" "[0.9,0.1]" "[0.1,0.9]" "[0.1,0.9]"; do
  ros2 topic pub --once /prediction ros2neuro_msgs/msg/NeuroPrediction \
    "{decoder: tut, fields: ['773','771'], values: $p, type: 2}"
done
```

The integrated values follow the mean of the last four predictions:

```text
[0.9, 0.1]   after the first four votes for class 1
[0.7, 0.3]   one vote for class 2 enters the window, one old vote leaves
[0.5, 0.5]   two votes for each class
```

Change the window while the node runs:

```bash
ros2 param set /integrator integrator.params.window 8
```

## Use it in a full pipeline

Replace the integrator parameters of a launch file, for example the ones of the
[`ros2neuro_devel_test`](../../packages/devel-test.md) launchers
(`launch/gaussian/config/integrator_exponential.yaml`), with `integrator.type:
tutorial::integrator::MovingAverage` and `integrator.params.window`. Keep `input_topic`, `output_topic`,
`event_topic` and `integrator.reset_event` as they are, because the [manager](../../packages/manager/index.md)
depends on them.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `Missing required parameter 'integrator.type'` | the YAML key is wrong or the node name in the file does not match the running node |
| the class cannot be loaded | the workspace is not sourced after the build, or `integrator.type` differs from `name` in `plugins.xml` |
| nothing is published | the node reads `/prediction` by default: set `input_topic` to your decoder output |
| `Prediction size changed` | a decoder publishes a different number of classes than before: call `reset` or restart the node |

## Exercises

1. Make the output a probability even when the input is not: normalise the mean so that it sums to 1.
2. Weight the window: give the latest prediction a larger weight than the oldest one (for example linearly).
3. Compare the behaviour with the [Buffer](../../packages/integrator/buffer.md) integrator on the same sequence of votes.

Next: [Power threshold event](../power-threshold-event/index.md).
