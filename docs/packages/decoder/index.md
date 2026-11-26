# Decoder

!!! info ""
    Package: [`ros2neuro_decoder`](https://github.com/ros2neuro/ros2neuro_decoder)

The decoder package turns a `NeuroFeature` (for example a PSD) into a `NeuroPrediction`. It provides the
`Decoder` plugin interface and `decoder_node`, which loads **one** decoder plugin.

!!! important "Select one plugin"
    The decoder is chosen by its type, for example [`ros2neuro::decoder::Gaussian`](gaussian.md). When you pass a model with
    `decoder.manifest`, the node reads the type from the `manifest.yaml`; otherwise set `decoder.type`.

## What is in this menu

| Page | What you find |
|---|---|
| [Base class: `ros2neuro_decoder`](base.md) | the node, its topics and parameters, the plugin interface and how to write a new plugin |
| [Available plugins](#available-plugins) | the plugins of the family, each with its own page |
| [Converters](converters.md) | Turn a decoder made elsewhere (a Matlab SMR `.mat`) into the `.r2nd` + `manifest.yaml` format |

## Available plugins

| Plugin | pluginlib class / type | Model |
|---|---|---|
| [LDA](lda.md) | [`ros2neuro::decoder::LDA`](lda.md) | linear discriminant analysis |
| [QDA](qda.md) | [`ros2neuro::decoder::QDA`](qda.md) | quadratic discriminant analysis |
| [SVM](svm.md) | [`ros2neuro::decoder::SVM`](svm.md) | support vector machine |
| [Gaussian](gaussian.md) | [`ros2neuro::decoder::Gaussian`](gaussian.md) | Gaussian classifier (ported from Matlab SMR) |
| [scikit-learn](sklearn.md) | [`ros2neuro::decoder::Sklearn`](sklearn.md) | any scikit-learn estimator or Pipeline with `predict_proba` (skops file), run in Python inside the plugin |
| [Braindecode](braindecode.md) | [`ros2neuro::decoder::Braindecode`](braindecode.md) | deep-learning model of braindecode (PyTorch), run in Python inside the plugin |

The [converters](converters.md) turn a Matlab SMR `.mat` decoder into the `.r2nd` + `manifest.yaml` format.

!!! note "Models made in Python"
    scikit-learn and braindecode (PyTorch) models run as plugins of this node, [`ros2neuro_decoder_sklearn`](sklearn.md) and
    [`ros2neuro_decoder_braindecode`](braindecode.md): the model runs in a Python interpreter inside the plugin, and they are configured
    like every decoder (`decoder.manifest`).
