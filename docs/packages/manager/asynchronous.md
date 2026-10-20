# Asynchronous manager (Control)

!!! info ""
    Package: [`ros2neuro_manager_asynchronous`](https://github.com/ros2neuro/ros2neuro_manager_asynchronous) · pluginlib class: `ros2neuro::manager::Control` · part of [Manager](index.md)

Plugin `ros2neuro::manager::Control` of `ros2neuro_manager`: continuous control. It does **not** run the
game: no `/game/command`, no command map, no cooldown, no dead zone, no trial events.

* The core publishes every valid normalized vector on the flow (`/manager_control/probabilities`), so the feedback moves.
* The plugin compares each class with its own threshold (`thresholds`, K values). When a class reaches it
  (value >= threshold, highest wins) it calls `request_reset()` on the integrator (a service call). From then on the manager
  forwards and decides on nothing until the integrator's reset message (all values 1/K) arrives, so the same saturated value
  cannot trigger repeated resets; if it does not arrive within 1 s an error is logged and the session is shut down. See the manager README.
* Thresholds can be changed at runtime, validated (K values in (0, 1]):
  `ros2 param set /manager thresholds "[0.7, 0.7]"`. The feedback markers follow only the feedback's own parameters.
* With 783 in `classes` the plugin needs `rest_mode` set to `timeout` or `class` (default `none` is refused).
* Resets are only logged; nothing is published on `/neuroevent`.

```bash
ros2 launch ros2neuro_manager_asynchronous asynchronous.launch.xml
ros2 launch ros2neuro_manager_asynchronous asynchronous.launch.xml feedback_plugin:=ros2neuro::feedback::Bar \
    classes:="[773, 771, 783]" rest_mode:=class thresholds:="[0.6, 0.6, 0.6]"
```

Tests: `colcon test --packages-select ros2neuro_manager_asynchronous`.
