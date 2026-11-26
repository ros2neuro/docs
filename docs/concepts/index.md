# Concepts

How ROS2neuro is put together, before any package or command. The six pages are written to be read **in this order**: first the picture of the whole, then the mechanism that makes the pieces interchangeable (plugins), then what travels between them (messages and topics), then the layer that runs an experiment (protocols and shared parameters).

## What is in this menu

| Page | The question it answers | Read it to... |
|---|---|---|
| [Architecture](architecture.md) | what are the pieces and how do they fit in a loop? | get the whole picture: the signal chain, control, manager, feedback and the recorder |
| [Plugins](plugins.md) | how can I swap the amplifier, a filter or a decoder with a parameter? | understand the families, the base packages and the plugin packages |
| [Messages and data types](messages.md) | what do the nodes say to each other? | know `NeuroFrame`, `NeuroFeature`, `NeuroPrediction`, `NeuroControl`, `NeuroEvent` and their layout |
| [Topics and services](topics.md) | on which topic does each node publish, and what can I call? | read the default names and the `ros2` commands to inspect them |
| [Protocols: control, manager, feedback](protocols.md) | how does a calibration, an evaluation or a free control run? | learn the trials, the events, the thresholds and the reset |
| [Shared parameters](shared-parameters.md) | which values must be the same in several nodes? | write one parameter file for manager, control and feedback |

## Where to go from here

| If you want to... | Go to |
|---|---|
| install and run something | [Installation](../installation/index.md), then the [tutorials](../tutorials/index.md) |
| read about one package or plugin | [Packages](../packages/index.md) |
| write your own plugin | [Plugins](plugins.md#anatomy-of-a-plugin-package), then the tutorials of [Extending the stack](../tutorials/index.md#extending-the-stack) |
| check that a stage gives the numbers it should | [Reproducibility](../reproducibility/index.md) |
