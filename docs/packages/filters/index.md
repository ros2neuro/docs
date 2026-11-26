# Filters

!!! info ""
    Package: [`ros2neuro_filters`](https://github.com/ros2neuro/ros2neuro_filters)

The filters package provides the **filter chain**: one node, `filter_chain_node`, that applies an ordered list of
filters to every `NeuroFrame`. Each filter is a plugin working on a matrix shaped `[samples x channels]`, and the
chain is described entirely in YAML.

## What is in this menu

| Page | What you find |
|---|---|
| [Base class: `ros2neuro_filters`](base.md) | the node, its topics and parameters, the plugin interface and how to write a new plugin |
| [Available plugins](#available-plugins) | the plugins of the family, each with its own page |

## Available plugins

| Kind | Plugin | pluginlib class |
|---|---|---|
| Temporal | [DC](dc.md) | [`ros2neuro_filters_dc/DcFloat`](dc.md) |
| Temporal | [Butterworth](butterworth.md) | [`ros2neuro_filters_butterworth/ButterworthFloat`](butterworth.md) |
| Spatial | [CAR](car.md) | [`ros2neuro_filters_car/CarFloat`](car.md) |
| Spatial | [Laplacian](laplacian.md) | [`ros2neuro_filters_laplacian/LaplacianFloat`](laplacian.md) |
| Window | [Hann](hann.md) | [`ros2neuro_filters_hann/HannFloat`](hann.md) |
| Window | [Hamming](hamming.md) | [`ros2neuro_filters_hamming/HammingFloat`](hamming.md) |
| Window | [Blackman](blackman.md) | [`ros2neuro_filters_blackman/BlackmanFloat`](blackman.md) |
| Window | [Flattop](flattop.md) | [`ros2neuro_filters_flattop/FlattopFloat`](flattop.md) |

Filters never change the dimensionality of the data.
