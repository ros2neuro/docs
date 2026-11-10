# Asynchronous manager (Asynchronous)

!!! info ""
    Package: [`ros2neuro_manager_asynchronous`](https://github.com/ros2neuro/ros2neuro_manager_asynchronous) · pluginlib class: `ros2neuro::manager::Asynchronous` · part of [Manager](index.md)

Plugin `ros2neuro::manager::Asynchronous` of [`ros2neuro_manager`](index.md): continuous control. It does **not** run the game: no trials, no
cues, no events. There is nothing for the manager to write here: the feedback follows the values of the integrator, and
the thresholds and the reset of the integrator belong to the control layer ([`ros2neuro_control`](../control/index.md), plugin
[`ros2neuro_control_feedback`](../control/feedback.md), protocol `control`), which is the node that knows the thresholds.

The plugin exists so that every protocol is launched the same way (a manager node with a plugin); it logs one line and writes nothing.

| | |
|---|---|
| **Layer** | Manager (protocol) |
| **Kind** | Plugin of [`ros2neuro_manager`](index.md) (pluginlib class `ros2neuro::manager::Asynchronous`) |
| **Reads** | nothing (it only hears the bus, through the manager node) |
| **Publishes** | nothing |
| **Run** | `ros2 launch ros2neuro_manager_asynchronous asynchronous.launch.xml` (together with [`ros2neuro_control_feedback`](../control/feedback.md), `protocol:=control`) |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_manager`](index.md), [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)
- **ROS 2 packages** (run only): [`ros2neuro_control_feedback`](../control/feedback.md), [`ros2neuro_feedback`](../feedback/index.md), [`ros2neuro_feedback_wheel`](../feedback/wheel.md), [`ros2neuro_feedback_bar`](../feedback/bar.md)

## Messages and topics

Default node name: `manager` (the node of [`ros2neuro_manager`](index.md)). The plugin publishes and reads nothing by itself.

## Example configuration

The control protocol of the Gaussian pipeline of [`ros2neuro_devel_test`](../devel-test.md) (`config/protocol_control.yaml`, `/manager` part; the
`/control` part is for [`ros2neuro_control_feedback`](../control/feedback.md); the layout, with the thresholds, is in `layout.yaml`):

```yaml
/manager:
    ros__parameters:
        plugin: ros2neuro::manager::Asynchronous
        event_topic: /neuroevent
```

<!-- /interfaces -->
What happens in control, and where:

* [`ros2neuro_control_feedback`](../control/feedback.md) (`protocol: control`) forwards every normalized vector of the integrator to the feedback.
* It compares each class with its own threshold. When a class reaches it (value >= threshold, highest wins) it asks the integrator for
  a reset through the control node, and waits for the integrator's neutral message (all values 1/K) before forwarding again; no
  message within 1 s -> error and the session is shut down. Thresholds can be changed at runtime:
  `ros2 param set /control thresholds "[0.7, 0.7]"`.
* Nothing is written on `/neuroevent`.

```bash
ros2 launch ros2neuro_manager_asynchronous asynchronous.launch.xml
ros2 launch ros2neuro_control_feedback control_feedback.launch.xml protocol:=control
```

Tests: `colcon test --packages-select ros2neuro_manager_asynchronous` (`test_asynchronous_plugin`: the plugin loaded by the manager node writes nothing on the bus).
