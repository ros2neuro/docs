# ros2neuro_feedback: the node and the base class

!!! info ""
    Package: [`ros2neuro_feedback`](https://github.com/ros2neuro/ros2neuro_feedback)

The node and the plugin interface (the parent class) of the feedback family, with what is common to all its plugins. For what the family does and its list of plugins see the [overview](index.md); each plugin has its own page.

## The node: `feedback_node`

The package provides one executable, `feedback_node`. It subscribes to the event bus and to the flow,
builds the layout from its parameters, loads the plugin and runs the drawing loop at `fps` frames per second.

| Parameter | Default | Meaning |
|---|---|---|
| `plugin` | (required) | pluginlib class of the drawing, [`ros2neuro::feedback::Wheel`](wheel.md) or [`ros2neuro::feedback::Bar`](bar.md) |
| `classes`, `rest_mode`, `thresholds` | `classes`, `thresholds`: required (no default); `rest_mode`: `none` | the same as the manager and control: the layout of the drawing and the initial markers. `thresholds`: one per class, except for a plugin that takes any number (the wheel draws any number of them as positions on its axis, see [Wheel](wheel.md)) |
| `event.start` ... `event.shown` | the defaults of the stack | the ids of the events (the same as the manager and control) |
| `control_topic` | `/control_feedback/probabilities` | the flow: values and thresholds |
| `event_topic` | `/neuroevent` | the phases of the trials and the outcome; also where `publish_display_events` writes |
| `fps` | `60` | frames per second of the window |
| `publish_display_events` | `false` | after drawing, publish `shown + id` events for the cue and the boom, and the matching `Off` |
| `latency_log_period_s` | `5.0` | seconds between the "latency stamp to draw" log lines, `0` disables them |
| `window_title` | `ros2neuro feedback` | title of the window |

Behaviour worth knowing:

- Before the first message the neutral vector (`1/K` for every class) is drawn.
- The cue is the last class event. A rest in `timeout` that ends as a Hit is marked by the plugin, and on a Miss the
  boom shows the class that went over its threshold. A Timeout gives a neutral grey boom.
- Gaps in the sequence counter `seq` of the flow are logged.
- Close the window with ESC: it ends the node.

## Minimal example

```yaml
/**:                          # the same for the manager, control and the feedback
  ros__parameters:
    classes: [773, 771]       # required by the feedback (no default)
    rest_mode: none
    thresholds: [0.7, 0.7]    # required by the feedback (the initial markers)

/feedback:
  ros__parameters:
    plugin: ros2neuro::feedback::Bar
    control_topic: /control_feedback/probabilities
    fps: 60.0
    window_title: "Bars"
```

The feedback is started together with the manager and control. See [`ros2neuro_devel_test`](../../reproducibility/packages/index.md) for complete
launch files, and the [hardware-free tutorial](../../tutorials/hardware-free-pipeline/index.md) to see them run.

## Writing a new drawing

Derive from `ros2neuro::feedback::Feedback` (`set_values`, cue, fixation, boom) and export it against
`ros2neuro_feedback` with `pluginlib_export_plugin_description_file(ros2neuro_feedback plugins.xml)`. Keep the
geometry in a pure, testable header, as [`ros2neuro_feedback_bar`](bar.md) does with `bar_geometry.hpp`.

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)
- **At run time**: the manager (writes the phases) and control (writes the outcome and the flow)
- **External libraries**:
    - [`neurodraw`](neurodraw.md): needed by the drawing plugins (see below)
- **At run time**: a drawing plugin package ([`ros2neuro_feedback_wheel`](wheel.md) or `_bar`)

## Messages and topics

Default node name: `feedback`.

| | Default topic | Type | Changed by |
|---|---|---|---|
| subscribes | `/control_feedback/probabilities` | `NeuroControl` | `control_topic` |
| subscribes | `/neuroevent` | `NeuroEvent` | `event_topic` |
| publishes | `/neuroevent` | `NeuroEvent` | `event_topic`, **only** with `publish_display_events: true` |

Messages used:

- `NeuroControl`: read, the flow of [`ros2neuro_control_feedback`](../control/feedback.md) (values, thresholds)
- `NeuroEvent`: read, the phases and the outcome; published, optional display events

## Example configuration

The feedback of the Gaussian pipeline of [`ros2neuro_devel_test`](../../reproducibility/packages/index.md) (`feedback/bars2/config/feedback_bars.yaml`). The `classes`, `rest_mode` and `thresholds` are in `layout.yaml`, which the launcher gives to the manager, control and the feedback alike.


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
## Requirements: `neurodraw`

The feedback itself (the node and the flow) does not draw anything: the two drawing plugins, [`ros2neuro_feedback_wheel`](wheel.md) and
[`ros2neuro_feedback_bar`](bar.md), are built on the **[`neurodraw`](neurodraw.md)** library (SDL2 and OpenGL), which they find with
`find_package(neurodraw CONFIG REQUIRED)`. Install it before building them:

```bash
sudo apt-get install libsdl2-dev libsdl2-image-dev libsdl2-ttf-dev
git clone https://github.com/neurorobotics-iaslab/neurodraw.git
cd neurodraw && cmake -S . -B build && cmake --build build && sudo cmake --install build
```

Alternatively, put the [`neurodraw`](neurodraw.md) folder in the `src/` of the workspace: `colcon` builds it before the plugins.

* Phases: what the bus says. With trials (calibration, evaluation) it shows the fixation, the cue and the boom; a control writes no events and only the values are drawn.
* Before the first message the neutral vector (1/K) is drawn. Gaps in `seq` are logged.
* Cue = last class event; a rest in timeout that ends as a Hit is marked by the plugins with a small circle (`is_rest_timeout_hit()`); on a Miss the boom shows the class over its threshold (same rule as [`ros2neuro_control_feedback`](../control/feedback.md)),
  on a Timeout a neutral grey boom.
* The latency (message stamp -> drawing) is logged every `latency_log_period_s`.
* `publish_display_events` (default false): after drawing, publishes on `/neuroevent` `shown + id` for the cue
  (class code), the boom (the id of Hit / Miss / Timeout) and the matching `+Off` (`event.shown` and `event.off`, the same as the manager and control), stamped after the drawing.
* Parameters: `plugin`, `control_topic`, `event_topic`, `fps` (60), `publish_display_events`, `latency_log_period_s` (5), `window_title`,
  `classes`, `rest_mode` (`none`), `thresholds` (initial) and `event.*` (the same as the manager and control; `classes` and `thresholds` have no default here and must be given). ESC in the window ends the node.
* The plugin API: `free_thresholds()` (false by default: one threshold per class, as the bars; true: any number of them, as the wheel, which draws them as positions on its axis; asked before `configure`), `configure(node, layout, options)`, `set_values`, `set_thresholds` (the markers move), `show_fixation` / `hide_fixation`,
  `show_cue` / `hide_cue`, `show_boom(Outcome, target, reached)` / `hide_boom`. A plugin knows nothing about the ids of the events: the
  controller translates them into the `Outcome` enum (`Hit`, `Miss`, `Timeout`).

Writing a plugin: derive from `Feedback`, register in a `plugins.xml` exported with
`pluginlib_export_plugin_description_file(ros2neuro_feedback plugins.xml)`.

Tests: `colcon test --packages-select ros2neuro_feedback`: the controller with a recording plugin (ids of the events other than the defaults, thresholds changed while running, the class a miss shows), the layout, the thresholds, the colors, the flow reader.
