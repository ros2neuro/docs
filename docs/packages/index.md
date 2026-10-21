# Packages

Every package of the workspace, grouped by the role it plays. Packages that select an implementation at runtime
are split into a **base package** (the generic node and the plugin interface) and one **plugin package** per
implementation. The base page explains what the node does and tells you to select a plugin; each plugin has its
own page.

## Foundations

| Package | Role |
|---|---|
| [`ros2neuro_msgs`, `ros2neuro_data`](msgs-data.md) | messages and in-memory data types |

## Signal chain

| Base package | Plugins |
|---|---|
| [Acquisition](acquisition/index.md) | [dummy](acquisition/dummy.md), [xdf](acquisition/xdf.md), [lsl](acquisition/lsl.md), [eegdev](acquisition/eegdev.md), [antneuro](acquisition/antneuro.md), [gusbamp](acquisition/gusbamp.md) |
| [Filters](filters/index.md) | [dc](filters/dc.md), [butterworth](filters/butterworth.md), [car](filters/car.md), [laplacian](filters/laplacian.md), [hann](filters/hann.md), [hamming](filters/hamming.md), [blackman](filters/blackman.md), [flattop](filters/flattop.md) |
| Processing | [spectral](processing/spectral.md) (FFT, Welch, spectrogram), [buffer](processing/buffer.md) |
| [Decoder](decoder/index.md) | [lda](decoder/lda.md), [qda](decoder/qda.md), [svm](decoder/svm.md), [gaussian](decoder/gaussian.md), [python](decoder/python.md); [converters](decoder/converters.md) |
| [Integrator](integrator/index.md) | [exponential](integrator/exponential.md), [buffer](integrator/buffer.md) |

## Protocol and feedback

| Base package | Plugins |
|---|---|
| [Manager](manager/index.md) | [synchronous](manager/synchronous.md) (`Training`), [asynchronous](manager/asynchronous.md) (`Control`) |
| [Feedback](feedback/index.md) | [wheel](feedback/wheel.md), [bar](feedback/bar.md). Both need the [neurodraw](feedback/neurodraw.md) library |

## Tools

| Package | Role |
|---|---|
| [Recorder](recorder/index.md) + [xdf](recorder/xdf.md) | write signal and events to GDF / BDF |
| [Visualizer](visualizer.md) | Qt scope of the signals |
| [`ros2neuro_devel_test`](devel-test.md) | hardware-free launchers that run the whole pipeline |

## Choosing the plugins of a pipeline

| To... | Select |
|---|---|
| run without hardware | acquisition [xdf](acquisition/xdf.md) or [dummy](acquisition/dummy.md) |
| record a session | recorder [xdf](recorder/xdf.md) |
| classify motor imagery from a PSD | [spectral](processing/spectral.md) Welch, a [gaussian](decoder/gaussian.md) or [qda](decoder/qda.md) model, an [exponential](integrator/exponential.md) integrator |
| run a calibration or an evaluation | manager [synchronous](manager/synchronous.md) |
| run a free-control session | manager [asynchronous](manager/asynchronous.md) |
| show two classes | feedback [wheel](feedback/wheel.md) |
| show two or more classes | feedback [bar](feedback/bar.md) |
