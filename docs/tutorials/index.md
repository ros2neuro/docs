# Tutorials

Step-by-step guides. Each tutorial has its explanation and its code **in the same folder**, and the code is a
real ROS 2 package that you can build and test yourself (see below). The code shown in each page is included from that package, so what you read is what builds.

## What is in this menu

The tutorials are in three groups, to be followed **in order**. Each page says its goal first and builds its files one piece at a time.

| Group | Goal | Tutorials |
|---|---|---|
| [Start here](#start-here) | **run a whole pipeline from zero**: learn the ROS 2 you need, start the pieces one by one, chain them and run the complete pipeline | 1-8 |
| [Your first BCI programs](#your-first-bci-programs) | write small programs of your own on top of the stack: a band power, a feedback window, a blink detector, and a second complete pipeline with a deep-learning model | 9-12 |
| [Extending the stack](#extending-the-stack) | write C++ for the stack: filter and integrator plugins, events from a power threshold, feedback in virtual reality, a robot | 13-17 |

## Start here

They follow the path of the [ROS-Neuro tutorials](https://sites.google.com/view/ros-neurotutorial/ros-neuro-tutorial) of the ROS 1 version, rewritten for ROS 2 and for ROS2neuro (see the table at the end). The first tutorials need no code of your own: you learn the ROS 2 you need, then you start the pieces of the stack and check them. The **goal** of the group is the last two: build the whole pipeline step by step (7) and run the complete one with the manager, control and feedback (8).

| # | Tutorial | You will learn | Code |
|---|---|---|---|
| 1 | [ROS 2 essentials: nodes, topics and launch files](ros2-basics/index.md) | nodes, topics, services, parameters, launch files and the `ros2` commands to inspect them | none |
| 2 | [Your first publisher and subscriber](publisher-subscriber/index.md) | the smallest nodes that talk: a talker and a listener, built and launched | `tutorial_pubsub` |
| 3 | [Acquire, view and record the EEG](acquisition-recording/index.md) | the acquisition node and its YAML, the visualizer, the recorder, a launch file for the three | `tutorial_signal_chain` |
| 4 | [View the signals in the visualizer](visualizer/index.md) | show the EEG filtered between 2 and 40 Hz and its Welch spectrum, side by side, and the trigger lines | `acquisition_gdf.yaml` |
| 5 | [Build a filter chain](filter-chain/index.md) | write a chain in YAML, start it, remap its topics, check it in the visualizer | `tutorial_signal_chain` |
| 6 | [Run several filter chains in parallel](multiple-chains/index.md) | the same node started twice (two bands), chains in parallel and in series | `tutorial_signal_chain` |
| 7 | [Build the whole pipeline step by step](full-pipeline/index.md) | acquisition, filters, spectrum, decoder and integrator in one launch file, checked stage by stage | `tutorial_signal_chain` |
| 8 | [Run the complete pipeline without hardware](hardware-free-pipeline/index.md) | the ready-made pipeline with the manager, control and feedback; inspect nodes, topics and events | none |

## Your first BCI programs

| # | Tutorial | You will learn | Code |
|---|---|---|---|
| 9 | [Compute the band power of a channel](band-power/index.md) | square, moving average and logarithm of a band-passed channel, in a node with tested maths | `tutorial_band_power` |
| 10 | [A feedback window that follows the band power](feedback-gui/index.md) | a window with a bar that follows the band power of a channel (Python, tkinter) | `tutorial_feedback_gui` |
| 11 | [Detect eye blinks (EOG)](eog-check/index.md) | detect eye blinks on Fp1 and Fp2 and publish them as events | `tutorial_eog_check` |
| 12 | [A complete pipeline with a deep-learning model](dl-pipeline/index.md) | the same chain with a Buffer and a ShallowNet instead of a Welch and a Gaussian: what changes and what does not | `dl_pipeline.launch.py` and its yaml |

## Extending the stack

From here you write C++ for the stack: plugins and nodes of your own.

| # | Tutorial | You will learn | Code |
|---|---|---|---|
| 13 | [Write a filter plugin](filter-plugin/index.md) | the filter interface, plugin registration, a unit test, loading it in the chain | `tutorial_filter_plugin` |
| 14 | [Write an integrator plugin](integrator-plugin/index.md) | the integrator interface, state and reset, runtime parameters | `tutorial_integrator_plugin` |
| 15 | [Raising an event when a channel power crosses a threshold](power-threshold-event/index.md) | read a `NeuroFrame`, compute power, hysteresis, publish a `NeuroEvent` aligned with the data | `tutorial_power_threshold` |
| 16 | [Feedback in virtual reality (WebXR and Unity)](vr-feedback/index.md) | send the flow of the feedback to a WebXR page (tested) and to Unity (example) through rosbridge | `webxr/`, `unity/` |
| 17 | [Control a robot in sync with the feedback](robot-control/index.md) | write a control plugin for a robot (it takes a `NeuroPrediction`) and a node that synchronizes it with the feedback by the header of the messages | `tutorial_robot_control` |

## Where the ROS-Neuro tutorials went

| ROS-Neuro tutorial (ROS 1) | Here |
|---|---|
| A) Setup the virtual machine | [Installation](../installation/index.md): the apt packages or a [container](../installation/container.md) replace the virtual machine |
| B) Gentle introduction to ROS | [1. ROS 2 essentials](ros2-basics/index.md) |
| C) ROS publishers and subscribers | [2. Your first publisher and subscriber](publisher-subscriber/index.md) |
| 1) Acquisition, visualization and recording | [3. Acquire, view and record the EEG](acquisition-recording/index.md) and [4. The visualizer](visualizer/index.md) |
| 2) EEG filtering | [5. Build a filter chain](filter-chain/index.md) and [6. Several chains](multiple-chains/index.md) |
| 3) A simple blink detector | [11. Detect eye blinks (EOG)](eog-check/index.md) |
| 4) Band power calculation | [9. Compute the band power of a channel](band-power/index.md) |
| 5) Creation of a simple feedback GUI | [10. A feedback window that follows the band power](feedback-gui/index.md) |

## Prerequisites

- A built ROS2neuro workspace on ROS 2, sourced:

  ```bash
  source /opt/ros/jazzy/setup.bash
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
