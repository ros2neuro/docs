# Manager

!!! info ""
    Package: [`ros2neuro_manager`](https://github.com/ros2neuro/ros2neuro_manager)

The manager runs the **trials** of a calibration or an evaluation. It writes the phases of every trial (Start, Fixation, cue,
CFeedback...) on the event bus and listens to the same bus, where [`ros2neuro_control_feedback`](../control/feedback.md) writes
the outcome (Hit / Miss / Timeout): that is what ends the continuous feedback and lets the manager go on with the next trial.
It does not read the integrator, does not reset it and does not talk to the feedback: that is the [control](../control/index.md)
layer. The core is shared by all protocols; the protocol itself is a **plugin that you must select** with the parameter `plugin`.

The manager reads only its own parameters. What it shares with [`ros2neuro_control_feedback`](../control/feedback.md) and
[the feedback](../feedback/index.md) (the `classes`, the `rest_mode`, the ids of the events) is **the same parameter in each of the
three**, written once for every node (a `/**` section of the parameter file, see [Shared parameters](../../concepts/shared-parameters.md)):
nobody asks the manager for anything, and there is no code shared between the three. The thresholds are the only thing it does not
know: they are control's. See [Protocols](../../concepts/protocols.md) for the concepts behind them.

## What is in this menu

| Page | What you find |
|---|---|
| [Base class: `ros2neuro_manager`](base.md) | the node, its topics and parameters, the plugin interface and how to write a new plugin |
| [Available plugins](#available-plugins) | the plugins of the family, each with its own page |

## Available plugins

| Plugin | pluginlib class | Protocol |
|---|---|---|
| [Synchronous](synchronous.md) | [`ros2neuro::manager::Synchronous`](synchronous.md) | calibration and evaluation: random order of the trials, Start, Fixation, cue, CFeedback, waits for the outcome |
| [Asynchronous](asynchronous.md) | [`ros2neuro::manager::Asynchronous`](asynchronous.md) | free control: no trials, writes no event (the reset at the threshold is in [`ros2neuro_control_feedback`](../control/feedback.md)) |
