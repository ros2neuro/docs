# Hann window

!!! info ""
    Package: [`ros2neuro_filters_hann`](https://github.com/ros2neuro/ros2neuro_filters_hann) · pluginlib class: `ros2neuro_filters_hann/HannFloat` · part of [Filters](index.md)

Multiplies each block of samples by a Hann window. A window filter for the [`ros2neuro_filters`](index.md) chain.

| | |
|---|---|
| **Layer** | Filters |
| **Kind** | Plugin of [`ros2neuro_filters`](index.md) (pluginlib class `ros2neuro_filters_hann/HannFloat`) |
| **Reads** | the `[samples x channels]` matrix of the previous filter in the chain |
| **Publishes** | a matrix of the same size, for the next filter |
| **Run** | in the chain YAML: `<configname>.<name>.class: ros2neuro_filters_hann/HannFloat` |

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
    filters.filters: [hann]
    filters.hann.class: ros2neuro_filters_hann/HannFloat
```

<!-- /interfaces -->
This package serves two related purposes:

- it exports a [`ros2neuro_filters`](index.md) plugin that applies a Hann window to an input matrix
- it exposes a small reusable C++ API that can be used by other packages needing Hann
  coefficients and normalization terms, such as spectral estimators

## Window definition

For a window length `N`, the Hann coefficients are:

```text
w[n] = 0.5 * (1 - cos(2*pi*n/(N-1)))
```

for `n = 0, ..., N-1`.

## Plugin

- plugin id: `ros2neuro_filters_hann/HannFloat`
- header: `Hann.hpp`

The plugin multiplies every channel (column) of the incoming matrix by the window, along the samples (rows). The window
length is the number of samples of the first matrix it receives and is not changed afterwards: every frame must have
that number of samples.

## Reusable C++ API

The `ros2neuro::filters::Hann<T>` class exposes:

- `initialize(int nsamples)`: explicitly create the window coefficients
- `coefficients()`: read the cached coefficient vector
- `mean_square()`: read the average squared coefficient value
- `apply(...)`: multiply an input matrix by the window

This makes the class usable both as a filter plugin and as a utility inside packages such as
[`ros2neuro_processing_spectral`](../processing/spectral.md) (the spectral plugins).

Example:

```cpp
ros2neuro::filters::Hann<double> window;
window.initialize(256);

const auto& coeffs = window.coefficients();
double mean_square = window.mean_square();
```

## Parameters

No extra runtime parameters.
