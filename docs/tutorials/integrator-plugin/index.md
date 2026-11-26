# Write an integrator plugin

A decoder says, for every window of EEG, *"90 % hands, 10 % feet"*, and the next window may say the opposite. Nobody moves a cursor with a signal that jumps like that: the
**integrator** turns the noisy stream of `NeuroPrediction` messages of the decoder into a smoother `NeuroPrediction` (`type = TYPE_SCORES`). The
[exponential integrator](../../packages/integrator/exponential.md) forgets the past with a decaying weight. In this tutorial you write one with a different rule.

**Goal.** Write an integrator called **MovingAverage**: the output is the mean of the last `window` predictions, and anything older counts for nothing. Build it as a plugin package,
test it, run it in the real [integrator node](../../packages/integrator/index.md), and **watch it vote** from the terminal.

**You will learn**

- the interface of an integrator (`configure`, `apply`, `reset`, runtime parameters);
- what the node does for you (topics, rejection, reset service) and what the plugin does;
- how to register, test and load the plugin.

**You need** the [filter plugin tutorial](../filter-plugin/index.md), because the registration steps are the same, and a built ROS2neuro workspace. About 25 minutes.

The complete package is in the repository, under `docs/tutorials/integrator-plugin/tutorial_integrator_plugin/`. The page includes its files, so the code below is the code that builds.

## 1. The plan

The node does everything except the maths. You write only that:

| The integrator node ([`ros2neuro_integrator`](../../packages/integrator/index.md)) | Your plugin |
|---|---|
| subscribes to `NeuroPrediction`, publishes a `NeuroPrediction` of type `TYPE_SCORES` | computes the integrated values from one prediction |
| holds the previous output when the input confidence is below `integrator.rejection` | says what the neutral state is after a reset |
| offers the `reset` service and resets on `integrator.reset_event` | forgets its history when `reset()` is called |
| loads the plugin by `integrator.type` and passes it `integrator.params.*` | reads its parameters in `configure()` |

The interface we implement:

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
    Every reset must return the **neutral vector** with all values equal to `1/K`. The [control](../../concepts/protocols.md#reset) waits for exactly that message to
    know that the reset happened.

The files:

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

## 2. The header

The header declares what the class overrides, and what it keeps: the window length and the last predictions in a `std::deque`.

```cpp title="include/tutorial_integrator_plugin/MovingAverage.h"
--8<-- "integrator-plugin/tutorial_integrator_plugin/include/tutorial_integrator_plugin/MovingAverage.h"
```

`using ros2neuro::integrator::Integrator::configure;` keeps the base-class overload `configure(name, type, params, logger)` visible. The node calls that overload, and it in turn calls
your parameterless `configure()`.

## 3. The implementation, step by step

**Read the parameter.** `getParam("window", window)` reads `integrator.params.window` (the node strips the `integrator.params.` prefix). An invalid value makes `configure()` return
`false` and the node refuses to start:

```cpp title="src/MovingAverage.cpp"
--8<-- "integrator-plugin/tutorial_integrator_plugin/src/MovingAverage.cpp:configure"
```

**Integrate one prediction.** Push the new prediction, drop the oldest ones, and return the mean. It throws `std::runtime_error` for an empty prediction or a change in the number
of classes: the node catches the exception and logs it.

```cpp
--8<-- "integrator-plugin/tutorial_integrator_plugin/src/MovingAverage.cpp:apply"
```

**The mean.** Sum the predictions of the window, divide by how many there are, and say which class wins:

```cpp
--8<-- "integrator-plugin/tutorial_integrator_plugin/src/MovingAverage.cpp:mean"
```

```cpp
--8<-- "integrator-plugin/tutorial_integrator_plugin/src/MovingAverage.cpp:trim"
```

**Reset.** Clear the history and store **one** neutral sample, so that the output is `1/K` for every class, as the note above requires:

```cpp
--8<-- "integrator-plugin/tutorial_integrator_plugin/src/MovingAverage.cpp:reset"
```

**A runtime parameter.** `set_runtime_parameter()` lets you change the window while the node runs. It must reject unknown names and invalid values, as it does here:

```cpp
--8<-- "integrator-plugin/tutorial_integrator_plugin/src/MovingAverage.cpp:runtime"
```

The last line of the file exports the class: `PLUGINLIB_EXPORT_CLASS(tutorial::integrator::MovingAverage, ros2neuro::integrator::Integrator)`.

??? example "The complete implementation"
    ```cpp
    --8<-- "integrator-plugin/tutorial_integrator_plugin/src/MovingAverage.cpp"
    ```

## 4. Register the plugin

```xml title="plugins.xml"
--8<-- "integrator-plugin/tutorial_integrator_plugin/plugins.xml"
```

The `name` is the string that users put in `integrator.type`.

```cmake title="CMakeLists.txt"
--8<-- "integrator-plugin/tutorial_integrator_plugin/CMakeLists.txt"
```

The key line is `pluginlib_export_plugin_description_file(ros2neuro_integrator plugins.xml)`: it registers your `plugins.xml` with the package that loads integrators.

```xml title="package.xml"
--8<-- "integrator-plugin/tutorial_integrator_plugin/package.xml"
```

## 5. Test it

Four behaviours matter: the mean over the window, old predictions leaving it, the neutral vector after a reset and the rejection of an invalid parameter.

```cpp title="test/test_moving_average.cpp"
--8<-- "integrator-plugin/tutorial_integrator_plugin/test/test_moving_average.cpp"
```

## 6. Build

From the root of your workspace:

```bash
colcon build --packages-select tutorial_integrator_plugin
colcon test  --packages-select tutorial_integrator_plugin
colcon test-result --verbose
source install/setup.bash
```

If the package lives outside `src/`, add its path: `colcon build --paths path/to/tutorial_integrator_plugin`.

## 7. Run it and watch it vote

The parameters: the plugin is chosen by `integrator.type`, and its own parameters are under `integrator.params.*`.

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

In a third one play the decoder: send predictions for two classes. Four vote for the first class, then two for the second:

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

Change the window while the node runs and send more votes to see the effect:

```bash
ros2 param set /integrator integrator.params.window 8
```

## 8. Use it in a full pipeline

The same plugin works in the pipeline of the [hardware-free tutorial](../hardware-free-pipeline/index.md). In the `config/` folder of the launcher you run (for example
`feedback/bars2/config/integrator_exponential.yaml` in [`ros2neuro_devel_test`](../../reproducibility/packages/index.md)) replace the type and the parameter of the plugin:

```yaml
        integrator.type: tutorial::integrator::MovingAverage
        integrator.params.window: 16
```

and keep `input_topic`, `output_topic`, `event_topic` and `integrator.reset_event` as they are, because [control](../../packages/control/index.md) reads that output and the trials
rely on the reset at every CFeedback. Rebuild `ros2neuro_devel_test` and launch again.

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

## What you learned

- an integrator is a class with `apply()` and `reset()`; the node does the topics, the rejection and the reset service;
- after a reset the output is always the neutral vector `1/K`;
- you can play the decoder from the terminal to test an integrator without any other node.

Next: [Detect a power threshold and publish an event](../power-threshold-event/index.md).
