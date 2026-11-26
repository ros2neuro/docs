# ros2neuro_control: the node and the base class

!!! info ""
    Package: [`ros2neuro_control`](https://github.com/ros2neuro/ros2neuro_control)

The node and the plugin interface (the parent class) of the control family, with what is common to all its plugins. For what the family does and its list of plugins see the [overview](index.md); each plugin has its own page.

## Topics and services

| | Name (default) | Type |
|---|---|---|
| subscribes | `/integrated/raw` (`input_topic`) | `NeuroPrediction` |
| service client | `/reset` (`reset_service`) | `std_srvs/Empty` |

The control node itself writes nothing. The plugin creates the rest on the same node: [`ros2neuro_control_feedback`](feedback.md) publishes the flow of the
feedback and writes the end of the continuous feedback and the outcome (Hit / Miss / Timeout) on the event bus; the end of the
outcome is the manager's.

## Minimal example

```yaml
/control:
  ros__parameters:
    plugin: ros2neuro::control::Feedback
    protocol: evaluation
    input_topic: /integrated/raw
    reset_service: /reset
    control_topic: /control_feedback/probabilities
```

Complete launch files that run every protocol (the constant `PROTOCOL` at the top of each file) are in the `feedback/` folder of [`ros2neuro_devel_test`](../../reproducibility/packages/index.md).

## Writing a new control

Derive from `ros2neuro::control::Control` (`configure`, `on_prediction`, optionally `start` and `stop`), use only
`ControlContext` (`request_reset`, `flush_input`, `request_shutdown`, `now`, `ok`) and the node you are given, and export it with
`PLUGINLIB_EXPORT_CLASS` and `pluginlib_export_plugin_description_file(ros2neuro_control plugins.xml)`.

---

## Reference (from the package README)

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, `std_srvs`, [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)
- **At run time**: a control plugin package

## Messages and topics

Default node name: `control`.

| | Default topic | Type | Changed by |
|---|---|---|---|
| subscribes | `/integrated/raw` | `NeuroPrediction` | `input_topic` |

| | Service | Type | Note |
|---|---|---|---|
| calls | `/reset` | `std_srvs/Empty` | `reset_service`: the reset service of the integrator (relative name `reset` at the root) |

Messages used:

- `NeuroPrediction`: read (the type of the input of every control)
- `std_srvs/Empty`: the reset of the integrator

<!-- /interfaces -->
## How it works

`control_node` loads one plugin (parameter `plugin`) and, for every `NeuroPrediction` that arrives on `input_topic`, calls
`Control::on_prediction()`. The plugin gets a `ControlContext` with what the node offers:

| Method | What it does |
|---|---|
| `now()`, `ok()` | clock of the node, `rclcpp::ok()` |
| `request_shutdown(failed)` | stops the node; `failed = true` makes the process exit with code 1 |
| `request_reset()` | calls the `reset` service of the integrator, asynchronously. `false` (nothing done) if the service is not up |
| `reset_pending()` | `true` from an accepted `request_reset()` until the integrator has answered it (it answers once it has reset). A plugin that must not use values of before the reset waits for `false`, then takes only the values stamped after its request (what [`ros2neuro_control_feedback`](feedback.md) does). Default `false` for contexts that do not track it |
| `flush_input()` | throws away the messages that the input subscription has queued and the node has not delivered yet (for example the values published before a reset) |

The plugin reads its own parameters from the node it is given and may create publishers, subscriptions and timers on it:
the node is the only thing it needs.

## Parameters

| Parameter | Default | Meaning |
|---|---|---|
| `plugin` | (required) | pluginlib class of the control plugin, for example [`ros2neuro::control::Feedback`](feedback.md) |
| `input_topic` | `/integrated/raw` | the `NeuroPrediction` topic of the integrator |
| `reset_service` | `/reset` | the reset service of the integrator |

## Writing a plugin

Derive from `ros2neuro::control::Control` (`include/ros2neuro_control/control.hpp`) and implement:

- `configure(node, context)`: read the parameters from `node`, return `false` if they are invalid;
- `on_prediction(prediction)`: called for every message of the integrator, from the executor thread: it must return quickly;
- optionally `start()` (once, after `configure()`, before the node spins) and `stop()` (before the plugin is released).

Export the class with `PLUGINLIB_EXPORT_CLASS(Derived, ros2neuro::control::Control)`, describe it in a `plugins.xml` and
register that file with `pluginlib_export_plugin_description_file(ros2neuro_control plugins.xml)`. A plugin that holds the
`shared_ptr` of the node must let it go in its destructor: the node calls `release_plugin()` before exiting.

## A control for a robot (custom)

`ros2neuro_control_robot` does not exist in the stack: it is **custom** and each robot needs its own. To write one:

1. derive from `ros2neuro::control::Control`: the input is a `NeuroPrediction` (the integrator output) in `on_prediction()`;
2. from there it can do whatever it wants with it: map it to a command, compare it with its own thresholds, call `request_reset()`...;
3. export it as a plugin and select it with `plugin:=<your class>` of `control_node`.

A robot control and [`ros2neuro_control_feedback`](feedback.md) are two plugins on **two** control nodes, both reading the same `/integrated/raw`.
If the robot has to move in step with what the subject sees on the feedback, they have to be **synchronized**: write a node that
looks at the **header** of the messages of the two (the flow of the feedback, `NeuroControl`, and whatever the robot control
publishes). The header of both comes from the integrator message they are made from, so the stamps of the two streams are the
same for the same prediction: the synchronization node pairs the messages with equal stamp (for example with
`message_filters::ApproximateTimeSynchronizer` or an exact-time policy) and acts on the pair. The stack does not ship that node.
