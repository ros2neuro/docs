# Decoder

!!! info ""
    Package: [`ros2neuro_decoder`](https://github.com/ros2neuro/ros2neuro_decoder)

The decoder package turns a `NeuroFeature` (for example a PSD) into a `NeuroPrediction`. It provides the
`Decoder` plugin interface and `decoder_node`, which loads **one** decoder plugin.

!!! important "Select one plugin"
    The decoder is chosen by its type, for example [`ros2neuro::decoder::Gaussian`](gaussian.md). When you pass a model with
    `decoder.manifest`, the node reads the type from the `manifest.yaml`; otherwise set `decoder.type`.

## Available plugins

| Plugin | pluginlib class / type | Model |
|---|---|---|
| [LDA](lda.md) | [`ros2neuro::decoder::LDA`](lda.md) | linear discriminant analysis |
| [QDA](qda.md) | [`ros2neuro::decoder::QDA`](qda.md) | quadratic discriminant analysis |
| [SVM](svm.md) | [`ros2neuro::decoder::SVM`](svm.md) | support vector machine |
| [Gaussian](gaussian.md) | [`ros2neuro::decoder::Gaussian`](gaussian.md) | Gaussian classifier (ported from Matlab SMR) |

The [converters](converters.md) turn a Matlab SMR `.mat` decoder into the `.r2nd` + `manifest.yaml` format.

!!! note "The Python decoder is not a plugin"
    [`ros2neuro_decoder_py`](python.md) runs deep-learning models (braindecode, torch) as **a separate Python node**, `decoder_node`
    of its own package, not as a pluginlib plugin of this one. It has the same topic contract (`/features` in, `~/prediction` out),
    so the rest of the chain does not notice the difference, but its models are folders with their own `manifest.yaml` and it is
    selected with `decoder.type`, not with a plugin class.

## Topics

| | Topic | Type |
|---|---|---|
| subscribes | `/features` (`input_topic`) | `NeuroFeature` |
| publishes | `~/prediction` (`output_topic`) | `NeuroPrediction` |

## Which processing feeds the decoder

The decoder reads a `NeuroFeature` that the [processing](../processing/index.md) stage publishes, and its model declares which one
(name, type and axes, in the manifest). The classic decoders (LDA, QDA, SVM, Gaussian) read a **PSD**, so they follow the
[Welch node](../processing/spectral.md); a deep-learning model in the [Python decoder](python.md) reads a **window of the
signal**, so it follows the [buffer node](../processing/buffer.md).

## Minimal example

```yaml
/decoder:
  ros__parameters:
    decoder.manifest: "/path/to/model/manifest.yaml"
```

```bash
ros2 run ros2neuro_decoder decoder_node --ros-args --params-file decoder.yaml \
  -r /features:=/processing/psd
```

`decoder.manifest_path` is accepted as an alternative name for `decoder.manifest`.

## Model format

A trained decoder is a folder with a `manifest.yaml` (decoder type, input contract, feature selection, output
fields) and a binary model file, `.r2nd` for the ROS2neuro decoders. The manifest is the runtime entry point.
The details are in the reference below.

---

## Reference (from the package README)

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs), `yaml-cpp`
- **External libraries**:
    - `yaml-cpp`: reading the model `manifest.yaml`
- **At run time**: a decoder plugin package ([`ros2neuro_decoder_lda`](lda.md), `_qda`, `_svm`, `_gaussian`) and a model

## Messages and topics

Default node name: `decoder`.

| | Default topic | Type | Changed by |
|---|---|---|---|
| subscribes | `/features` | `NeuroFeature` | `input_topic` |
| publishes | `~/prediction` | `NeuroPrediction` | `output_topic` |

Messages used:

- `NeuroFeature`: read, the input of the model
- `NeuroPrediction`: published, one value per class

<!-- /interfaces -->
This package is intentionally plugin-oriented. Unlike generic processing blocks, decoders are a natural fit for runtime replacement because different experiments may swap:

- model family: `LDA`, `QDA`, `SVM`, `MLP`, `CNN`
- feature-selection logic
- saved model format
- output interpretation: scores, probabilities, logits

## Architecture

- `ros2neuro_msgs/msg/NeuroFeature`: input to the decoder
- `ros2neuro_msgs/msg/NeuroPrediction`: decoder output
- `ros2neuro::decoder::Decoder`: base plugin interface
- `ros2neuro::decoder::DecoderNode`: ROS 2 node that loads one decoder plugin and applies it to incoming `NeuroFeature` messages

The decoder plugin is responsible for:

- loading its saved model
- interpreting the incoming `NeuroFeature`
- selecting the trained subset of features
- running inference
- returning a `NeuroPrediction`

## NeuroPrediction

The current decoder output message is:

```text
std_msgs/Header header
string          decoder
string[]        fields
float32[]       values
uint8           type
```

Semantics:

- `decoder`: free-form decoder or model provenance
- `fields[i]`: semantic label associated with `values[i]`
- `values`: raw decoder output vector
- `type`: interpretation of `values`

## Runtime Node

The node subscribes to a `NeuroFeature` topic and publishes `NeuroPrediction`.

Default topics:

- input: `/features`
- output: `~/prediction`

Main parameters:

- `input_topic`
- `output_topic`
- `decoder.name`
- `decoder.type`
- `decoder.manifest_path`
- `decoder.params.*`

## Saved Model Layout

The package does not force a single file format, but the intended structure is:

```text
my_decoder/
  manifest.yaml
  model_file
```

The manifest is expected to describe:

- decoder identity
- input feature expectations
- feature-selection definition
- class labels
- preprocessing
- output type
- model file path

Different plugins can then support different model formats while keeping the same runtime ROS contract.

The recommended runtime entrypoint is `manifest.yaml`.

When `decoder.manifest_path` is provided, `DecoderNode` reads decoder identity from the
manifest before instantiating the plugin. The plugin can then resolve the binary model
payload referenced by `decoder.path` and validate manifest and payload consistency.

## `.r2nd` Container

The suggested extension for ROS2neuro decoder model files is `.r2nd`:

- `r2n`: short for `ros2neuro`
- `d`: short for `decoder`

This is the generic decoder container format. Concrete decoder packages can reuse it and
define their own model-specific parameter blocks inside it.

Version 2 stores:

- file magic and version
- decoder name, subject, decoder type, and parameterization
- optional `training` metadata such as priors, regularization, solver, and source
- expected feature name, type, and unit
- expected channel labels and frequency values
- the ordered feature selection used for inference
- output classes and output type
- decoder-specific inference parameters

Version 1 files are still accepted by current readers for backward compatibility. They
simply load with an empty `training` block.

The common intent of the container is:

- `decoder.type`: identify which decoder family should read the file
- `decoder.parameterization`: identify how inference parameters are stored
- `input.*`: define the input contract against `NeuroFeature`
- `features.*`: define the feature set passed to the decoder model
- `output.*`: define the semantic meaning of the produced `NeuroPrediction`
- `training.*`: document how the model was estimated, without forcing the runtime to
  recompute inference coefficients

Typical optional `training` fields are:

- `training.priors`
- `training.regularization.method`
- `training.regularization.lambda`
- `training.solver`
- `training.source`

These fields are descriptive metadata. In general, decoder plugins should perform
runtime inference from the stored final model parameters, not from raw training
statistics unless that is explicitly part of the decoder-specific parameterization.

One possible manifest convention for a spectrum-based decoder is:

```yaml
decoder:
  name: motor_imagery_lda_v1                      # Human-readable decoder name
  subject: subject_01                             # Subject this decoder was trained for
  type: ros2neuro::decoder::LDA            # Semantic decoder type
  path: model.bin                                 # Path to the serialized model artifact relative to the manifest

input:
  name: psd_welch                                 # Expected NeuroFeature.name
  type: NeuroFeature::TYPE_SPECTRUM               # Expected NeuroFeature.type
  unit: uV2/Hz                                    # Expected unit for NeuroFeature.data
  order: row_major                                # Flattening convention used for feature.data
  axes:                                           # Expected semantic axes of the incoming NeuroFeature
    - name: channels                              # First tensor dimension represents channels
      labels: [C3, Cz, C4]                        # Required channel labels in the feature axis
    - name: frequency                             # Second tensor dimension represents frequency bins
      values: [8.0, 10.0, 12.0, 18.0, 20.0, 22.0] # Required frequency coordinates in Hz
      unit: Hz                                    # Unit associated with the frequency axis

features:
  mode: selection                                 # Decoder consumes an ordered feature subset
  selection:                                      # Ordered subset extracted from the feature tensor for inference
    channels: [C3, C3, Cz, C4]
    frequencies: [8.0, 10.0, 10.0, 20.0]

preprocessing:
  # TODO: optional preprocessing metadata, for example normalization or scaling parameters

output:
  fields: [idle, active]                          # Fields associated with the decoder output
  type: NeuroPrediction::TYPE_PROBABILITIES       # Semantic meaning of the output vector
```

The manifest can use semantic type names such as [`ros2neuro::decoder::LDA`](lda.md).
The current runtime ROS parameter `decoder.type` uses the same pluginlib lookup key, for example
`ros2neuro::decoder::LDA` for the LDA decoder plugin.

## Plugin Interface

Each decoder plugin derives from:

```cpp
ros2neuro::decoder::Decoder
```

and implements:

- `configure()`
- `predict(const ros2neuro_msgs::msg::NeuroFeature&)`

### `LDA` v1 Contract

For a first concrete implementation, [`ros2neuro::decoder::LDA`](lda.md) can target the
manifest convention above and support one well-defined input layout:

- `input.type = NeuroFeature::TYPE_SPECTRUM`
- `input.order = row_major`
- `input.axes = [channels, frequency]`
- `features.mode = selection`
- `features.selection` as an ordered set of `(channel, frequency)` entries

#### `configure()`

During `configure()`, the decoder should:

- read the decoder identity fields: `decoder.name`, `decoder.subject`, `decoder.type`, `decoder.path`
- validate that `decoder.type` matches the decoder implementation
- resolve `decoder.path` relative to the manifest location
- load the serialized model artifact from `decoder.path`
- read and validate `input.name`
- read and validate `input.type`
- read and validate `input.unit` when present
- require `input.order = row_major`
- require exactly two feature axes
- require one axis named `channels` with non-empty `labels`
- require one axis named `frequency` with non-empty `values`
- require `features.mode = selection`
- read and validate every `features.selection` entry
- read and validate `output.fields`
- read and validate `output.type`
- verify that the model input dimension matches `features.selection.size()`
- verify that the model output dimension matches `output.fields.size()`
- keep preprocessing as optional and unimplemented for now

If any of these checks fails, `configure()` should return `false` and log a precise error.

#### `predict()`

During `predict()`, the decoder should:

- validate `feature.name` against the configured `input.name`
- validate `feature.type` against the configured `input.type`
- validate `feature.unit` when the manifest declares one
- validate `feature.shape.size() == 2`
- validate `feature.axes.size() == feature.shape.size()`
- validate `feature.data.size() == feature.shape[0] * feature.shape[1]`
- locate the `channels` axis and validate its labels against the incoming feature
- locate the `frequency` axis and validate its values against the incoming feature
- build an input vector by extracting entries from `feature.data` in the exact order defined by `features.selection`
- apply preprocessing only when that part of the contract is implemented
- run the LDA inference on the extracted vector
- fill `NeuroPrediction.header` from the input feature header
- fill `NeuroPrediction.decoder` from the configured decoder or model provenance
- fill `NeuroPrediction.fields` from `output.fields`
- fill `NeuroPrediction.type` from `output.type`
- fill `NeuroPrediction.values` with the raw decoder scores, probabilities, logits, or regression values

Any runtime mismatch between the configured contract and the incoming feature should raise
an exception or produce a clear logged error instead of silently decoding the wrong tensor.

#### Feature Extraction Rule

For `shape = [n_channels, n_frequencies]` and `input.order = row_major`, the flattened index is:

```text
index = channel_index * n_frequencies + frequency_index
```

So a selection entry:

```yaml
- channel: Cz
  frequency: 10.0
```

means:

- find `channel_index` by matching `axes[channel_axis].labels[channel_index] == "Cz"`
- find `frequency_index` by matching `axes[frequency_axis].values[frequency_index] == 10.0`
- read `data[index]`

The extracted values are appended to the model input vector in manifest order.

`features.selection` supports both a compact column-oriented form:

```yaml
features:
  mode: selection
  selection:
    channels: [C3, C3, Cz, C4]
    frequencies: [8.0, 10.0, 10.0, 20.0]
```

and an explicit row-oriented form:

```yaml
features:
  mode: selection
  selection:
    - channel: C3
      frequency: 8.0
    - channel: C3
      frequency: 10.0
    - channel: Cz
      frequency: 10.0
    - channel: C4
      frequency: 20.0
```

For spectrum decoders, `channel`/`channels` and `frequency`/`frequencies` are the
current convention and refer to the `input.axes` entries named `channels` and
`frequency`.

## Testing

The package includes a small passthrough test decoder exported through `pluginlib` to verify that:

- plugins are discoverable
- parameter configuration works
- a `NeuroPrediction` can be produced from a `NeuroFeature`
