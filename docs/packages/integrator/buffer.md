# Buffer integrator

!!! info ""
    Package: [`ros2neuro_integrator_buffer`](https://github.com/ros2neuro/ros2neuro_integrator_buffer) · pluginlib class: `ros2neuro::integrator::Buffer` · part of [Integrator](index.md)

ROS2 port of the `rosneuro_integrator_buffer` (ROS1) plugin: a
`ros2neuro_integrator` backend (`ros2neuro::integrator::Buffer`) that keeps
one accumulator buffer per class. On every prediction it nudges the winning
class's buffer up by one step and the other classes' buffers down by the same
amount shared between them (`step / (K - 1)` each, so the sum of the buffers stays
1 apart from the clipping, for any number of classes K; with K = 2 it is the classic +step / -step),
clipped to `[0, 1]`;
the integrated output is the buffer state itself, and the decision is
whichever class currently has the highest buffer value (not necessarily the
same as the instantaneous winning class of the latest prediction).

## Parameters

| Name          | Type          | Default        | Notes                                                             |
| ------------- | ------------- | -------------- | ------------------------------------------------------------------ |
| `buffer_size` | int           | `48`           | Its inverse is the step size per frame                             |
| `increment`   | int           | `0` (HARD)     | `0` HARD: fixed step `1/buffer_size`. `1` SOFT: step scaled by the winning class's probability, `P(c)/buffer_size` |
| `init_val`    | double array  | *(none)*       | Per-class initial buffer values. If absent, or its size doesn't match the class count at `reset()`, falls back to a uniform `1/n_classes` (logged as a warning in the mismatch case) |

Both `buffer_size` and `increment` are changeable at runtime via
`set_runtime_parameter` (rejected if the value is the wrong type or out of
range). `init_val` is configure-time only, matching the ROS1 plugin (it
defines the buffer's initial state, not something you'd want to change
mid-session).

## Differences from the ROS1 plugin

- **More than two classes.** The two-class behaviour (winner +step, loser -step) is extended to K classes by
  sharing the decrement among the K-1 losers (`step / (K - 1)` each), so the sum of the buffers stays 1 as long as
  the `[0, 1]` clipping does not kick in. With two classes it is exactly the same as before. If the clipping alters
  the sum, the consumers normalize anyway (the manager divides by the sum).
- **No `n_classes` parameter.** ROS1 required it upfront to size the
  buffers and validate `init_val`. In ROS2, `ros2neuro_integrator` tells the
  plugin the class count directly -- via `reset(class_count)`, and
  implicitly via the size of each `NeuroPrediction.values` -- so the buffer
  now sizes (and re-sizes, with a warning, if a prediction's size changes
  mid-stream) itself lazily instead of needing it as a separate parameter
  that could drift out of sync with the real prediction size.
- **`init_val` is not mandatory.** ROS1 failed `configure()` outright
  without it. Here, since the class count isn't even known at configure
  time, a missing or wrong-sized `init_val` just falls back to a uniform
  `1/n` buffer with a logged warning, rather than refusing to start.
- **Runtime reconfiguration** uses `Integrator::set_runtime_parameter`
  (ROS2's per-plugin parameter-callback hook) instead of ROS1's
  `dynamic_reconfigure` + a generated `Buffer.cfg`. Same two knobs
  (`buffer_size`, `increment`), no separate `.cfg` file needed.

## Known gap in the current parameter pipeline

As of this writing, `ros2neuro_integrator::IntegratorNode` only pre-declares
and routes through one hardcoded plugin parameter, `integrator.params.alpha`
-- both at configure time (`get_parameters("integrator.params", ...)` only
returns *declared* parameters, and only `alpha` is declared) and at runtime
(`IntegratorNode::is_supported_runtime_parameter` only allow-lists
`rejection` and `integrator.params.alpha`). Until that's generalized (e.g.
`automatically_declare_parameters_from_overrides` on the node, and dropping
the runtime allow-list in favor of delegating anything under
`integrator.params.*` to the plugin), `buffer_size`/`increment`/`init_val`
won't actually reach this plugin from a launch YAML or `ros2 param set`, and
it will silently run with its code defaults (`buffer_size=48`,
`increment=HARD`, uniform `init_val`). The plugin itself is written
correctly against the documented `Integrator` interface and is verified
directly (see Testing below); this gap is in the node that hosts it, not
here.

## Testing

```bash
colcon build --packages-select ros2neuro_integrator_buffer
colcon test --packages-select ros2neuro_integrator_buffer
```

`test/test_buffer.cpp` loads the plugin through `pluginlib::ClassLoader`
(the same path `ros2neuro_integrator` uses in production) and covers HARD
and SOFT increment, `[0, 1]` clipping, `init_val` handling (both matching
and mismatched sizes), invalid `configure()` parameters, and
`set_runtime_parameter` validation.
