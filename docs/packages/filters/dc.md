# DC filter

!!! info ""
    Package: [`ros2neuro_filters_dc`](https://github.com/ros2neuro/ros2neuro_filters_dc) · pluginlib class: `ros2neuro_filters_dc/DcFloat` · part of [Filters](index.md)

Removes the DC offset: it subtracts from every channel its own mean over the block. A temporal filter for the [`ros2neuro_filters`](index.md) chain.

| | |
|---|---|
| **Layer** | Filters |
| **Kind** | Plugin of [`ros2neuro_filters`](index.md) (pluginlib class `ros2neuro_filters_dc/DcFloat`) |
| **Reads** | the `[samples x channels]` matrix of the previous filter in the chain |
| **Publishes** | a matrix of the same size, for the next filter |
| **Run** | in the chain YAML: `<configname>.<name>.class: ros2neuro_filters_dc/DcFloat` |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_filters`](index.md)
- **External libraries**:
    - Eigen3: matrices

## Messages and topics

Default node name: (none: it runs inside `filter_chain_node`).

Messages used:

- none: it works on a `[samples x channels]` matrix, not on messages

<!-- /interfaces -->
## Algorithm

For each channel, the filter subtracts the mean computed over the current time window:

`x_out(:, c) = x(:, c) - mean(x(:, c))`

This removes the per-channel DC component while preserving the matrix shape `[samples x channels]`.

## Plugin

- `ros2neuro_filters_dc/DcFloat`

## Parameters

No extra parameters.

Example:

```yaml
filter_chain:
  ros__parameters:
    configname: filterchain
    filterchain.filters: [dc]
    filterchain.dc.class: ros2neuro_filters_dc/DcFloat
```
