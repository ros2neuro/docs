# Feedback

!!! info ""
    Package: [`ros2neuro_feedback`](https://github.com/ros2neuro/ros2neuro_feedback)

The feedback is **passive**: it makes no decisions. It reads only the manager's control topic and draws what it
finds there. The drawing is a **plugin that you must select** with the parameter `plugin`.

It rebuilds the same layout as the manager from the same parameters (`classes`, `rest_mode`, `thresholds`), so
declare them once and load them in both nodes.

## Available plugins

| Plugin | pluginlib class | Drawing |
|---|---|---|
| [Wheel](wheel.md) | `ros2neuro::feedback::Wheel` | a ring with a moving line, for exactly two classes |
| [Bar](bar.md) | `ros2neuro::feedback::Bar` | one bar per classifier output, with its own threshold line |

Both use [neurodraw](../neurodraw.md).

## Modes

- `mode: control`: values only.
- `mode: training`: values plus the trial phases (fixation, cue, boom).

## Minimal example

```yaml
/feedback:
  ros__parameters:
    plugin: ros2neuro::feedback::Bar
    mode: training
    control_topic: /manager_control/probabilities
    fps: 60.0
    window_title: "Bars"
```

Close the window with ESC to end the node.

## Writing a new drawing

Derive from `ros2neuro::feedback::FeedbackPlugin` (`set_values`, cue, fixation, boom) and export it against
`ros2neuro_feedback`. Keep the geometry in a pure, testable header, as `ros2neuro_feedback_bar` does with
`bar_geometry.hpp`.

---

## Reference (from the package README)

Passive core of the feedback: **no decisions**. It reads ONLY the manager's `control_topic` (never
`/neuroevent`): values, `seq`, phases (`event`) and the outcome (`outcome`). It rebuilds the same layout as the
manager from the same parameters (`classes`, `rest_mode` (`none` | `timeout` | `class`, default `none`), `thresholds`) and translates `fields` with the shared
function (`ros2neuro_manager` is used for headers only). Drawing is delegated to a pluginlib plugin
(`ros2neuro::feedback::FeedbackPlugin`): `ros2neuro_feedback_wheel`, `ros2neuro_feedback_bar`.

* `mode: control` (values only) | `training` (values + fixation, cue, boom).
* Before the first message the neutral vector (1/K) is drawn. Gaps in `seq` are logged.
* Cue = last class event; a rest in timeout that ends as a Hit is marked by the plugins with a small circle (`is_rest_timeout_hit()`); on a Miss the boom shows the class over its threshold (same rule as training),
  on a Timeout a neutral grey boom.
* The latency (message stamp -> drawing) is logged every `latency_log_period_s`.
* `publish_display_events` (default false): after drawing, publishes on `/neuroevent` `Shown + id` for the cue
  (class code), the boom (897/898/899) and the matching `+Off`, stamped after the drawing.
* Parameters: `plugin`, `mode`, `classes`, `rest_mode`, `thresholds`, `control_topic`, `event_topic`, `fps` (60),
  `publish_display_events`, `latency_log_period_s` (5), `window_title`. ESC in the window ends the node.

Writing a plugin: derive from `FeedbackPlugin`, register in a `plugins.xml` exported with
`pluginlib_export_plugin_description_file(ros2neuro_feedback plugins.xml)`.

Tests: `colcon test --packages-select ros2neuro_feedback` (the controller with a recording plugin).
