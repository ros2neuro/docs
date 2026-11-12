# scikit-learn decoder (plugin)

!!! info ""
    Package: [`ros2neuro_decoder_sklearn`](https://github.com/ros2neuro/ros2neuro_decoder_sklearn) · part of [Decoder](index.md)

Decoder plugin for [scikit-learn](https://scikit-learn.org) models: any estimator or `Pipeline` with `predict_proba`, saved with
[skops](https://skops.readthedocs.io). It runs inside the C++ decoder node of [`ros2neuro_decoder`](index.md)
and is configured like every decoder: the node is given the `manifest.yaml` of the model, whose `decoder.type` picks this plugin.

| | |
|---|---|
| **Plugin** | `ros2neuro::decoder::Sklearn` (base `ros2neuro::decoder::Decoder`) |
| **Input** | a 2-D `NeuroFeature` of the type of `input.type`: a spectrum `[channels, frequency]` ([`ros2neuro_processing_spectral`](../processing/spectral.md)) or a window `[time, channels]` ([`ros2neuro_processing_buffer`](../processing/buffer.md)) |
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
`ros2neuro_devel_test/extra/test.gdf` computed as the chain of `ros2neuro_devel_test/launch/sklearn` (Laplacian, Welch Hamming 256 / overlap
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

The whole chain (GDF replay, Laplacian, Welch, this plugin, integrator, control, feedback):

```bash
ros2 launch ros2neuro_devel_test sklearn_bars.launch.xml protocol:=evaluation          # 2 classes, features.mode selection
ros2 launch ros2neuro_devel_test sklearn_4class_bars.launch.xml protocol:=evaluation   # 4 classes, RandomForest
```

The launchers of `ros2neuro_devel_test` use their own made-up models (`launch/sklearn/model`, `launch/sklearn_4class/model`, written by its
`scripts/make_sklearn_models.py`); the example model of this package is the one of the tests.

## Dependencies

- ROS 2: `ros2neuro_decoder`, `ros2neuro_msgs`, `pluginlib`, `rclcpp`; build: `pybind11-dev`, `python3-dev`.
- Python: scikit-learn, skops, numpy, PyYAML: `pip install -r requirements.txt` (skops is not a Debian package; load a model with the
  scikit-learn version it was saved with). The training script also needs `mne`.

## Tests

```bash
colcon test --packages-select ros2neuro_decoder_sklearn && colcon test-result --verbose
```

- `test/test_sklearn_decoder.cpp` (the plugin, loaded through pluginlib as the node does): the probabilities of `predict_proba` on two
  reference features of test.gdf (`test/reference_*`, written by the training script), tolerance 1e-6; the model given as the manifest or the
  folder; channels and frequencies reversed or with an extra one (same output); a missing channel or frequency, a time series, a 1-D
  feature (an error); no model, a missing manifest, an `output.fields` class the model does not have (`configure` false, no exception).
- `test/test_sklearn_model.py` (the Python side, on small models fitted in the test): `mode: all` is the feature channel-major whatever the
  order of the axes; `mode: selection` takes the pairs in their order; the probabilities follow `output.fields`, not `model.classes_`; the
  float32 bytes the plugin passes give the same result.
