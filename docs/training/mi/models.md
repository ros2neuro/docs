# Models and outputs

## Machine-learning models

The features and the estimators are chosen in the **Model** tab.

| Features | What it is | The ROS 2 stage that computes it online |
|---|---|---|
| **PSD** | the power spectral density (ln) of every channel at the chosen frequencies | [Welch](../../packages/processing/spectral.md) |
| **CSP** | the CSP log-variance of a band | [Fbcsp](../../packages/processing/fbcsp.md) with one band |
| **FBCSP** | the CSP log-variance of a bank of bands | [Fbcsp](../../packages/processing/fbcsp.md) |

The features are the ones the ROS 2 plugins compute: the tests compare the Python computation with the reference data the C++ plugins are checked against.

**Feature selection.** A score is computed once, on the whole feature map: **Fisher**, **CVA** or **MIBIF**. On the left of the selection panel you see the map of the score with the chosen features boxed (click to add or remove one), on the right an empty image with the selection alone, and below the map of every run, to see whether the selection stays the same from run to run.

**Estimators.** LDA, QDA, logistic regression, SVM, random forest, **Gaussian**, or **Auto**, which tries all of them in cross validation and keeps the best. The Gaussian one, with its default parameters, reproduces the Matlab SMR Gaussian classifier: one prototype per class, diagonal covariance, 20 epochs, and the epoch with the highest channel capacity is kept.

## Deep-learning models

The deep models are [braindecode](https://braindecode.org) networks trained with PyTorch (for example `ShallowFBCSPNet`, as in the [deep-learning pipeline tutorial](../../tutorials/dl-pipeline/index.md)). The network reads a **window of the signal**, so in ROS 2 it follows the [Buffer](../../packages/processing/buffer.md) plugin, not a Welch.

## What the output folder contains

The folder is the **model folder** of the decoder: its `manifest.yaml` is the entry point (`decoder.manifest`).

| Model | Files | Decoder that loads it |
|---|---|---|
| PSD features with LDA, QDA or Gaussian | `.r2nd` + `manifest.yaml` (the scaler is absorbed in the weights), plus the same model for scikit-learn in `sklearn/` (not for the Gaussian) | [LDA](../../packages/decoder/lda.md), [QDA](../../packages/decoder/qda.md), [Gaussian](../../packages/decoder/gaussian.md) |
| any other machine-learning model | `model.skops` + `manifest.yaml` | [scikit-learn decoder](../../packages/decoder/sklearn.md) |
| deep learning | the parameters (`params.pt`) + `manifest.yaml` (the network and its configuration, the channels it reads by label, the classes) | [Braindecode decoder](../../packages/decoder/braindecode.md) |

Next to the model, the trainer writes the yaml of the nodes that must run **before** the decoder, so that the model sees what it was trained on:

* `filter_chain.yaml`: the common filter chain of the [filter chain node](../../packages/filters/index.md);
* `processing.yaml`: the section of the [processing node](../../packages/processing/index.md) (`processing.plugin`, `processing.params.*`, and `input_topics` for FBCSP);
* `band_chains.yaml`, for FBCSP only: one filter chain per band (a `filter_chain_node` named `band_<lo>_<hi>`: high-pass at `lo`, low-pass at `hi`), because the Fbcsp plugin does not filter: it reads one already filtered stream per band, on topics that end with `band_<lo>_<hi>` in the order of the bands.

The `output.fields` of the manifest are the **class codes** (`"773"`), and the names go in `output.labels`. If the codes differ from the `classes` of your [protocol](../../concepts/shared-parameters.md), map them with `input_fields` of the [control](../../packages/control/feedback.md).

## Check a model offline

A trained model can be opened without ROS 2, to see what the node would do with a recording: [`r2n_*_read`](../../reproducibility/python.md#decoders) for the `.r2nd` files, [`r2n_sklearn_load`](../../reproducibility/python.md#r2n_sklearn_load) for scikit-learn, [`r2n_braindecode_load`](../../reproducibility/python.md#r2n_braindecode_load) for a deep network. See [Reproducibility](../../reproducibility/index.md).
