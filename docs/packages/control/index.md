# Control

!!! info ""
    Package: [`ros2neuro_control`](https://github.com/ros2neuro/ros2neuro_control)

The control layer acts on the output of the integrator. It is where the **thresholds** are known, so it is where the decisions
are taken. The package provides the parent class `ros2neuro::control::Control` (the input of every control is a
`NeuroPrediction`) and `control_node`, which loads the plugin you select with the parameter `plugin`. A control plugin can
**reset the integrator**.

!!! important "Select one plugin"
    Set `plugin` to one of the classes below.

## What is in this menu

| Page | What you find |
|---|---|
| [Base class: `ros2neuro_control`](base.md) | the node, its topics and parameters, the plugin interface and how to write a new plugin |
| [Available plugins](#available-plugins) | the plugins of the family, each with its own page |

## Available plugins

| Plugin | pluginlib class | What it controls |
|---|---|---|
| [Feedback](feedback.md) | [`ros2neuro::control::Feedback`](feedback.md) | the feedback window (wheel, bars): calibration with autopilot, evaluation, free control |
| `ros2neuro_control_robot` (custom, not in the stack) | | a robot: you write it, see [A control for a robot](base.md#a-control-for-a-robot-custom) |
