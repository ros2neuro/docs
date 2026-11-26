# scikit-learn decoder

!!! info ""
    Package: [`ros2neuro_decoder_sklearn`](https://github.com/ros2neuro/ros2neuro_decoder_sklearn) · part of [Decoder](index.md)

Decoder plugin for [scikit-learn](https://scikit-learn.org) models: any estimator or `Pipeline` with `predict_proba`, saved with
[skops](https://skops.readthedocs.io). It runs inside the C++ decoder node of [`ros2neuro_decoder`](index.md)
and is configured like every decoder: the node is given the `manifest.yaml` of the model, whose `decoder.type` picks this plugin.

| | |
|---|---|
| **Plugin** | `ros2neuro::decoder::Sklearn` (base [`ros2neuro::decoder::Decoder`](index.md)) |
| **Input** | a 2-D `NeuroFeature` of the type of `input.type`: a spectrum `[channels, frequency]` (the `Welch` plugin of [`ros2neuro_processing_spectral`](../processing/spectral.md)) or a window `[time, channels]` (the `Buffer` plugin of [`ros2neuro_processing_buffer`](../processing/buffer.md)), or the FBCSP features `[band, component]` ([`ros2neuro_processing_fbcsp`](../processing/fbcsp.md)) |
| **Output** | `NeuroPrediction`: `predict_proba` of the model, in the order of `output.fields`, header of the feature |
| **Run** | `ros2 run ros2neuro_decoder decoder_node --ros-args -p decoder.manifest:=<model>/manifest.yaml` (like every decoder) |

## How it works

pluginlib loads only C++ classes, so the plugin is C++ and the model runs in Python inside it: the plugin starts a Python interpreter in the
decoder node (pybind11), imports `ros2neuro_decoder_sklearn.SklearnModel` (installed by this package) and calls it.

- `configure()` reads the manifest and loads the model with skops. skops refuses the types it does not know unless they are trusted: the
  model is the one you configured, so its types are trusted and **listed in the log** (`skops: trusting the type ...`). A missing manifest or
  model, a model without `predict_proba` or an `output.fields` class that the model does not have give an error and `configure` false (the node
  exits with 1), never a crash.
- `predict()` reorders the feature to the axes of the manifest: channels **by label**, frequencies **by value** (the node may publish them in
  another order or have more of them), takes the whole feature (`features.mode: all`, row-major: axis 0 major, as it was given to `fit`) or the
  pairs of `features.selection`, and calls `predict_proba`. The probabilities are returned in the order of `output.fields`, whatever the order of
  `model.classes_`. A missing channel or frequency, another number of features or another feature type give an error for that feature (the node
  logs it and goes on).
- The data go to Python as float32 bytes and numpy builds the array there (no numpy API of pybind11: Ubuntu 24.04 has pybind11 2.11, which
  does not support numpy 2). The interpreter is started once per process and never finalized.

## The model folder

`manifest.yaml` + the `.skops` file:

```yaml
decoder:
  name: sklearn_lda_test_gdf
  type: ros2neuro::decoder::Sklearn          # the plugin (read by the node)
  path: model.skops                          # the model, next to the manifest
input:
  name: psd
  type: NeuroFeature::TYPE_SPECTRUM          # or NeuroFeature::TYPE_TIME_SERIES
  unit: ln(power/Hz)
  axes:                                      # the two axes of the feature, in this order
    - name: channels
      labels: [Fz, FC3, ...]
    - name: frequency
      values: [4, 6, ..., 48]
features:
  mode: all                                  # all | selection
  # selection: {channels: [C3, C4], frequencies: [12, 12]}   (mode selection: these pairs, in this order)
output:
  fields: ['773', '771']                     # every one must be in model.classes_ (as text)
  type: NeuroPrediction::TYPE_PROBABILITIES
```

For a window `[time, channels]` the axes are `{name: time}` (taken as it is) and `{name: channels, labels: [...]}`; use `mode: all`.

To make your own: fit the model on the features **as ROS 2 computes them** (same filters, same PSD), flattened the same way
(`feature.reshape(-1)` of the `[axis 0, axis 1]` array), then `skops.io.dump(model, 'model.skops')` and write the manifest.
`scripts/train_example_model.py` does all of it for the example and is the template.

## The example model

`extra/sklearn_lda_test_gdf/`: `StandardScaler` + `LinearDiscriminantAnalysis(solver='lsqr', shrinkage='auto')` on the PSD of
`ros2neuro_devel_test/data/test.gdf` computed as the chain of [`ros2neuro_devel_test`](../../reproducibility/packages/index.md) (`pipeline/qda/config/psd_pipeline.yaml`: Laplacian, Welch Hamming 256 / overlap
128 on a buffer of 512, ln, 4:2:48 Hz), one feature per frame of the continuous feedback of the 20 trials 773 / 771 (1486 features).
Leave-one-trial-out accuracy on the single windows: 0.68. It exercises the plugin; it is not a validated classifier.

```bash
python3 scripts/train_example_model.py     # rewrites extra/sklearn_lda_test_gdf and the reference of the tests (needs mne)
```

## Parameters

Of the decoder node, the same as every decoder:

- `decoder.manifest`: the `manifest.yaml` of the model
- `input_topic`, `output_topic` (or remaps)

Of the plugin (`decoder.params.*`):

- `model_path` (string): the model folder or its `manifest.yaml`, only when the node has no `decoder.manifest`

## Example

`config/sklearn.yaml`:

```yaml
/decoder:
    ros__parameters:
        input_topic: /processing/psd
        output_topic: /classification/prediction
        decoder.manifest: /path/to/sklearn_lda_test_gdf/manifest.yaml
```

## Dependencies

- ROS 2: [`ros2neuro_decoder`](index.md), [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs), `pluginlib`, `rclcpp`; build: `pybind11-dev`, `python3-dev`.
- Python: scikit-learn, skops, numpy, PyYAML: `pip install -r requirements.txt` (skops is not a Debian package; load a model with the
  scikit-learn version it was saved with). The training script also needs `mne`.
