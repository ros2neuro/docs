# Manager: tests and replication

!!! info ""
    Plugins: [Manager](../../packages/manager/index.md) · part of [Reproducibility](../index.md) › [Packages](index.md)

How the manager is checked: the manager runs the trials of every test, so its events (order, durations, outcomes) are checked by all of them, and in particular by the acquisition test.

| Test (`ros2neuro_devel_test`) | What it checks | Check | MATLAB functions | Python functions |
|---|---|---|---|---|
| `acquisition/` | the 6 trials of a calibration | `check_acquisition` | none | none |

How to run a test: [Packages](index.md#run-the-checks). Every function is explained, with its code, in [MATLAB](../matlab.md) and [Python](../python.md); [download them](../download.md).

## Manager (base package)

`colcon test --packages-select ros2neuro_manager`: the ids of the events (defaults, validation, changed ids), the class codes (reserved,
out of range, following the configured ids), the protocol layout, and `test_manager_node` (a test plugin loaded by the node: it writes on
the bus, it hears the bus including its own events, the event ids / classes / rest_mode are parameters of the node, a missing
or unknown plugin or invalid ids do not configure).

## Synchronous manager (Synchronous)

`colcon test --packages-select ros2neuro_manager_synchronous`: the trial sequence (counts, shuffle, any code), and
`test_synchronous_plugin`, the plugin loaded by the node of [`ros2neuro_manager`](../../packages/manager/index.md) with a helper node that plays
[`ros2neuro_control_feedback`](../../packages/control/feedback.md) (it answers CFeedback with the close of the feedback and Hit / Miss / Timeout): the ten events of
every trial in order, the manager writes the phases and the end of the outcome, the outcome is closed after the boom, the next trial waits for the outcome, every class
the requested number of times, `protocol_ended`, the wait of `duration.begin`, wrong `trials` / durations. `test_synchronous_no_outcome` (its own executable, the node shuts the process down):
the trial is never closed -> the manager stops with an error.
