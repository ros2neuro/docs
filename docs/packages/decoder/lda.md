# LDA decoder

!!! info ""
    Package: [`ros2neuro_decoder_lda`](https://github.com/ros2neuro/ros2neuro_decoder_lda) · pluginlib class: `ros2neuro::decoder::LDA` · part of [Decoder](index.md)

`ros2neuro_decoder_lda` provides a first concrete decoder plugin for [`ros2neuro_decoder`](index.md).

## Runtime configuration

The plugin is loaded through:

- `decoder.type = ros2neuro::decoder::LDA`

and expects one plugin parameter:

- preferred: `decoder.manifest_path` pointing to a decoder folder entrypoint
- legacy fallback: `decoder.params.model_path` pointing directly to a `.r2nd` model artifact

The package also installs a small helper executable:

- `write_example_lda_model`: writes a valid example `.r2nd` artifact

An example node configuration is available in `config/decoder_lda.yaml`.

## LDA model implementation

`ros2neuro_decoder_lda` uses the generic `.r2nd` decoder container described in the
main [ros2neuro_decoder README](index.md).

Inside that container, `LDA` expects:

- `decoder.type = ros2neuro::decoder::LDA`
- `decoder.parameterization = linear_discriminants`
- final LDA inference coefficients stored as `weights` and `bias`

The optional `training` block is supported for traceability and can contain fields such as:

- `training.priors`
- `training.regularization.method`
- `training.regularization.lambda`
- `training.solver`
- `training.source`

These values document the training procedure only. The runtime decoder does not recompute
LDA parameters from them.

### LDA parameter semantics

The `.r2nd` file stores the final linear discriminant parameters of a trained LDA model.

For each class `k`, the runtime computes:

```text
delta_k(x) = bias[k] + sum_j weights[k * n_features + j] * x_j
```

where:

- `n_features = selection.size()`
- `x_j` is the input feature vector extracted from `NeuroFeature.data` in `selection` order
- `weights` is stored in row-major class-major order
- `bias[k]` is the intercept of class `k`

So `weights` and `bias` must already be the final LDA decision-function coefficients
exported from training. They are not raw class means, covariance matrices, or other
intermediate training statistics.

If `output.type = NeuroPrediction::TYPE_PROBABILITIES`, the runtime applies a softmax
to the class discriminant scores. This is appropriate when the stored scores are the
complete LDA discriminants including the effect of class priors.

## Writer API

The package exposes a small public C++ API in
`LDAModel.h`:

- `ros2neuro::decoder::LDAModel`
- `ros2neuro::decoder::write_r2nd_lda(...)`
- `ros2neuro::decoder::read_r2nd_lda(...)`

This is the official serializer/deserializer for `.r2nd` artifacts and is reused by the
decoder itself and by the package tests.

The current implementation supports:

- `NeuroFeature::TYPE_SPECTRUM`
- tensor layout `[channels, frequency]`
- row-major flattening
- output types `NeuroPrediction::TYPE_SCORES` and `NeuroPrediction::TYPE_PROBABILITIES`
