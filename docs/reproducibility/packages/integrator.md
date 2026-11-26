# Integrator: tests and replication

!!! info ""
    Plugins: [Integrator](../../packages/integrator/index.md) · part of [Reproducibility](../index.md) › [Packages](index.md)

How the integrator is checked: whole pipelines that end in each integrator: raw, Laplacian, band-pass, Welch, QDA, integrator. They also check the reset at every CFeedback and the outcome of every trial.

| Test (`ros2neuro_devel_test`) | What it checks | Check | MATLAB functions | Python functions |
|---|---|---|---|---|
| `integrator/exponential/` | exponential integrator | `check_integrator_exponential` | [`r2n_integrator_exponential`](../matlab.md#r2n_integrator_exponential), [`r2n_threshold_winner`](../matlab.md#r2n_threshold_winner) | [`r2n_integrator_exponential`](../python.md#r2n_integrator_exponential), [`r2n_threshold_winner`](../python.md#r2n_threshold_winner) |
| `integrator/buffer/` | buffer integrator, hard and soft | `check_integrator_buffer` | [`r2n_integrator_buffer`](../matlab.md#r2n_integrator_buffer), [`r2n_threshold_winner`](../matlab.md#r2n_threshold_winner) | [`r2n_integrator_buffer`](../python.md#r2n_integrator_buffer), [`r2n_threshold_winner`](../python.md#r2n_threshold_winner) |

How to run a test: [Packages](index.md#run-the-checks). Every function is explained, with its code, in [MATLAB](../matlab.md) and [Python](../python.md); [download them](../download.md).

## Integrator (base package)

`colcon test --packages-select ros2neuro_integrator`

### Tests of the whole stack

[`ros2neuro_devel_test`](https://github.com/ros2neuro/ros2neuro_devel_test) (`integrator/`) runs a WHOLE pipeline (raw, Laplacian, band-pass, Welch, QDA, integrator) and redoes every step in MATLAB, with one figure per step; it also checks the resets at every CFeedback and the outcome of every trial. `pipeline/` adds control and the feedback window. Run: `integrator/<kind>/integrator_<kind>.launch.py` then `check_integrator_<kind>`, for `exponential` and `buffer`; the check is a MATLAB file you read from the top (see the README of that package).

## Buffer integrator

### Testing

```bash
colcon build --packages-select ros2neuro_integrator_buffer
colcon test --packages-select ros2neuro_integrator_buffer
```

`test/test_buffer.cpp` loads the plugin through `pluginlib::ClassLoader`
(the same path [`ros2neuro_integrator`](../../packages/integrator/index.md) uses in production) and covers HARD
and SOFT increment, `[0, 1]` clipping, `init_val` handling (both matching
and mismatched sizes), invalid `configure()` parameters, and
`set_runtime_parameter` validation.
`test/test_buffer_node.cpp` runs the integrator node with this plugin (parameters given as
`integrator.params.*`) and checks the published `NeuroPrediction` (`TYPE_SCORES`, the buffer values).

## Exponential integrator

`colcon test --packages-select ros2neuro_integrator_exponential`
