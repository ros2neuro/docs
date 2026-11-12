# Bar feedback

!!! info ""
    Package: [`ros2neuro_feedback_bar`](https://github.com/ros2neuro/ros2neuro_feedback_bar) · pluginlib class: `ros2neuro::feedback::Bar` · part of [Feedback](index.md)

A feedback drawing with one bar per classifier output, so it works with any number of classes: each bar has its own colour and a white threshold line, and lights up when its threshold is reached. It is drawn with [`neurodraw`](neurodraw.md).

| | |
|---|---|
| **Layer** | Feedback |
| **Kind** | Plugin of [`ros2neuro_feedback`](index.md) (pluginlib class `ros2neuro::feedback::Bar`) |
| **Reads** | the flow of [`ros2neuro_control_feedback`](../control/feedback.md) and the event bus, through the feedback node |
| **Publishes** | a window |
| **Run** | in the feedback YAML: `plugin: ros2neuro::feedback::Bar` |
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

From the Gaussian pipeline of [`ros2neuro_devel_test`](../devel-test.md) (`config/feedback_bars.yaml`); the layout (`classes`, `rest_mode`, the ids of the events, the thresholds) is not a parameter of the plugin: the feedback core reads it from its own parameters (the same as the manager and control) and gives it to the plugin:

```yaml
# Feedback (bars). It reads the event bus (the phases the manager writes, the outcome control writes) and the flow of control (values and
# thresholds). The classes, rest_mode and the initial thresholds are the same for every node: they come from layout.yaml (loaded by the launcher).
/feedback:
    ros__parameters:
        plugin: ros2neuro::feedback::Bar
        control_topic: /control_feedback/probabilities    # the flow: values and thresholds (the phases come from event_topic)
        event_topic: /neuroevent                         # the phases of the trials and the outcome; also publish_display_events
        fps: 60.0
        window_title: "Gaussian - bars"
        publish_display_events: false
        latency_log_period_s: 0.0                        # seconds between the "Latency stamp->draw" log lines; 0 = off
```

<!-- /interfaces -->
The build needs the [`neurodraw`](neurodraw.md) library: see the README of [`ros2neuro_feedback`](index.md) for how to install it.

## Behaviour

* One bar per classifier output, in the order of `output_classes`, **each with its own color** (royalblue, firebrick,
  forestgreen, mediumpurple, deeppink, darkcyan, saddlebrown; none is yellow: yellow is always the rest). There are no
  labels: the colors tell the bars apart, and the order is the one of the `classes` parameter. With two bars they are
  blue and red, like the wheel.
* **Same unit scale for every bar**: the frame is the interval [0, 1], the fill is the normalized value, so all the bars
  start at the same level, 1/K, and when one rises the others fall.
* **Threshold**: a white line across each bar at the value of *its own* threshold on that same scale (`thresholds[i]` for
  the i-th bar).
* **Threshold reached**: while the value of a bar is at or above its threshold (same rule as the outcomes) the bar and its
  threshold line light up: **the same color, only brighter** (the three RGB channels are scaled by the same factor, so hue and
  saturation do not change; the base brightness of the bars is capped at 78% so the difference is always visible) and the
  line becomes thicker. A bar never takes another color: on a miss the target keeps its own and the bar that was reached
  is the one that lights up.
  (The thresholds come in the flow of control and are followed while running: after `ros2 param set /control thresholds ...` the lines move.)
* **Fixation cross and cue always in the same place**: centred under the bars, whatever the target. The bars are always
  there. The cue has the color of the target's bar (a rest in timeout, which has no bar, is yellow).
* **No circle for a Hit or a Miss**: the outcome is the bar that was reached lighting up, and a bar never takes the color of another class.
* **Timeout**: when the trial ends without any bar reaching its threshold (the Timeout of an evaluation) **every bar keeps its color but paler** (the same color mixed with white) until the boom
  ends (`duration.boom` of the manager), and then goes back to its own color: the trial is over and nothing was reached. It is the same idea as the arc of the wheel, which goes to the background. The paler
  color is different from the vivid color of a bar that reached its threshold, so the two cannot be confused. How pale it is: `kTowardsWhite` in `faded_color()` (`src/bar_geometry.cpp`, 0.25).
* **The rest in timeout that is a Hit**: a rest with **`rest_mode=timeout`** that ends without touching a threshold for `rest_timeout` seconds (see the `ros2neuro_control_feedback` README, where it is a parameter) is a Hit:
  a small **yellow dot** appears in the same place under the bars while the boom lasts (only in that case).
* With `rest_mode=class` the rest is one more bar, **yellow** (the bar and its threshold line, which is white on the other bars); with `none`/`timeout` it has no bar (cue and boom only).
* neurodraw has no scaling: each bar is a full-height rectangle that slides behind a black mask, whose top edge is the value.

Tests: `colcon test --packages-select ros2neuro_feedback_bar` (geometry and colors, no window).
