# Exponential integrator

!!! info ""
    Package: [`ros2neuro_integrator_exponential`](https://github.com/ros2neuro/ros2neuro_integrator_exponential) · pluginlib class: `ros2neuro::integrator::Exponential` · part of [Integrator](index.md)

An exponential moving average of the predicted probabilities: the new output is `alpha * previous + (1 - alpha) * prediction`. A high `alpha` (the default is 0.98) gives a very smooth output that reacts slowly.

| | |
|---|---|
| **Layer** | Integrator |
| **Kind** | Plugin of [`ros2neuro_integrator`](index.md) (pluginlib class `ros2neuro::integrator::Exponential`) |
| **Reads** | `NeuroPrediction` of type `TYPE_PROBABILITIES`, through the integrator node |
| **Publishes** | `NeuroControl` through the integrator node |
| **Run** | in the integrator YAML: `integrator.type: ros2neuro::integrator::Exponential`, `integrator.params.alpha: 0.98` |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_integrator`](index.md), [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)

## Messages and topics

Default node name: `integrator` (the node of [`ros2neuro_integrator`](index.md)).

Messages used:

- `NeuroPrediction`: read through the integrator node
- `NeuroControl`: published through the integrator node

<!-- /interfaces -->
## How it works

For every prediction the integrated values are updated with an exponential moving average:

```text
state = alpha * state + (1 - alpha) * prediction
```

The first prediction initialises the state. A high `alpha` weights the past heavily, so the output is very smooth and reacts
slowly; a low `alpha` follows the decoder closely. The decision is the class with the highest integrated value.

- The plugin expects predictions of type `NeuroPrediction::TYPE_PROBABILITIES` and a constant number of classes; otherwise the
  integrator node logs the error and skips the prediction.
- A reset ([`ros2neuro_integrator`](index.md)) sets every class to `1/K`.

## Parameters

| Parameter | Default | Meaning |
|---|---|---|
| `alpha` | `0.98` | smoothing factor, in `[0.0, 1.0]` (an invalid value falls back to the default with a warning) |

`alpha` can be changed while the node runs.

## Use

In the YAML of the integrator node (the plugin parameters live under `integrator.params.`):

```yaml
/integrator:
  ros__parameters:
    integrator.type: ros2neuro::integrator::Exponential
    integrator.params.alpha: 0.98
    integrator.rejection: 0.55
```

```bash
ros2 param set /integrator integrator.params.alpha 0.9
```

## Tests

`colcon test --packages-select ros2neuro_integrator_exponential`
