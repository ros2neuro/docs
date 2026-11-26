# Decoder: tests and replication

!!! info ""
    Plugins: [Decoder](../../packages/decoder/index.md) · part of [Reproducibility](../index.md) › [Packages](index.md)

How the decoder is checked: every decoder reads the PSD (or the feature) that ROS 2 published and its probabilities are compared with the function that opens the same model and predicts. The deep-learning model is replayed in Python, with PyTorch.

| Test (`ros2neuro_devel_test`) | What it checks | Check | MATLAB functions | Python functions |
|---|---|---|---|---|
| `decoder/qda/` | QDA | `check_decoder_qda` | [`r2n_qda_read`](../matlab.md#r2n_qda_read), [`r2n_qda_predict`](../matlab.md#r2n_qda_predict), [`r2n_softmax`](../matlab.md#r2n_softmax) | [`r2n_qda_read`](../python.md#r2n_qda_read), [`r2n_qda_predict`](../python.md#r2n_qda_predict), [`r2n_softmax`](../python.md#r2n_softmax) |
| `decoder/lda/` | LDA | `check_decoder_lda` | [`r2n_linear_read`](../matlab.md#r2n_linear_read), [`r2n_linear_predict`](../matlab.md#r2n_linear_predict), [`r2n_softmax`](../matlab.md#r2n_softmax) | [`r2n_linear_read`](../python.md#r2n_linear_read), [`r2n_linear_predict`](../python.md#r2n_linear_predict), [`r2n_softmax`](../python.md#r2n_softmax) |
| `decoder/gaussian/` | Matlab SMR Gaussian classifier | `check_decoder_gaussian` | [`r2n_gaussian_read`](../matlab.md#r2n_gaussian_read), [`r2n_gaussian_predict`](../matlab.md#r2n_gaussian_predict) | [`r2n_gaussian_read`](../python.md#r2n_gaussian_read), [`r2n_gaussian_predict`](../python.md#r2n_gaussian_predict) |
| `decoder/fbcsp_lda/` | LDA (scikit-learn) on FBCSP | `check_decoder_fbcsp` | [`r2n_sklearn_lda_read`](../matlab.md#r2n_sklearn_lda_read), [`r2n_sklearn_lda_predict`](../matlab.md#r2n_sklearn_lda_predict)|[`r2n_sklearn_load`](../python.md#r2n_sklearn_load), [`r2n_sklearn_predict`](../python.md#r2n_sklearn_predict) |
| `decoder/shallow/` | ShallowNet (deep learning) | `check_decoder_shallow.py` | none | [`r2n_braindecode_load`](../python.md#r2n_braindecode_load), [`r2n_braindecode_predict`](../python.md#r2n_braindecode_predict) |

How to run a test: [Packages](index.md#run-the-checks). Every function is explained, with its code, in [MATLAB](../matlab.md) and [Python](../python.md); [download them](../download.md).

## Decoder (base package)

### Testing

The package includes a small passthrough test decoder exported through `pluginlib` to verify that:

- plugins are discoverable
- parameter configuration works
- a `NeuroPrediction` can be produced from a `NeuroFeature`

### Tests of the whole stack

[`ros2neuro_devel_test`](https://github.com/ros2neuro/ros2neuro_devel_test) (`decoder/`) tests some decoders (QDA, LDA, the Matlab SMR Gaussian classifier, LDA on FBCSP, ShallowNet) on the feature of the stage before, against MATLAB (the deep network against PyTorch). `pipeline/` runs complete pipelines with a QDA, an LDA, FBCSP + LDA and ShallowNet. Run: `decoder/<d>/decoder_<d>.launch.py` then `check_decoder_<d>` for `qda`, `lda`, `gaussian`, `fbcsp_lda`, `shallow`; the check is a MATLAB file you read from the top (see the README of that package).

## Braindecode decoder (plugin)

```bash
colcon test --packages-select ros2neuro_decoder_braindecode && colcon test-result --verbose
```

`test/test_braindecode_decoder.cpp` loads the plugin through pluginlib, as the node does:

- **the probabilities of the model in plain Python**: two fixed windows (`test/reference_input_*.csv`) and the probabilities that
  the model gives for them outside ROS 2 (`test/reference_output.csv`, about 0.78 and 0.32 for BOTH_HANDS: a channel in the wrong place
  would change them), tolerance 1e-5; regenerate them with `python3 test/make_reference.py`;
- channels taken by label (reversed order, an extra channel: same output);
- a missing channel, a short window, a spectrum, no labels: an error, not a wrong number;
- the model given as the manifest (what the node passes) or as the folder: the same model;
- no model or a folder that does not exist: `configure` false, no exception.

## scikit-learn decoder (plugin)

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

## scikit-learn decoder: the chain on FBCSP

The package [`ros2neuro_devel_test`](index.md) tests the plugin on a real chain: `decoder/fbcsp_lda/` replays a GDF through four band filter chains, the `Fbcsp` plugin,
this decoder (a test LDA on FBCSP features, `data/models/fbcsp_lda/`, a `TYPE_MATRIX` input), the integrator and the control, and its `check_decoder_fbcsp.m` redoes the
LDA in MATLAB from the numbers in `lda_weights.yaml`:

```bash
cd ros2neuro_devel_test
ros2 launch ros2neuro_devel_test decoder_fbcsp_lda.launch.py   # then check_decoder_fbcsp in MATLAB
```

The model of `lda_psd` (`data/models/lda_psd/sklearn/`) is the same LDA on the PSD as a scikit-learn file; the example model of this package is the one of the tests.

## Braindecode decoder: the chain with a ShallowNet

The whole chain (GDF replay, filters 4-14 Hz, buffer of 512 samples, this plugin, integrator, control) is the test `decoder/shallow/` of [`ros2neuro_devel_test`](index.md):
MATLAB checks the filter and the window the network reads, and `check_decoder_shallow.py` compares the probabilities with PyTorch:

```bash
cd ros2neuro_devel_test
ros2 launch ros2neuro_devel_test decoder_shallow.launch.py   # then check_decoder_shallow in MATLAB
```

## Decoder converters: check a converted classifier against Matlab

`test/` holds a check that the converted classifier gives the same output in ROS 2 as in Matlab: `check_decoder.launch.py` replays a GDF through
the pipeline (Laplacian filter, Welch, decoder) and `record_features.py` saves the PSD, the features the classifier uses and its probabilities in a CSV;
`check_decoder.m` repeats the processing in Matlab, compares and plots. In the ROS 2 container, with the workspace sourced:

```bash
ros2 launch ros2neuro_decoder_converters check_decoder.launch.py          # the example of this package
ros2 launch ros2neuro_decoder_converters check_decoder.launch.py manifest:=<manifest.yaml> \
    mat_file:=<classifier.smr.mat> gdf_file:=<recording.gdf> output_csv:=<ros_features.csv>
```

Without arguments it uses the example installed with the package (`share/ros2neuro_decoder_converters/test_data`: a classifier, the model converted
from it and a GDF; `test/data` in the sources). It replays the GDF in real time and ends by itself, writing `ros_features.csv` in the current
folder (`output_csv:=...` to change it). Then in Matlab run `check_decoder(mat_file, gdf_file, 'ros_features.csv')`, or just `check_decoder` from
`test/` with the example. The model must have been converted with the unit of the Welch node (`ln(power/Hz)`, the default).
