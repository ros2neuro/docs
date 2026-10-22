# Python decoder (deep learning)

!!! info ""
    Package: [`ros2neuro_decoder_py`](https://github.com/ros2neuro/ros2neuro_decoder_py) · part of [Decoder](index.md)

A Python decoder node for machine-learning and deep-learning models (for example a `braindecode` ShallowFBCSPNet). It listens to `NeuroFeature` messages that carry a window of the signal, runs the model and publishes a `NeuroPrediction` with class probabilities. It has the same topic contract as the C++ decoder but is **a separate node, not a pluginlib plugin**.

| | |
|---|---|
| **Layer** | Decoder |
| **Kind** | Python node (`decoder_node`, installed by this package); models are folders with their own `manifest.yaml` |
| **Reads** | `/features` (`NeuroFeature`, parameter `input_topic`; the models of the stack read the window of [`ros2neuro_processing_buffer`](../processing/buffer.md)) |
| **Publishes** | `~/prediction` (`NeuroPrediction`, `TYPE_PROBABILITIES`, parameter `output_topic`) |
| **Run** | `ros2 launch ros2neuro_decoder_py example_decoder.launch.xml` (starts the whole chain: GDF replay, filters, buffer, this decoder, and optionally a visualizer and a recorder) |
| **Parameters** | `decoder.type` (`braindecode`), `decoder.model_path`, `decoder.name` |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `rclpy`, [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)
- **External libraries**:
    - `braindecode`, `torch`: the deep-learning models
    - `numpy`, `PyYAML`, `skops`: arrays, the manifest and the (incomplete) scikit-learn support
    - Python virtual environment: recommended: see the setup instructions below

## Messages and topics

Default node name: `ros2neuro_decoder_py`.

| | Default topic | Type | Changed by |
|---|---|---|---|
| subscribes | `/features` | `NeuroFeature` | `input_topic` |
| publishes | `~/prediction` | `NeuroPrediction` | `output_topic` |

Messages used:

- `NeuroFeature`: read, a window of the signal
- `NeuroPrediction`: published, `TYPE_PROBABILITIES`

## Example configuration

From the EEGNet pipeline of [`ros2neuro_devel_test`](../devel-test.md):

```yaml
/decoder:
  ros__parameters:
    decoder.type: braindecode
    decoder.model_path: /path/to/ros2neuro_decoder_py/extra/eegnet_mi_bhbf   # the folder of the model
    decoder.name: eegnet_bhbf
```

<!-- /interfaces -->
## How it works

`decoder_node` (node name `ros2neuro_decoder_py`) is the Python counterpart of the decoder node of [`ros2neuro_decoder`](index.md): it
listens to `NeuroFeature` messages, runs a model on them and publishes a `NeuroPrediction` with the class probabilities
(`TYPE_PROBABILITIES`) and the header of the feature. It lets a deep-learning model, trained with `braindecode` and `torch`, run
inside the ROS2neuro loop.

It is **a separate node and not a pluginlib plugin of [`ros2neuro_decoder`](index.md)**: the topics are the same (`/features` in,
`~/prediction` out), so the integrator and the rest of the chain do not notice the difference, but the models are different
(see below) and are selected with `decoder.type`, not with a manifest type.

The input is a **window of the filtered signal**: the `NeuroFeature` published by [`ros2neuro_processing_buffer`](../processing/buffer.md)
(`TYPE_TIME_SERIES`, shape `[samples, channels]`, sample-major). For every feature the decoder

1. checks the input against the model: all the channel labels the model was trained on must be present in the feature (the
   channels are then reordered to the order of the model) and the shape must match;
2. transposes the window to `[1, channels, samples]`, as `braindecode` expects;
3. runs `predict_proba` and publishes the probabilities, with the class names of the model as `fields`.

## Parameters

| Parameter | Default | Meaning |
|---|---|---|
| `input_topic` | `/features` | the `NeuroFeature` topic |
| `output_topic` | `~/prediction` | where the `NeuroPrediction` is published |
| `decoder.type` | `sklearn` | the kind of model: `braindecode` (see the limitations below for `sklearn`) |
| `decoder.model_path` | (empty) | the model: for `braindecode`, the **folder** of the model |
| `decoder.name` | `decoder` | written in `NeuroPrediction.decoder` |

## Model format (`braindecode`)

A model is a folder with a `manifest.yaml` and the weights. This manifest is **not** the one of the C++ decoders (it has no `.r2nd`
file): it describes a `braindecode` network.

```text
eegnet_mi_bhbf/
  manifest.yaml     decoder.target (the class, for example braindecode.models.ShallowFBCSPNet), decoder.config (its
                    arguments), decoder.parameters_file, the input contract (name, type, shape, axes with the channel
                    labels) and the output classes; also the training provenance
  params.pt         the weights (a torch state dict)
```

The example model of the package is `extra/eegnet_mi_bhbf` (a ShallowFBCSPNet for two classes, both hands and both feet, on 16
channels, a 4-14 Hz band, 512 samples at 512 Hz). It goes with the recording `extra/test_mi.gdf`. The launchers
`eegnet_*` of [`ros2neuro_devel_test`](../devel-test.md) use both.

## Example

```bash
ros2 launch ros2neuro_decoder_py example_decoder.launch.xml
```

The chain is: acquisition (replaying `test_mi.gdf`) → filter chain (4-14 Hz band) → `buffer_node` (512 samples) → this decoder.
The arguments of the launch file select the model (`decoder_model_path`), the configuration, and whether the visualizer and
the recorder are started.

## Known limitations

- Only `decoder.type: braindecode` is wired up. The `sklearn` type exists in the code (`skops` models, probabilities from
  `predict_proba`) but, in the current code, the node cannot create it: its constructor does not accept the `model_path` that the
  node passes, and its `load()` and `predict()` signatures differ from the ones the node calls.
- The decoder checks the labels and the shape of the feature, so the channels and the window length of the buffer must match
  those of the model.
- The model is loaded when the node starts, which takes a while: the protocols of the launchers wait for it
  (`duration.begin`).

## Setup Instructions

It is highly recommended to use a Python virtual environment to manage dependencies when building and running this package alongside ROS 2.

### 1. Create and Activate a Virtual Environment

Navigate to the root of your `ros2neuro` workspace and create a virtual environment (if you haven't already):

```bash
cd ~/neurorobotics/ros2neuro_ws
python3 -m venv ros2neuro_venv
```

Activate the virtual environment:

```bash
source ros2neuro_venv/bin/activate
```

*(Note: You will need to activate this virtual environment every time you want to build or run this package in a new terminal).*

### 2. Install Python Dependencies

With the virtual environment activated, install the necessary Python dependencies for this package:

```bash
cd ~/neurorobotics/ros2neuro_ws/src/ros2neuro_decoder_py
pip install -r requirements.txt
```

### 3. Build the Package

Ensure your ROS 2 installation is sourced (e.g., `source /opt/ros/jazzy/setup.bash`), and your virtual environment is active. Then, build the package using `colcon` from the root of the workspace:

```bash
cd ~/neurorobotics/ros2neuro_ws
colcon build --packages-select ros2neuro_decoder_py
```

### 4. Running the Package (Example)

After a successful build, source the workspace installation map alongside the virtual environment to run the nodes:

```bash
cd ~/neurorobotics/ros2neuro_ws
source install/setup.bash
source ros2neuro_venv/bin/activate

ros2 launch ros2neuro_decoder_py example_decoder.launch.xml
```
