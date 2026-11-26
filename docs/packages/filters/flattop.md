# Flattop window

!!! info ""
    Package: [`ros2neuro_filters_flattop`](https://github.com/ros2neuro/ros2neuro_filters_flattop) · pluginlib class: `ros2neuro_filters_flattop/FlattopFloat` · part of [Filters](index.md)

Multiplies each block of samples by a flat-top window. A window filter for the [`ros2neuro_filters`](index.md) chain.

| | |
|---|---|
| **Layer** | Filters |
| **Kind** | Plugin of [`ros2neuro_filters`](index.md) (pluginlib class `ros2neuro_filters_flattop/FlattopFloat`) |
| **Reads** | the `[samples x channels]` matrix of the previous filter in the chain |
| **Publishes** | a matrix of the same size, for the next filter |
| **Run** | in the chain YAML: `<configname>.<name>.class: ros2neuro_filters_flattop/FlattopFloat` |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_filters`](index.md)
- **External libraries**:
    - Eigen3: matrices

## Messages and topics

Default node name: (none: it runs inside `filter_chain_node`).

Messages used:

- none: it works on a `[samples x channels]` matrix, not on messages

## Example configuration

The filter has no parameters: it is enough to put it in the chain.

```yaml
filter_chain:
  ros__parameters:
    configname: filters
    filters.filters: [flattop]
    filters.flattop.class: ros2neuro_filters_flattop/FlattopFloat
```

<!-- /interfaces -->
This package serves two related purposes:

- it exports a [`ros2neuro_filters`](index.md) plugin that applies a five-term flattop window to an input matrix
- it exposes a small reusable C++ API that can be used by other packages needing flattop
  coefficients and normalization terms, such as spectral estimators

## Window definition

This implementation uses the five-term flattop coefficients:

```text
w[n] = A0
     - A1*cos(2*pi*n/(N-1))
     + A2*cos(4*pi*n/(N-1))
     - A3*cos(6*pi*n/(N-1))
     + A4*cos(8*pi*n/(N-1))
```

with:

- `A0 = 0.21557895`
- `A1 = 0.41663158`
- `A2 = 0.277263158`
- `A3 = 0.083578947`
- `A4 = 0.006947368`

## Plugin

- plugin id: `ros2neuro_filters_flattop/FlattopFloat`
- header: `Flattop.hpp`

The plugin multiplies every channel (column) of the incoming matrix by the window, along the samples (rows). The window
length is the number of samples of the first matrix it receives and is not changed afterwards: every frame must have
that number of samples.

## Reusable C++ API

The `ros2neuro::filters::Flattop<T>` class exposes:

- `initialize(int nsamples)`: explicitly create the window coefficients
- `coefficients()`: read the cached coefficient vector
- `mean_square()`: read the average squared coefficient value
- `apply(...)`: multiply an input matrix by the window

Example:

```cpp
ros2neuro::filters::Flattop<double> window;
window.initialize(256);

const auto& coeffs = window.coefficients();
double mean_square = window.mean_square();
```

## Parameters

No extra runtime parameters.
