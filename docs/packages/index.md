# Packages

Every package of the workspace, grouped by the role it plays. A family that selects an implementation at runtime has the same three kinds of page:

* the **overview** of the family (what it does and its plugins), which is the first entry of its menu;
* the **base class** page: the package that holds the generic node and the parent class (the plugin interface), where those are explained;
* **one page per plugin**: a package that extends the parent class with one implementation.

For example *Acquisition* explains what the acquisition stage does and lists its plugins; *Base class* explains the node and `NeuroDevice`; *dummy*, *xdf*, *lsl*, ... are the devices. The tests and the replication of every package are not here: they are in [Reproducibility](../reproducibility/packages/index.md).

## What is in this menu

## Foundations

| Package | Role |
|---|---|
| [`ros2neuro_msgs`, `ros2neuro_data`](msgs-data.md) | messages and in-memory data types |

## Signal chain

| Base package | Plugins |
|---|---|
| [Acquisition](acquisition/index.md) · [base class](acquisition/base.md) | [dummy](acquisition/dummy.md), [xdf](acquisition/xdf.md), [lsl](acquisition/lsl.md), [eegdev](acquisition/eegdev.md), [antneuro](acquisition/antneuro.md), [gusbamp](acquisition/gusbamp.md) |
| [Filters](filters/index.md) · [base class](filters/base.md) | [dc](filters/dc.md), [butterworth](filters/butterworth.md), [car](filters/car.md), [laplacian](filters/laplacian.md), [hann](filters/hann.md), [hamming](filters/hamming.md), [blackman](filters/blackman.md), [flattop](filters/flattop.md) |
| [Processing](processing/index.md) · [base class](processing/base.md) | [spectral](processing/spectral.md) (FFT, Welch, spectrogram) for the classic decoders, [buffer](processing/buffer.md) for the deep-learning ones, [fbcsp](processing/fbcsp.md) for the FBCSP models: the decoder decides |
| [Decoder](decoder/index.md) · [base class](decoder/base.md) | [lda](decoder/lda.md), [qda](decoder/qda.md), [svm](decoder/svm.md), [gaussian](decoder/gaussian.md), [sklearn](decoder/sklearn.md), [braindecode](decoder/braindecode.md) (**Plugins**); [converters](decoder/converters.md) (**Converters**: Matlab SMR `.mat` to `.r2nd`) |
| [Integrator](integrator/index.md) · [base class](integrator/base.md) | [exponential](integrator/exponential.md), [buffer](integrator/buffer.md) |

## Protocol and feedback

| Base package | Plugins |
|---|---|
| [Control](control/index.md) · [base class](control/base.md) | [feedback](control/feedback.md) (`Feedback`: calibration with autopilot, evaluation, free control) |
| [Manager](manager/index.md) · [base class](manager/base.md) | [synchronous](manager/synchronous.md) (`Synchronous`: runs the trials), [asynchronous](manager/asynchronous.md) (`Asynchronous`: writes nothing) |
| [Feedback](feedback/index.md) · [base class](feedback/base.md) | [wheel](feedback/wheel.md), [bar](feedback/bar.md). Both need the [neurodraw](feedback/neurodraw.md) library |

## Tools

| Package | Role |
|---|---|
| [Recorder](recorder/index.md) · [base class](recorder/base.md) + [xdf](recorder/xdf.md) | write signal and events to GDF / BDF |
| [Visualizer](visualizer.md) | Qt scope of the signals |
| [`ros2neuro_devel_test`](../reproducibility/packages/index.md) | hardware-free tests of every stage and of the whole pipeline: see [Reproducibility](../reproducibility/index.md) |

## Choosing the plugins of a pipeline

| To... | Select |
|---|---|
| run without hardware | acquisition [xdf](acquisition/xdf.md) or [dummy](acquisition/dummy.md) |
| record a session | recorder [xdf](recorder/xdf.md) |
| classify motor imagery from a PSD | [spectral](processing/spectral.md) Welch, a [gaussian](decoder/gaussian.md) or [qda](decoder/qda.md) model, an [exponential](integrator/exponential.md) integrator |
| classify with a deep-learning model | [buffer](processing/buffer.md) instead of Welch, then the [braindecode decoder](decoder/braindecode.md) |
| run a calibration or an evaluation | manager [synchronous](manager/synchronous.md) + [control_feedback](control/feedback.md) (`protocol: calibration` or `evaluation`) |
| run a free-control session | [control_feedback](control/feedback.md) (`protocol: control`) |
| show two classes | feedback [wheel](feedback/wheel.md) |
| show two or more classes | feedback [bar](feedback/bar.md) |
