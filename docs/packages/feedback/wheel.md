# Wheel feedback

!!! info ""
    Package: [`ros2neuro_feedback_wheel`](https://github.com/ros2neuro/ros2neuro_feedback_wheel) · pluginlib class: `ros2neuro::feedback::Wheel` · part of [Feedback](index.md)

Plugin `ros2neuro::feedback::Wheel` (neurodraw) for `ros2neuro_feedback`: the wheel (ring, arc, moving line,
cross, cue circle, threshold markers), driven by the feedback core.

* Two active classes (`K == 2`): `output_classes[0]` on the left, `[1]` on the right; the position is the normalized
  value of the first. A rest is allowed only with `rest_mode=timeout`; `rest_mode=class` (K=3) is rejected.
* Threshold markers: first class at `th0`, second at `1 - th1` (with `[0.8, 0.8]`: 0.8 and 0.2); the one closest to 0 is
  red, the one closest to 1 blue.
* Colors as in the existing wheel: first class blue, second red; **the rest is always yellow**; timeout boom neutral grey.
  **Rest** (yellow): with `rest_mode=timeout` it has a cue (yellow circle) and nothing else on the wheel; when it ends as a Hit
  (no threshold touched for `rest_timeout` seconds) the **arc turns yellow**, like the arc takes the color of the class
  reached on any hit (no extra dots). With `rest_mode=class` the rest is a normal class, one of the two sides (e.g.
  `classes:=[783, 773]`), that only colors when it reaches its threshold; its **threshold marker is yellow** too (the other side
  keeps blue / red).
* Parameter `angle_range` (180). Blink indicator not ported (the feedback reads only the flow).

Tests: `colcon test --packages-select ros2neuro_feedback_wheel` (geometry, no window).
