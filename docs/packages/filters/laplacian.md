# Laplacian filter

!!! info ""
    Package: [`ros2neuro_filters_laplacian`](https://github.com/ros2neuro/ros2neuro_filters_laplacian) · pluginlib class: `ros2neuro_filters_laplacian/LaplacianFloat` · part of [Filters](index.md)

The Laplacian spatial filter: it subtracts from each channel the average of its four cardinal neighbours (north, south, east, west), defined by an electrode layout matrix. A spatial filter for the [`ros2neuro_filters`](index.md) chain.

| | |
|---|---|
| **Layer** | Filters |
| **Kind** | Plugin of [`ros2neuro_filters`](index.md) (pluginlib class `ros2neuro_filters_laplacian/LaplacianFloat`) |
| **Reads** | the `[samples x channels]` matrix of the previous filter in the chain |
| **Publishes** | a matrix of the same size, for the next filter |
| **Run** | in the chain YAML: `<configname>.<name>.class: ros2neuro_filters_laplacian/LaplacianFloat` |

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

For each channel, the filter subtracts the average of the cardinal neighbours defined by the electrode layout:

```text
    N
W [C] E
    S
```

Only non-zero entries in the layout are treated as valid channels.

## Plugin

- `ros2neuro_filters_laplacian/LaplacianFloat`

## Parameters

- `layout` (`string`, required): matrix serialized row-by-row with `;` between rows
- `nchannels` (`integer`, optional): number of channels of the input (the mask is `nchannels x nchannels`); if omitted, the
  highest channel id in the layout is used. Channel ids are 1-based (0 = no electrode): a layout with an id below 0 or above
  `nchannels` is refused at configure. Every frame must have exactly `nchannels` channels: a frame with another number is not
  filtered, and the filter chain logs `Laplacian: the frame has N channels, 'nchannels' is M` and drops it

Example:

```yaml
filter_chain:
  ros__parameters:
    configname: laplacian_chain
    laplacian_chain.filters: [laplacian]
    laplacian_chain.laplacian.class: ros2neuro_filters_laplacian/LaplacianFloat
    laplacian_chain.laplacian.nchannels: 16
    laplacian_chain.laplacian.layout: "0 0 1 0 0; 2 3 4 5 6; 7 8 9 10 11; 12 13 14 15 16"
```
