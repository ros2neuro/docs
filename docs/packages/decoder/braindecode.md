# Braindecode decoder (plugin)

!!! info ""
    Package: [`ros2neuro_decoder_braindecode`](https://github.com/ros2neuro/ros2neuro_decoder_braindecode) · part of [Decoder](index.md)

Decoder plugin for deep-learning models made with [braindecode](https://braindecode.org) (PyTorch). It runs inside the C++ decoder node of
[`ros2neuro_decoder`](index.md), like LDA, QDA, SVM and Gaussian, and reads the **same model folders** as
the model in plain Python: on the same features the plugin gives the same probabilities (checked against a run of 956 predictions,
difference 0).

| | |
|---|---|
| **Plugin** | `ros2neuro::decoder::Braindecode` (base [`ros2neuro::decoder::Decoder`](index.md)) |
| **Input** | `NeuroFeature` `TYPE_TIME_SERIES`, shape `[samples, channels]`, axis 1 = channel labels (what the `Buffer` plugin of [`ros2neuro_processing_buffer`](../processing/buffer.md) publishes) |
| **Output** | `NeuroPrediction`: one value per class of the model (`output.fields`), type `output.type` of the manifest, header of the feature |
| **Run** | `ros2 run ros2neuro_decoder decoder_node --ros-args -p decoder.manifest:=<model>/manifest.yaml` (like every decoder) |

## How it works

pluginlib loads only C++ classes, so the plugin is C++ and the model runs in Python inside it: the plugin starts a Python interpreter in the
decoder node (pybind11), imports `ros2neuro_decoder_braindecode.BraindecodeModel` (installed by this package) and calls it.

- `configure()` loads the model: reads `manifest.yaml`, builds `decoder.target` with `decoder.config`, loads `decoder.parameters_file`. A missing
  folder, a broken manifest or weights that do not fit give an error in the log and `configure` false (the node exits with 1), never a crash.
- `predict()` takes the channels **by label** in the order of the model (`input.axes[1].labels`): the feature may have them in another order or
  have more channels. A channel of the model that is missing, a shape other than `input.shape` or a feature type other than `input.type` give an
  error for that feature (the node logs it and goes on).
- The samples go to Python as float32 bytes and numpy builds the array there: the plugin does not depend on the numpy version pybind11 was built
  for (Ubuntu 24.04 has pybind11 2.11, which does not support numpy 2).
- The interpreter is started once per process and never finalized (finalizing it while the node still holds Python objects is what makes
  embedded Python crash at exit).

## The model folder

A folder with `manifest.yaml` + the weights. It is given like the model of every decoder, with
`decoder.manifest` of the decoder node: the node reads only `decoder.name` and `decoder.type` (which picks this plugin) and passes the
manifest to the plugin, which reads the rest:

```yaml
decoder:
  name: eegnet_mi_bhbf
  type: ros2neuro::decoder::Braindecode        # the plugin (read by the node)
  wrapper: EEGClassifier                       # descriptive (what was `type` before; nobody reads it)
  target: braindecode.models.ShallowFBCSPNet   # the class of the network
  config: {...}                                # its arguments
  parameters_file: params.pt                   # the weights (state_dict)
input:
  type: NeuroFeature::TYPE_TIME_SERIES
  shape: [512, 16]                             # [samples, channels]
  axes: [{name: time}, {name: channels, labels: [FZ, FC1, ...]}]
output:
  fields: [BOTH_HANDS, BOTH_FEET]
  type: NeuroPrediction::TYPE_PROBABILITIES
```

`extra/eegnet_mi_bhbf/` is an example (ShallowFBCSPNet, 16 channels, 512 samples, BOTH_HANDS / BOTH_FEET), trained on the
recording `test_mi.gdf` of `ros2neuro_devel_test/data`.

!!! note "Older manifests"
    A manifest written by an older training script may still have `type: EEGClassifier`: write `type: ros2neuro::decoder::Braindecode`
    there (the old value can stay as `wrapper: EEGClassifier`: nobody reads it).

## Parameters

Of the decoder node, the same as every decoder:

- `decoder.manifest`: the `manifest.yaml` of the model (its `decoder.type` picks this plugin, its `decoder.name` goes in `NeuroPrediction.decoder`)
- `input_topic`, `output_topic` (or remaps)

Of the plugin (`decoder.params.*`):

- `device` (string, optional): `cpu` or `cuda`; empty = `cuda` when available
- `model_path` (string): the model folder or its `manifest.yaml`, only when the node has no `decoder.manifest`

## Example

`config/braindecode.yaml`:

```yaml
/decoder:
    ros__parameters:
        input_topic: /processing/buffered_features
        output_topic: /classification/prediction
        decoder.manifest: /path/to/eegnet_mi_bhbf/manifest.yaml
        decoder.params.device: cpu
```

The whole chain (GDF replay, filters 4-14 Hz, buffer of 512 samples, this plugin, integrator, control) is the test `decoder/shallow/` of [`ros2neuro_devel_test`](../devel-test.md):
MATLAB checks the filter and the window the network reads, and `check_decoder_shallow.py` compares the probabilities with PyTorch:

```bash
cd ros2neuro_devel_test
ros2 launch ros2neuro_devel_test decoder_shallow.launch.py   # then check_decoder_shallow in MATLAB
```

## Dependencies

- ROS 2: [`ros2neuro_decoder`](index.md), [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs), `pluginlib`, `rclcpp`; build: `pybind11-dev`, `python3-dev`.
- Python (not Debian packages): `pip install -r requirements.txt` (torch, braindecode, numpy, PyYAML).

## Tests

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

## Python replication

A deep network cannot be redone with the MATLAB functions: it is replayed in **Python**, with braindecode / PyTorch written outside the plugin, and compared with the probabilities ROS 2 published (`check_decoder_shallow.py` and `check_pipeline_dl.py` in [`ros2neuro_devel_test`](../devel-test.md)). See [Reproducibility in Python](../../reproducibility/python.md).

```python
import importlib, torch, yaml
manifest = yaml.safe_load(open('manifest.yaml'))
dec = manifest['decoder']
module, name = dec['target'].rsplit('.', 1)
net = getattr(importlib.import_module(module), name).from_config(dec['config'])
net.load_state_dict(torch.load('params.pt', map_location='cpu', weights_only=True))
net.eval()
with torch.no_grad():                      # window: [1, channels, samples], the channels of the manifest picked by label
    p = torch.softmax(net(window).double(), dim=1)      # probabilities, one per class
```
