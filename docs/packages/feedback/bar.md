# Bar feedback

!!! info ""
    Package: [`ros2neuro_feedback_bar`](https://github.com/ros2neuro/ros2neuro_feedback_bar) · pluginlib class: `ros2neuro::feedback::Bar` · part of [Feedback](index.md)

Plugin `ros2neuro::feedback::Bar`, **neurodraw only** (`Rectangle`, `Circle`, `Cross`; neurodraw itself is not modified).

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
  (The thresholds are those of the feedback's own `thresholds` parameter: a runtime change on the manager is not followed.)
* **Fixation cross and cue always in the same place**: centred under the bars, whatever the target. The bars are always
  there. The cue has the color of the target's bar (a rest in timeout, which has no bar, is yellow).
* **No circle for the outcome**: the outcome is the bars lighting up, and a bar never changes color. The only exception is a
  rest with **`rest_mode=timeout`** that is a Hit (no threshold touched for `rest_timeout` seconds, see the training README):
  a small **yellow dot** appears in the same place under the bars while the boom lasts (only in that case).
* With `rest_mode=class` the rest is one more bar, **yellow** (the bar and its threshold line, which is white on the other bars); with `none`/`timeout` it has no bar (cue and boom only).
* neurodraw has no scaling: each bar is a full-height rectangle that slides behind a black mask, whose top edge is the value.

Tests: `colcon test --packages-select ros2neuro_feedback_bar` (geometry and colors, no window).
