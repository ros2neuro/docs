# Gaussian decoder

!!! info ""
    Package: [`ros2neuro_decoder_gaussian`](https://github.com/ros2neuro/ros2neuro_decoder_gaussian) · pluginlib class: `ros2neuro::decoder::Gaussian` · part of [Decoder](index.md)

`ros2neuro_decoder_gaussian` provides a diagonal Gaussian prototype decoder plugin for
[`ros2neuro_decoder`](index.md), reimplemented from the legacy `rosneuro_decoder_gaussian` package
using the same core algorithm inside the ROS 2 plugin structure used by the other decoders.

| | |
|---|---|
| **Layer** | Decoder |
| **Kind** | Plugin of [`ros2neuro_decoder`](index.md) (pluginlib class `ros2neuro::decoder::Gaussian`) |
| **Reads** | a `NeuroFeature` (a PSD) through the decoder node |
| **Publishes** | a `NeuroPrediction` through the decoder node |
| **Run** | `ros2 run ros2neuro_decoder_gaussian write_example_gaussian_model` (writes an example model) |

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

The configuration shipped with the package (`config/decoder_gaussian.yaml`); `decoder.manifest_path` points to the model folder, with its `manifest.yaml`:

```yaml
decoder:
  ros__parameters:
    input_topic: "/features"
    output_topic: "~/prediction"
    decoder.manifest_path: /absolute/path/to/my_decoder/manifest.yaml
```

<!-- /interfaces -->
## Legacy algorithm summary

The old package implements a classifier with:

- one or more Gaussian prototypes per class
- diagonal covariance for each prototype
- per-class activity equal to the sum of its prototype activities
- final probabilities obtained by normalizing the class activities

For class `k`, prototype `p`, and selected feature vector `x`, the activity is:

```text
activity_k,p(x) = exp(-0.5 * sum_j ((x_j - center_j)^2 / covariance_j)) /
                  prod_j sqrt(covariance_j)
```

Then:

```text
raw_score_k = sum_p activity_k,p
probability_k = raw_score_k / sum_c raw_score_c
```

This implementation preserves that inference rule.

## Runtime configuration

The plugin is loaded through:

- `decoder.type = ros2neuro::decoder::Gaussian`

and can be configured in two ways:

- preferred: `decoder.manifest_path` at node level, pointing to a decoder folder entrypoint
- legacy fallback: `decoder.params.model_path` pointing directly to a `.r2nd` model artifact

When `manifest.yaml` is used, the runtime resolves the `.r2nd` file from `decoder.path`
inside the manifest and validates that manifest and binary agree on the critical fields:

- decoder identity
- feature contract
- selected channels/frequencies
- output classes/type

The package also installs a small helper executable:

- `write_example_gaussian_model`: writes a valid example `.r2nd` artifact

An example node configuration is available in `config/decoder_gaussian.yaml`.

## Gaussian model implementation

Inside the generic `.r2nd` container, `Gaussian` expects:

- `decoder.type = ros2neuro::decoder::Gaussian`
- `decoder.parameterization = gaussian_diagonal_prototypes`
- `prototype_count`
- flattened `centers` and `covariances` tensors for `[class][prototype][feature]`

The optional `training` block is supported for traceability and can contain fields such as:

- `training.priors`
- `training.regularization.method`
- `training.regularization.lambda`
- `training.solver`
- `training.source`

These values document the training procedure only. The runtime decoder uses the stored
final prototype parameters directly.

## Writer API

The package exposes a small public C++ API in
`GaussianModel.h`:

- `ros2neuro::decoder::GaussianModel`
- `ros2neuro::decoder::write_r2nd_gaussian(...)`
- `ros2neuro::decoder::read_r2nd_gaussian(...)`

This serializer/deserializer is reused by the decoder itself and by the package tests.

The current implementation supports:

- `NeuroFeature::TYPE_SPECTRUM`
- tensor layout `[channels, frequency]`
- row-major flattening
- output types `NeuroPrediction::TYPE_SCORES` and `NeuroPrediction::TYPE_PROBABILITIES`
