# CAR filter

!!! info ""
    Package: [`ros2neuro_filters_car`](https://github.com/ros2neuro/ros2neuro_filters_car) · pluginlib class: `ros2neuro_filters_car/CarFloat` · part of [Filters](index.md)

The Common Average Reference: it subtracts from every sample the mean over the channels. A spatial filter for the [`ros2neuro_filters`](index.md) chain.

| | |
|---|---|
| **Layer** | Filters |
| **Kind** | Plugin of [`ros2neuro_filters`](index.md) (pluginlib class `ros2neuro_filters_car/CarFloat`) |
| **Reads** | the `[samples x channels]` matrix of the previous filter in the chain |
| **Publishes** | a matrix of the same size, for the next filter |
| **Run** | in the chain YAML: `<configname>.<name>.class: ros2neuro_filters_car/CarFloat` |

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

For each sample, the filter subtracts the average across channels:

`x_out(s, :) = x(s, :) - mean(x(s, :))`

This is the classic CAR spatial re-referencing step.

## Plugin

- `ros2neuro_filters_car/CarFloat`

## Parameters

No extra parameters.

Example:

```yaml
filter_chain:
  ros__parameters:
    configname: filterchain
    filterchain.filters: [car]
    filterchain.car.class: ros2neuro_filters_car/CarFloat
```
