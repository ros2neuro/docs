# Control: tests and replication

!!! info ""
    Plugins: [Control](../../packages/control/index.md) · part of [Reproducibility](../index.md) › [Packages](index.md)

How the control is checked: the decision of a trial (Hit, Miss, Timeout) is recomputed from the integrated values and compared with the outcome control wrote on the event bus, in the integrator tests.

| Test (`ros2neuro_devel_test`) | What it checks | Check | MATLAB functions | Python functions |
|---|---|---|---|---|
| `integrator/` | Hit / Miss / Timeout of every trial | `check_integrator_exponential` | [`r2n_threshold_winner`](../matlab.md#r2n_threshold_winner) | [`r2n_threshold_winner`](../python.md#r2n_threshold_winner) |

How to run a test: [Packages](index.md#run-the-checks). Every function is explained, with its code, in [MATLAB](../matlab.md) and [Python](../python.md); [download them](../download.md).

## Control (base package)

`colcon test --packages-select ros2neuro_control`

`test/test_control_node.cpp` loads a test plugin through the node and checks that the plugin receives the `NeuroPrediction`,
that `request_reset()` calls the service (and is refused when the service is not up) and that `flush_input()` drops the
queued messages and leaves the subscription working.

## Control feedback (Feedback)

`colcon test --packages-select ros2neuro_control_feedback`

- logic without ROS: `layout`, `fields_map`, `flow` (header, values, thresholds), `reset_wait`, `trial_logic` (the outcome of a trial), `autopilot`, `asynchronous_logic` (the threshold that triggers a reset);
- `test_feedback_core`: the plugin writes only the end of the feedback and the outcome on the bus and refuses the rest (the end of the outcome is the manager's);
- `test_feedback_plugin`: the plugin loaded by the node of [`ros2neuro_control`](../../packages/control/index.md), with a helper node that plays the integrator, the manager (events) and the feedback: the three protocols (autopilot with and without the rest, Hit / Miss / Timeout, the rest in timeout, no trial without a cue, the classes and the ids of the events as parameters, the thresholds changed while running), the flow (the header of the prediction, the thresholds in force, no phase in it, neutral first) and the configuration that is refused (a rest without `rest_mode`, wrong durations, `rest_timeout` missing);
- `test_feedback_reset_timeout`: no value after a reset -> the node stops with an error (in its own executable, because the node shuts the process down).
