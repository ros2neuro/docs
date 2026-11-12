# Buffer integrator

!!! info ""
    Package: [`ros2neuro_integrator_buffer`](https://github.com/ros2neuro/ros2neuro_integrator_buffer) · pluginlib class: `ros2neuro::integrator::Buffer` · part of [Integrator](index.md)

ROS2 port of the `rosneuro_integrator_buffer` (ROS1) plugin: a
[`ros2neuro_integrator`](index.md) backend (`ros2neuro::integrator::Buffer`) that keeps
one accumulator buffer per class. On every prediction the class that wins
(the highest value of the prediction) goes up by one step and the other classes
go down by the same total amount. The buffers always stay in `[0, 1]` and always
sum to 1, so the integrated output is the buffer state itself, already a
distribution (nothing to normalize downstream). The decision is whichever class
currently has the highest buffer value, not necessarily the winner of the latest
prediction. See [How the update works](#how-the-update-works).

| | |
|---|---|
| **Layer** | Integrator |
| **Kind** | Plugin of [`ros2neuro_integrator`](index.md) (pluginlib class `ros2neuro::integrator::Buffer`) |
| **Reads** | `NeuroPrediction`, through the integrator node |
| **Publishes** | `NeuroPrediction` (`TYPE_SCORES`) through the integrator node |
| **Run** | in the integrator YAML: `integrator.type: ros2neuro::integrator::Buffer`, `integrator.params.buffer_size: 48` |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_integrator`](index.md), [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)

## Messages and topics

Default node name: `integrator` (the node of [`ros2neuro_integrator`](index.md)).

Messages used:

- `NeuroPrediction`: read through the integrator node
- `NeuroPrediction`: published through the integrator node (`type = TYPE_SCORES`, the buffers as `values`)

## Example configuration

From the Gaussian pipeline of [`ros2neuro_devel_test`](../devel-test.md) (`integrator:=buffer`): at 16 predictions per second, `buffer_size: 48` means that, with two classes, 24 unanimous predictions (1.5 seconds) take a buffer from `1/K` = 0.5 to 1 (in general `(1 - 1/K) * buffer_size` predictions):

```yaml
/integrator:
    ros__parameters:
        input_topic: /classification/prediction
        output_topic: /integrated/raw
        event_topic: /neuroevent
        integrator.name: mi_buffer_integrator
        integrator.type: ros2neuro::integrator::Buffer
        integrator.params.buffer_size: 48
        integrator.params.increment: 0
        integrator.rejection: 0.55
        integrator.reset_event: 781
```

<!-- /interfaces -->
## Parameters

| Name          | Type          | Default        | Notes                                                             |
| ------------- | ------------- | -------------- | ------------------------------------------------------------------ |
| `buffer_size` | int           | `48`           | Its inverse is the step size per frame                             |
| `increment`   | int           | `0` (HARD)     | `0` HARD: fixed step `1/buffer_size`. `1` SOFT: step scaled by the winning class's probability, `P(c)/buffer_size` |
| `init_val`    | double array  | *(none)*       | Per-class initial buffer values, normalized to sum 1 (negative values are an error). If absent, or its size doesn't match the class count at `reset()`, falls back to a uniform `1/n_classes` (logged as a warning in the mismatch case) |

Both `buffer_size` and `increment` are changeable at runtime via
`set_runtime_parameter` (rejected if the value is the wrong type or out of
range). `init_val` is configure-time only, matching the ROS1 plugin (it
defines the buffer's initial state, not something you'd want to change
mid-session).

## How the update works

For every prediction `p` (the node skips it before the plugin if it is below `integrator.rejection`):

1. the **winner** `w` is the class with the highest value in `p.values`;
2. the **step** is `1 / buffer_size` (HARD, `increment: 0`) or `p.values[w] / buffer_size` (SOFT, `increment: 1`);
3. the winner **gains** `min(step, 1 - buffer[w])`: it never goes above 1;
4. **exactly that amount is taken from the other classes**, in equal shares (`gain / (K - 1)` each);
5. a class that would go below 0 **stops at 0** and cannot give more: the share it could not give is taken, again in equal
   shares, from the classes that still have something (this repeats until the whole amount has been taken).

The consequences:

- the values are clipped only at **0 and 1**, and the clipping never loses anything: what a class cannot give or receive is
  moved to the others, so the **sum of the buffers stays 1** and no value can become negative;
- with two classes it is the classic `+step / -step`;
- HARD and SOFT differ only in the step: in HARD a prediction `{0.51, 0.49}` counts as much as `{0.99, 0.01}`, in SOFT the
  more confident prediction moves the buffer more. SOFT is also a bit slower (the step is at most `1/buffer_size`, and with
  two classes the winning probability is between 0.5 and 1);
- when a buffer is saturated (`{0, 1, 0}`) it stays there while the same class keeps winning, and it takes many predictions of
  another class to move away from it.

### Example: three classes, SOFT, always the same winner

`buffer_size: 10`, `increment: 1`, `init_val: [0.3, 0.5, 0.2]` (the sum is 1), and class 1 wins every time with probability
0.9. The step is `0.9 / 10 = 0.09`:

| Prediction | Class 0 | Class 1 (winner) | Class 2 | What happens |
|---|---|---|---|---|
| start | 0.30 | 0.50 | 0.20 | |
| 1 | 0.255 | 0.59 | 0.155 | the winner +0.09, the others -0.045 each |
| 2 | 0.21 | 0.68 | 0.11 | |
| 3 | 0.165 | 0.77 | 0.065 | |
| 4 | 0.12 | 0.86 | 0.02 | |
| 5 | 0.05 | 0.95 | **0** | class 2 has only 0.02 to give (not 0.045): it stops at 0 and class 0 gives the missing 0.025 more |
| 6 | **0** | **1** | 0 | the winner gains only what it misses to reach 1 (0.05), taken from class 0, the only one left |
| 7 and later | 0 | 1 | 0 | saturated, nothing changes |

The sum is 1 in every row, and no value is negative. With HARD the result is the same, only the step changes (`1/10 = 0.1`
for every prediction, whatever its probability).

## Differences from the ROS1 plugin

- **More than two classes.** The two-class behaviour (winner +step, loser -step) is extended to K classes by
  sharing the decrement among the K-1 losers (`step / (K - 1)` each). With two classes it is exactly the same as before.
  The clipping at 0 and 1 does not alter the sum: the winner gains at most `1 - value` and exactly that amount is taken from
  the others (a loser that reaches 0 stops there and the rest is taken from the others), so the output is always a
  distribution (see [How the update works](#how-the-update-works)).
- **No `n_classes` parameter.** ROS1 required it upfront to size the
  buffers and validate `init_val`. In ROS2, [`ros2neuro_integrator`](index.md) tells the
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

## Parameters from the launch file and at runtime

`ros2neuro_integrator` declares every `integrator.params.*` parameter it is given at start (parameter
file or `-p`) and passes all of them to the plugin, so `buffer_size`, `increment` and `init_val` reach
`configure()` from a launch YAML. At runtime it forwards any change under `integrator.params.*` to
`set_runtime_parameter`, so `ros2 param set /integrator integrator.params.buffer_size 32` works, but only
for a parameter that was given at start (ROS refuses an undeclared parameter). A parameter that is not
given keeps its code default (`buffer_size=48`, `increment=HARD`, uniform `init_val`).

## Testing

```bash
colcon build --packages-select ros2neuro_integrator_buffer
colcon test --packages-select ros2neuro_integrator_buffer
```

`test/test_buffer.cpp` loads the plugin through `pluginlib::ClassLoader`
(the same path [`ros2neuro_integrator`](index.md) uses in production) and covers HARD
and SOFT increment, `[0, 1]` clipping, `init_val` handling (both matching
and mismatched sizes), invalid `configure()` parameters, and
`set_runtime_parameter` validation.
`test/test_buffer_node.cpp` runs the integrator node with this plugin (parameters given as
`integrator.params.*`) and checks the published `NeuroPrediction` (`TYPE_SCORES`, the buffer values).
