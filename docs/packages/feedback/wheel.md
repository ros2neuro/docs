# Wheel feedback

!!! info ""
    Package: [`ros2neuro_feedback_wheel`](https://github.com/ros2neuro/ros2neuro_feedback_wheel) · pluginlib class: `ros2neuro::feedback::Wheel` · part of [Feedback](index.md)

A feedback drawing for exactly two classes: a ring with a moving line that shows which class the classifier favours, threshold markers (any number), a cross, a cue circle and a coloured arc for the outcome. It is drawn with [`neurodraw`](neurodraw.md).

| | |
|---|---|
| **Layer** | Feedback |
| **Kind** | Plugin of [`ros2neuro_feedback`](index.md) (pluginlib class `ros2neuro::feedback::Wheel`) |
| **Reads** | the flow of [`ros2neuro_control_feedback`](../control/feedback.md) and the event bus, through the feedback node |
| **Publishes** | a window |
| **Run** | in the feedback YAML: `plugin: ros2neuro::feedback::Wheel` |
| **Depends on** | [`neurodraw`](neurodraw.md) |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_feedback`](index.md), [`neurodraw`](neurodraw.md)
- **External libraries**:
    - [`neurodraw`](neurodraw.md): the drawing library: SDL2 and OpenGL

## Messages and topics

Default node name: `feedback` (the node of [`ros2neuro_feedback`](index.md)).

Messages used:

- `NeuroControl` (the flow) and `NeuroEvent` (the event bus): read through the feedback node

## Example configuration

From the Gaussian pipeline of [`ros2neuro_devel_test`](../../reproducibility/packages/index.md) (`feedback/wheel/config/feedback_wheel.yaml`); the layout (`classes`, `rest_mode`, the ids of the events, the thresholds) is not a parameter of the plugin: the feedback core reads it from its own parameters (the same as the manager and control) and gives it to the plugin:

```yaml
# Feedback (wheel). It reads the event bus (the phases the manager writes, the outcome control writes) and the flow of control (values and
# thresholds). The classes, rest_mode and the initial thresholds are the same for every node: they come from layout.yaml (loaded by the launcher).
/feedback:
    ros__parameters:
        plugin: ros2neuro::feedback::Wheel
        control_topic: /control_feedback/probabilities    # the flow: values and thresholds (the phases come from event_topic)
        event_topic: /neuroevent                         # the phases of the trials and the outcome; also publish_display_events
        fps: 60.0
        window_title: "Gaussian - wheel"
        publish_display_events: false
        latency_log_period_s: 0.0                        # seconds between the "Latency stamp->draw" log lines; 0 = off
        angle_range: 180.0                               # wheel only
```

<!-- /interfaces -->
The build needs the [`neurodraw`](neurodraw.md) library: see the README of [`ros2neuro_feedback`](index.md) for how to install it.

## Behaviour

* Two active classes (`K == 2`): `output_classes[0]` on the left, `[1]` on the right; the position is the normalized
  value of the first. A rest next to two classes needs `rest_mode=timeout` (or `none`): with `rest_mode=class` it is one more output
  (K=3) and the layout is rejected; with `rest_mode=class` the rest can only be one of the two sides (see below).
* **Threshold markers: any number** (they follow the thresholds while running: `set_thresholds`, the number may change too). Values in (0, 1]:
  * as many as classes (2): written one per class as for the other feedbacks, both above 0.5 (`[0.7, 0.7]`: markers at 0.7 and 0.3,
    first class at `th0`, second at `1 - th1`); or already positions on the 0-1 axis, one above and one below 0.5 (`[0.3, 0.7]`).
    Both at or below 0.5 is refused;
  * any other number: positions on the 0-1 axis, as given (`[0.2, 0.3, 0.6, 0.7]`: four markers; 1 = fully left).

  The **outer** markers (the smallest and the largest position, the ones that can trigger something) have the color of the class of
  their side (above 0.5 the first class, blue; below it the second, red; exactly 0.5 grey); the **inner** ones are black. With two
  thresholds both are outer.
  The wheel only draws them: what they do (reset, outcome, a change of state) is decided by control. The flow carries them as
  `threshold:*` fields in the order of the list (`free_thresholds()` of the plugin: the core neither asks for K thresholds nor for K
  `threshold:<code>` fields).
* Colors as in the existing wheel: first class blue, second red; **the rest is always yellow**; timeout boom neutral grey.
  **The arc at the end of a trial** does not use the thresholds, only what the wheel knows: **Hit** = the color of the cue (the rest: yellow),
  **Miss** = the color of the other class (a rest has no other class: the side where the indicator is), **Timeout** = neutral grey.
  This holds with any number of thresholds, and only for the wheel (two classes): the bars, with more classes, do not work this way.
  **Rest** (yellow): with `rest_mode=timeout` it has a cue (yellow circle) and nothing else on the wheel; when it ends as a Hit
  (no threshold touched for `rest_timeout` seconds) the **arc turns yellow**, like the arc takes the color of the class
  reached on any hit (no extra dots). With `rest_mode=class` the rest is a normal class, one of the two sides (e.g.
  `classes:=[783, 773]`), that only colors when it reaches its threshold; its **threshold marker is yellow** too (the other side
  keeps blue / red).
* Parameter `angle_range` (180).

Tests: `colcon test --packages-select ros2neuro_feedback_wheel` (geometry, no window).
