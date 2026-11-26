# Butterworth filter

!!! info ""
    Package: [`ros2neuro_filters_butterworth`](https://github.com/ros2neuro/ros2neuro_filters_butterworth) · pluginlib class: `ros2neuro_filters_butterworth/ButterworthFloat` · part of [Filters](index.md)

A real-time Butterworth IIR filter, low-pass or high-pass (chain one of each for a band-pass), built on `librtfilter`; it keeps its state from one frame to the next. A temporal filter for the [`ros2neuro_filters`](index.md) chain.

| | |
|---|---|
| **Layer** | Filters |
| **Kind** | Plugin of [`ros2neuro_filters`](index.md) (pluginlib class `ros2neuro_filters_butterworth/ButterworthFloat`) |
| **Reads** | the `[samples x channels]` matrix of the previous filter in the chain |
| **Publishes** | a matrix of the same size, for the next filter |
| **Run** | in the chain YAML: `<configname>.<name>.class: ros2neuro_filters_butterworth/ButterworthFloat` |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_filters`](index.md)
- **External libraries**:
    - Eigen3: matrices
    - `librtfilter`: the IIR filter implementation (found with `find_library`)

## Messages and topics

Default node name: (none: it runs inside `filter_chain_node`).

Messages used:

- none: it works on a `[samples x channels]` matrix, not on messages

<!-- /interfaces -->
## Algorithm

The plugin builds a stateful low-pass or high-pass Butterworth filter. Internal state is allocated on first use, once the number of channels is known; from then on every input must have that same number of channels. The filter runs in double precision and its output is converted back to float32.

## Plugin

- `ros2neuro_filters_butterworth/ButterworthFloat`

## Parameters

- `order` (`integer`, required)
- `samplerate` (`double`, required)
- `cutoff` (`double`, required)
- `type` (`string`, required): `lowpass` or `highpass`

Example:

```yaml
filter_chain:
  ros__parameters:
    configname: filterchain
    filterchain.filters: [hp, lp]

    filterchain.hp.class: ros2neuro_filters_butterworth/ButterworthFloat
    filterchain.hp.order: 4
    filterchain.hp.samplerate: 512.0
    filterchain.hp.cutoff: 1.0
    filterchain.hp.type: highpass

    filterchain.lp.class: ros2neuro_filters_butterworth/ButterworthFloat
    filterchain.lp.order: 4
    filterchain.lp.samplerate: 512.0
    filterchain.lp.cutoff: 40.0
    filterchain.lp.type: lowpass
```
