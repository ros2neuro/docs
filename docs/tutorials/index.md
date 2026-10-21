# Tutorials

Step-by-step guides. Each tutorial has its explanation and its code **in the same folder**, and the code is a
real ROS 2 package that is compiled and tested by the CI of this repository, so what you read is what builds.

| # | Tutorial | You will learn | Code |
|---|---|---|---|
| 1 | [Running the whole pipeline without hardware](hardware-free-pipeline/index.md) | start a full pipeline from a GDF file to the feedback, inspect nodes, topics and events | none |
| 2 | [Looking at the signals with the visualizer](visualizer/index.md) | show the EEG filtered between 2 and 40 Hz and its Welch spectrum, side by side, and the trigger lines | `acquisition_gdf.yaml` |
| 3 | [Writing a filter plugin](filter-plugin/index.md) | the filter interface, plugin registration, a unit test, loading it in the chain | `tutorial_filter_plugin` |
| 4 | [Writing an integrator plugin](integrator-plugin/index.md) | the integrator interface, state and reset, runtime parameters | `tutorial_integrator_plugin` |
| 5 | [Raising an event when a channel power crosses a threshold](power-threshold-event/index.md) | read a `NeuroFrame`, compute power, hysteresis, publish a `NeuroEvent` aligned with the data | `tutorial_power_threshold` |
| 6 | [Checking the EOG with frontal channels](eog-check/index.md) | detect eye blinks on Fp1 and Fp2 and publish them as events | `tutorial_eog_check` |
| 7 | [Showing the feedback in virtual reality](vr-feedback/index.md) | send the manager's flow to a WebXR page (tested) and to Unity (example) through rosbridge | `webxr/`, `unity/` |

## Prerequisites

- A built ROS2neuro workspace on ROS 2, sourced:

  ```bash
  source /opt/ros/<distro>/setup.bash
  source install/setup.bash
  ```

- Basic ROS 2 knowledge: nodes, topics, parameters, `colcon`.
- The [Concepts](../concepts/architecture.md) section, in particular [Messages](../concepts/messages.md) and
  [Plugins](../concepts/plugins.md).

No tutorial needs hardware: they all run on the synthetic acquisition, on a replayed GDF file or on the small
simulator that comes with the tutorial.

## Building a tutorial package

Every tutorial package is an ordinary ROS 2 package. Put it in the `src/` folder of your workspace (or point
`colcon` to it) and build it:

```bash
colcon build --packages-select tutorial_filter_plugin
colcon test  --packages-select tutorial_filter_plugin
source install/setup.bash
```

```bash
# from anywhere, without copying the package into the workspace
colcon build --paths path/to/docs/tutorials/filter-plugin/tutorial_filter_plugin
```

## Conventions

- Tutorial packages are called `tutorial_*` so they never clash with the packages of the stack.
- The logic that does not need ROS (detectors, power, filters' maths) is in a header that is tested on its own;
  the node is a thin layer around it. Follow the same pattern in your packages.
- Events published by your own nodes should use ids that do not collide with the ones the stack reserves (see
  [Protocols](../concepts/protocols.md#event-codes)).
