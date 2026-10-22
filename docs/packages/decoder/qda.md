# QDA decoder

!!! info ""
    Package: [`ros2neuro_decoder_qda`](https://github.com/ros2neuro/ros2neuro_decoder_qda) · pluginlib class: `ros2neuro::decoder::QDA` · part of [Decoder](index.md)

A quadratic discriminant analysis decoder: it classifies a PSD feature with a model stored in a `.r2nd` file.

| | |
|---|---|
| **Layer** | Decoder |
| **Kind** | Plugin of [`ros2neuro_decoder`](index.md) (pluginlib class `ros2neuro::decoder::QDA`) |
| **Reads** | a `NeuroFeature` (a PSD) through the decoder node |
| **Publishes** | a `NeuroPrediction` through the decoder node |
| **Run** | `ros2 run ros2neuro_decoder_qda write_example_qda_model` (writes an example model) |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_decoder`](index.md), [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)

## Messages and topics

Default node name: `decoder` (the node of [`ros2neuro_decoder`](index.md)).

| | Default topic | Type | Changed by |
|---|---|---|---|
| subscribes | `/features` | `NeuroFeature` | `input_topic` |
| publishes | `~/prediction` | `NeuroPrediction` | `output_topic` |

Messages used:

- `NeuroFeature`: read through the decoder node
- `NeuroPrediction`: published through the decoder node

## Example configuration

The configuration shipped with the package (`config/decoder_qda.yaml`); `decoder.manifest_path` points to the model folder, with its `manifest.yaml`:

```yaml
decoder:
  ros__parameters:
    input_topic: "/features"
    output_topic: "~/prediction"
    decoder.manifest_path: /absolute/path/to/my_decoder/manifest.yaml
```

<!-- /interfaces -->
## Runtime configuration

The plugin is loaded through:

- `decoder.type = ros2neuro::decoder::QDA`

and expects one plugin parameter:

- preferred: `decoder.manifest_path` pointing to a decoder folder entrypoint
- legacy fallback: `decoder.params.model_path` pointing directly to a `.r2nd` model artifact

The package also installs a small helper executable:

- `write_example_qda_model`: writes a valid example `.r2nd` artifact

An example node configuration is available in `config/decoder_qda.yaml`.

## QDA model implementation

`ros2neuro_decoder_qda` uses the same generic `.r2nd` decoder container described in the
main [ros2neuro_decoder README](index.md).

Inside that container, `QDA` expects:

- `decoder.type = ros2neuro::decoder::QDA`
- `decoder.parameterization = quadratic_discriminants`
- final QDA inference coefficients stored as `quadratic_weights`, `linear_weights`, and `bias`

The optional `training` block is supported for traceability and can contain fields such as:

- `training.priors`
- `training.regularization.method`
- `training.regularization.lambda`
- `training.solver`
- `training.source`

These values document the training procedure only. The runtime decoder does not rebuild
QDA statistics from them.

### QDA parameter semantics

The `.r2nd` file stores the final quadratic discriminant parameters of a trained QDA model.

For each class `k`, the runtime computes:

```text
delta_k(x) = bias[k] + linear_weights[k]^T x + x^T quadratic_weights[k] x
```

where:

- `x` is the input feature vector extracted from `NeuroFeature.data` in `selection` order
- `linear_weights` is stored in row-major class-major order
- `quadratic_weights` is stored in row-major class-major matrix order
- `bias[k]` is the class intercept

So the serialized parameters must already be the final inference coefficients exported
from training. They are not raw covariance matrices, means, or other intermediate
training statistics.

If `output.type = NeuroPrediction::TYPE_PROBABILITIES`, the runtime applies a softmax
to the class discriminant scores.

## Writer API

The package exposes a small public C++ API in
`QDAModel.h`:

- `ros2neuro::decoder::QDAModel`
- `ros2neuro::decoder::write_r2nd_qda(...)`
- `ros2neuro::decoder::read_r2nd_qda(...)`

This serializer/deserializer is reused by the decoder itself and by the package tests.

The current implementation supports:

- `NeuroFeature::TYPE_SPECTRUM`
- tensor layout `[channels, frequency]`
- row-major flattening
- output types `NeuroPrediction::TYPE_SCORES` and `NeuroPrediction::TYPE_PROBABILITIES`
