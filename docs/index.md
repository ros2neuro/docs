![ROS2neuro](assets/logo.png){ .home-logo }

# ROS2neuro

**ROS2neuro** is a modular C++ framework for real-time neurophysiological signal acquisition, processing,
decoding and closed-loop Brain-Computer Interface (BCI) applications, built on **ROS 2**.

Every stage of the pipeline is a ROS 2 node whose behaviour is chosen at launch time by loading a **plugin**:
the amplifier, the filters, the decoder, the integrator, the recorder, the protocol and the feedback are all
interchangeable pieces that talk through a small set of messages.

## The loop

[![The ROS2neuro loop](assets/fig_loop.png)](assets/fig_loop.png)

The **signal chain** (acquisition, filters, features, decoder, integrator) turns the amplifier signal into class probabilities. **Control**
decides what to do with them (thresholds, outcome of a trial, reset of the integrator) and sends the values to the **feedback**, which the subject
sees: that closes the loop. The **manager** runs the trials of an experiment and writes their phases on an event bus, which the recorder stores
next to the signal. The dashed boxes are extensions that are not part of the stack: the *Robot Control* is **your** plugin, to drive a robot.
Click the figure to enlarge it; it is explained in [Architecture](concepts/architecture.md).

## The plugins

[![The plugin families of ROS2neuro](assets/fig_plugins.png)](assets/fig_plugins.png)

Every colour is a **family**: a package that defines a base class, and under it the plugins available (the amplifier, the filters, the decoder, the
integrator, the recorder, the control, the protocol, the drawing). You pick one with a parameter and nothing else changes. The package of every family
is written in its header; see [Plugins](concepts/plugins.md) for the classes and how to write your own.

!!! info "Which BCIs"
    ROS2neuro has been tested with motor imagery (MI). It should work for any BCI paradigm: the processing stage has no
    fixed implementation, so other paradigms, such as the exogenous SSVEP or P300, can be supported by writing your own processing node:
    see [Processing](packages/processing/index.md).

!!! info "Tested on ROS 2 Jazzy"
    All of ROS2neuro was built and tested on **ROS 2 Jazzy** (Ubuntu 24.04), and the Debian packages are built for it:
    see [Installation](installation.md). The commands in this documentation use `jazzy`; other releases have not been tested.

## Where to start

<div class="grid cards" markdown>

-   **[Concepts](concepts/architecture.md)**

    How ROS2neuro is organised: the architecture, the messages and their data types, the topics, the plugin
    mechanism and the protocol layer (control, manager and feedback).

-   **[Packages](packages/index.md)**

    One page per package and per plugin: what it does, which topics and parameters it has and how to use it.

-   **[Tutorials](tutorials/index.md)**

    Step-by-step guides with code that compiles: run a pipeline without hardware, write a filter or an
    integrator plugin, raise an event when a channel power crosses a threshold, check the EOG.

</div>

## The stack in one paragraph

Data flows from the hardware (or a GDF file) through the **acquisition**, the **filters** and the
**processing** (a Welch spectrum for the classic classifiers, a window of the signal for the deep-learning ones), is
classified by a **decoder** and smoothed by an **integrator**. **Control** knows the
thresholds: it drives a passive **feedback**, decides the outcome of the trials and resets the integrator. A **manager**
runs the trials of a calibration or an evaluation and writes their events. A **recorder** writes everything to GDF/BDF and a **visualizer** shows the signals.

## Conventions used in this documentation

- Package names are written as in the workspace ([`ros2neuro_filters`](packages/filters/index.md)), plugin classes with their full
  pluginlib name ([`ros2neuro::acquisition::XDFDevice`](packages/acquisition/xdf.md)).
- Commands assume a sourced ROS 2 environment (`source /opt/ros/jazzy/setup.bash`) and ROS2neuro installed, from apt or from a workspace (`source install/setup.bash`): see [Installation](installation.md).
- Parameters are shown in YAML (`ros__parameters`), the way they are normally passed to a node.
