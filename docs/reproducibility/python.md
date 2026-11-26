# Reproducibility in Python

[Download and use the functions](download.md) · [MATLAB version](matlab.md)

Everything the MATLAB page does, with **numpy and scipy**, plus what MATLAB cannot do: **load the models** the decoders use, whatever their kind, and run them offline. The functions are the twins of the `r2n_*` ones of MATLAB (same names, same arithmetic) and they also open:

* the **`.r2nd`** models of the decoders trained in Matlab or with `mi_training` (LDA, QDA, SVM, Gaussian);
* any **scikit-learn** model of [`decoder_sklearn`](../packages/decoder/sklearn.md) (skops file + manifest): LDA, logistic regression, random forest, ...;
* any **deep-learning** model of [`decoder_braindecode`](../packages/decoder/braindecode.md) (braindecode / PyTorch): ShallowNet, EEGNet, ...

So the whole chain of an experiment, including a deep network, can be replayed on a recording and compared with what the nodes published.

!!! success "Download"
    - **[ros2neuro_python.zip](ros2neuro_python.zip)**: the `r2n_*.py` functions, one file each.
    - **[check_pipeline_dl.py](files/python/check_pipeline_dl.py)**: the whole deep-learning pipeline replayed and compared with a run (also in `pipeline/dl/` of [`ros2neuro_devel_test`](https://github.com/ros2neuro/ros2neuro_devel_test/tree/main/pipeline/dl)).

    The functions are in the `python/` folder of [`ros2neuro_devel_test`](https://github.com/ros2neuro/ros2neuro_devel_test/tree/main/python), next to `matlab/`.

```text
ros2neuro_devel_test/
├── matlab/    r2n_*.m
├── python/    r2n_*.py: the same functions, plus the loaders of the r2nd, scikit-learn and braindecode models
└── pipeline/dl/check_pipeline_dl.py    the deep-learning pipeline, replayed and compared with a run
```

You need `numpy` and `scipy`; the scikit-learn functions also `scikit-learn`, `skops` and `pyyaml`; the deep-learning ones `torch`, `braindecode` and `pyyaml` (the Docker image and the `ros2neuro` container have them all).

## The functions

| Function | What it reproduces | Takes → gives | Plugin page |
|---|---|---|---|
| **Filters** | | | |
| [`r2n_car`](#r2n_car) | CAR: common average reference | `[samples x channels]` → same shape | [filters_car](../packages/filters/car.md) |
| [`r2n_dc`](#r2n_dc) | DC: remove the mean of each frame | `[samples x channels]`, `block` (32) → `[floor(samples/block)*block x channels]` | [filters_dc](../packages/filters/dc.md) |
| [`r2n_laplacian`](#r2n_laplacian) | Laplacian: spatial filter | `[samples x channels]`, `layout` → same shape | [filters_laplacian](../packages/filters/laplacian.md) |
| [`r2n_window`](#r2n_window) | Hann, Hamming, Blackman, Flattop windows | `[samples x channels]`, `name`, `block` (32) → `[.. x channels]`, window | [filters_hann, filters_hamming, filters_blackman, filters_flattop](../packages/filters/hann.md) |
| [`r2n_butterworth`](#r2n_butterworth) | Butterworth: low-pass and high-pass | `[samples, channels]`, `kind`, `order`, `fc`, `fs` → `y`, `b`, `a` | [filters_butterworth](../packages/filters/butterworth.md) |
| **Processing** | | | |
| [`r2n_welch`](#r2n_welch) | Welch: ln of the power spectral density | `[samples, channels]` buffer, `fs`, `length`, `overlap`, `window`, `freqs` → `[frequencies, channels]` | [processing_spectral (`Welch`)](../packages/processing/spectral.md) |
| [`r2n_fft`](#r2n_fft) | FFT: amplitude spectrum | `[window_length x channels]`, `fs`, window, `apply_log` → `[bins x channels]`, frequencies | [processing_spectral (`FFT`)](../packages/processing/spectral.md) |
| [`r2n_spectrogram`](#r2n_spectrogram) | Spectrogram | `[analysis_length x channels]`, `fs`, `window_length`, `overlap`, window, `apply_log` → `[segments x bins x channels]`, frequencies, times | [processing_spectral (`Spectrogram`)](../packages/processing/spectral.md) |
| [`r2n_spectral_window`](#r2n_spectral_window) | Window of FFT and spectrogram | name, `n` → window of `n` values | [processing_spectral](../packages/processing/spectral.md) |
| [`r2n_fbcsp`](#r2n_fbcsp) | FBCSP features | one `[buffer x channels]` per band, `W` `[bands x components x channels]` → one feature vector | [processing_fbcsp](../packages/processing/fbcsp.md) |
| [`r2n_fbcsp_weights`](#r2n_fbcsp_weights) | CSP filters as an array | flat `filters`, bands, components, channels → `[bands x components x channels]` | [processing_fbcsp](../packages/processing/fbcsp.md) |
| **Decoders** | | | |
| [`r2n_softmax`](#r2n_softmax) | Softmax of the scores | scores `[K]` → probabilities `[K]` | [decoder_lda, decoder_qda, decoder_svm](../packages/decoder/index.md) |
| [`r2n_linear_read`](#r2n_linear_read) | Read the `.r2nd` of LDA and SVM | `.r2nd` file → model | [decoder_lda, decoder_svm](../packages/decoder/lda.md) |
| [`r2n_linear_predict`](#r2n_linear_predict) | LDA and linear SVM | model, PSD feature → probabilities, scores | [decoder_lda, decoder_svm](../packages/decoder/lda.md) |
| [`r2n_qda_read`](#r2n_qda_read) | Read the `.r2nd` of QDA | `.r2nd` file → model | [decoder_qda](../packages/decoder/qda.md) |
| [`r2n_qda_predict`](#r2n_qda_predict) | QDA | model, PSD feature → probabilities, scores | [decoder_qda](../packages/decoder/qda.md) |
| [`r2n_gaussian_read`](#r2n_gaussian_read) | Read the `.r2nd` of the Gaussian decoder | `.r2nd` file → model | [decoder_gaussian](../packages/decoder/gaussian.md) |
| [`r2n_gaussian_predict`](#r2n_gaussian_predict) | Gaussian decoder | model, PSD feature → probabilities | [decoder_gaussian](../packages/decoder/gaussian.md) |
| **ML and deep-learning models** | | | |
| [`r2n_sklearn_load`](#r2n_sklearn_load) | Load a scikit-learn model | model folder (`manifest.yaml` + `model.skops`) → model | [decoder_sklearn](../packages/decoder/sklearn.md) |
| [`r2n_sklearn_predict`](#r2n_sklearn_predict) | Predict with a scikit-learn model | model, 2-D feature → probabilities | [decoder_sklearn](../packages/decoder/sklearn.md) |
| [`r2n_braindecode_load`](#r2n_braindecode_load) | Load a braindecode / PyTorch model | model folder (`manifest.yaml` + `params.pt`) → network | [decoder_braindecode](../packages/decoder/braindecode.md) |
| [`r2n_braindecode_predict`](#r2n_braindecode_predict) | Predict with a braindecode / PyTorch model | model, windows `[n x samples x channels]` → probabilities `[n x K]` | [decoder_braindecode](../packages/decoder/braindecode.md) |
| **Integrator and control** | | | |
| [`r2n_integrator_exponential`](#r2n_integrator_exponential) | Exponential integrator | `[frames, K]` probabilities, `alpha`, reset frames (0-based) → `[frames, K]`, reset times | [integrator_exponential](../packages/integrator/exponential.md) |
| [`r2n_integrator_buffer`](#r2n_integrator_buffer) | Buffer integrator | `[frames, K]` probabilities, `buffer_size`, `increment`, reset frames (0-based), `init_val` → `[frames, K]` | [integrator_buffer](../packages/integrator/buffer.md) |
| [`r2n_threshold_winner`](#r2n_threshold_winner) | Which class touched its threshold | thresholds, values → index of the winning class (0-based, -1 = none) | [control_feedback](../packages/control/feedback.md) |
| **Helpers** | | | |
| [`r2n_r2nd`](#r2n_r2nd) | Reader of the `.r2nd` files | file → sequential reader | [decoder_lda, decoder_qda, decoder_gaussian](../packages/decoder/index.md) |

Click a name to jump to its dropdown; it opens by itself. Every dropdown starts with the explanation and ends with the code, which is the file of the zip.

### Filters

<a id="r2n_car"></a>

??? example "r2n_car.py: CAR: common average reference"
    **Reproduces:** [filters_car](../packages/filters/car.md)
    **Takes → gives:** `[samples x channels]` → same shape

    Subtracts from every sample the mean of all the channels at that instant, so what the channels have in common (a drift, the reference) disappears. The plugin does it row by row on each `NeuroFrame`; the function does it on the whole signal at once, because the operation has no memory.

    **How close:** The plugin adds the channels in float32, one after the other; numpy adds them in another order. The result can differ by 1-2 ULP of the input.

    ```python
    --8<-- "files/python/r2n/r2n_car.py"
    ```

<a id="r2n_dc"></a>

??? example "r2n_dc.py: DC: remove the mean of each frame"
    **Reproduces:** [filters_dc](../packages/filters/dc.md)
    **Takes → gives:** `[samples x channels]`, `block` (32) → `[floor(samples/block)*block x channels]`

    Cuts the signal in blocks of `block` samples (one `NeuroFrame`), and subtracts from every channel the mean of **its** block. It is a high-pass with no memory: the mean is recomputed on every frame. The samples at the end that do not fill a block are dropped, as the node never gets them.

    **How close:** The plugin sums the block in float32 with Eigen; numpy sums in another order: up to 4 ULP of the input.

    ```python
    --8<-- "files/python/r2n/r2n_dc.py"
    ```

<a id="r2n_laplacian"></a>

??? example "r2n_laplacian.py: Laplacian: spatial filter"
    **Reproduces:** [filters_laplacian](../packages/filters/laplacian.md)
    **Takes → gives:** `[samples x channels]`, `layout` → same shape

    Builds the matrix of the filter from the layout of the electrodes (a grid of channel numbers, `0` where there is no electrode): column *c* has +1 on channel *c* and −1/n on each of its *n* neighbours (left, right, up, down). The signal is then multiplied by that matrix: every channel minus the mean of its neighbours. `layout` is the matrix or the text of the yaml parameter `"1 2 3; 4 5 6; 7 8 9"`, so you can paste the parameter of your launch file.

    **How close:** One matrix product in float32; the order of the additions is not the one of Eigen: a few ULP of the input at most.

    ```python
    --8<-- "files/python/r2n/r2n_laplacian.py"
    ```

<a id="r2n_window"></a>

??? example "r2n_window.py: Hann, Hamming, Blackman, Flattop windows"
    **Reproduces:** [filters_hann, filters_hamming, filters_blackman, filters_flattop](../packages/filters/hann.md)
    **Takes → gives:** `[samples x channels]`, `name`, `block` (32) → `[.. x channels]`, window

    The four window filters are the same operation with a different window: every block of `block` samples (one `NeuroFrame`) is multiplied, sample by sample, by the same window. The windows are the **symmetric** ones (denominator N−1, the one the plugins use) and are rounded to float32 like the plugins. Returns the signal and the window.

    **How close:** A product of two float32 numbers is exact in the arithmetic of both: the result is identical to the node (difference 0).

    ```python
    --8<-- "files/python/r2n/r2n_window.py"
    ```

<a id="r2n_butterworth"></a>

??? example "r2n_butterworth.py: Butterworth: low-pass and high-pass"
    **Reproduces:** [filters_butterworth](../packages/filters/butterworth.md)
    **Takes → gives:** `[samples, channels]`, `kind`, `order`, `fc`, `fs` → `y`, `b`, `a`

    Designs the Butterworth filter of the given order and cut-off (normalized to the Nyquist frequency) and runs it **causally** (forward only, as it must be online) over the whole signal, keeping the state from one sample to the next. The plugin does the same frame after frame with the state kept between frames, which gives the same numbers as one pass over the whole signal. The computation is in double, the result is rounded to float32 as the plugin publishes it. A band-pass is two of them, one after the other (high-pass at the lower edge, low-pass at the upper).

    **How close:** Same design, same recursion: the difference is 0 for the low-pass and 0.25 ULP for the 1 Hz high-pass.

    ```python
    --8<-- "files/python/r2n/r2n_butterworth.py"
    ```

### Processing

<a id="r2n_welch"></a>

??? example "r2n_welch.py: Welch: ln of the power spectral density"
    **Reproduces:** [processing_spectral (`Welch`)](../packages/processing/spectral.md)
    **Takes → gives:** `[samples, channels]` buffer, `fs`, `length`, `overlap`, `window`, `freqs` → `[frequencies, channels]`

    Splits the buffer in segments of `length` samples every `length - overlap`, multiplies each by the window, takes the power spectrum of each and averages them: that is Welch's PSD (one-sided, in power/Hz). The plugin publishes `ln(max(PSD, 1e-12))` at the bins of the frequencies you ask for (`freqs`, in Hz, multiples of `fs/length`). That is what a PSD decoder (QDA, LDA, Gaussian) reads: all the channels, all the frequencies, channel by channel.

    **How close:** The window must be the symmetric one (`r2n_spectral_window`), with no detrending, `nfft = length`: with these choices the difference is 0. In Python the Welch parameters are arguments, not a struct. `scipy.signal.welch` detrends by default and MATLAB's `pwelch` does not: the function passes `detrend=False`.

    ```python
    --8<-- "files/python/r2n/r2n_welch.py"
    ```

<a id="r2n_fft"></a>

??? example "r2n_fft.py: FFT: amplitude spectrum"
    **Reproduces:** [processing_spectral (`FFT`)](../packages/processing/spectral.md)
    **Takes → gives:** `[window_length x channels]`, `fs`, window, `apply_log` → `[bins x channels]`, frequencies

    Multiplies the buffer by the window, takes the FFT and keeps the first N/2+1 bins (the one-sided spectrum). The amplitude is `|FFT| / N`, doubled on every bin but the first and the last (the energy of the negative frequencies). With `apply_log` it is expressed as `20·log10`. Computed in double like the node and rounded to float32 at the end.

    **How close:** The node and the function compute the same double and round once: the float32 numbers are the same (< 1 ULP).

    ```python
    --8<-- "files/python/r2n/r2n_fft.py"
    ```

<a id="r2n_spectrogram"></a>

??? example "r2n_spectrogram.py: Spectrogram"
    **Reproduces:** [processing_spectral (`Spectrogram`)](../packages/processing/spectral.md)
    **Takes → gives:** `[analysis_length x channels]`, `fs`, `window_length`, `overlap`, window, `apply_log` → `[segments x bins x channels]`, frequencies, times

    Cuts the buffer in overlapping segments, windows each one and computes its power spectral density (`|FFT|² / (fs·Σw²)`, doubled on the inner bins). The result is a time-frequency map; in dB when `apply_log` (`10·log10`). Also returns the frequency of every bin and the time of the centre of every segment. The feature published by the node has the same shape with the channel varying fastest.

    **How close:** Double precision like the node, rounded to float32 at the end: < 1 ULP.

    ```python
    --8<-- "files/python/r2n/r2n_spectrogram.py"
    ```

<a id="r2n_spectral_window"></a>

??? example "r2n_spectral_window.py: Window of FFT and spectrogram"
    **Reproduces:** [processing_spectral](../packages/processing/spectral.md)
    **Takes → gives:** name, `n` → window of `n` values

    The window used by `r2n_welch`, `r2n_fft` and `r2n_spectrogram`: rectangular, Hann, Hamming, Blackman or flat-top, **symmetric** (denominator n−1) and in double (not rounded to float32: that is `r2n_window`, for the filters).

    ```python
    --8<-- "files/python/r2n/r2n_spectral_window.py"
    ```

<a id="r2n_fbcsp"></a>

??? example "r2n_fbcsp.py: FBCSP features"
    **Reproduces:** [processing_fbcsp](../packages/processing/fbcsp.md)
    **Takes → gives:** one `[buffer x channels]` per band, `W` `[bands x components x channels]` → one feature vector

    The input is the signal of every band **already band-passed** (the node reads one filtered topic per band; here, `r2n_butterworth` high-pass then low-pass). For each band the window is projected on the CSP filters (`z = x · W'`), the variance of every component is taken and normalized by the sum of the variances of that band; the feature is its logarithm. The vector is band after band (`index = band · components + component`). `r2n_fbcsp_weights` rearranges the flat `filters` parameter of the plugin in the array this function takes.

    **How close:** Double arithmetic, float32 at the end: 1e-7 against the node.

    ```python
    --8<-- "files/python/r2n/r2n_fbcsp.py"
    ```

<a id="r2n_fbcsp_weights"></a>

??? example "r2n_fbcsp_weights.py: CSP filters as an array"
    **Reproduces:** [processing_fbcsp](../packages/processing/fbcsp.md)
    **Takes → gives:** flat `filters`, bands, components, channels → `[bands x components x channels]`

    The `filters` parameter of the Fbcsp plugin is a flat list ordered `[band][component][channel]`, channel varying fastest. This reorders it in the 3-D array `r2n_fbcsp` takes.

    ```python
    --8<-- "files/python/r2n/r2n_fbcsp_weights.py"
    ```

### Decoders

<a id="r2n_softmax"></a>

??? example "r2n_softmax.py: Softmax of the scores"
    **Reproduces:** [decoder_lda, decoder_qda, decoder_svm](../packages/decoder/index.md)
    **Takes → gives:** scores `[K]` → probabilities `[K]`

    How LDA, QDA and SVM turn their scores into probabilities: `exp(score − max)` (the maximum is subtracted so that nothing overflows) divided by the sum, added **in order** in float32 like the C++. If the sum is not above the float32 epsilon the values are returned as they are, as the C++ does.

    ```python
    --8<-- "files/python/r2n/r2n_softmax.py"
    ```

<a id="r2n_linear_read"></a>

??? example "r2n_linear_read.py: Read the `.r2nd` of LDA and SVM"
    **Reproduces:** [decoder_lda, decoder_svm](../packages/decoder/lda.md)
    **Takes → gives:** `.r2nd` file → model

    Reads the binary model that the decoder node loads (header `R2NDEC1`, little endian, versions 1 and 2) skipping the fields the prediction does not use. You get the selected features (the pairs channel / frequency, 0-based), the weights (one row per class), the bias, the classes and the frequencies. A linear SVM has the same file layout as the LDA.

    ```python
    --8<-- "files/python/r2n/r2n_linear_read.py"
    ```

<a id="r2n_linear_predict"></a>

??? example "r2n_linear_predict.py: LDA and linear SVM"
    **Reproduces:** [decoder_lda, decoder_svm](../packages/decoder/lda.md)
    **Takes → gives:** model, PSD feature → probabilities, scores

    Takes from the feature (all the channels × all the frequencies, channel by channel) the values the model selected, computes for every class `score = bias + Σ w·x` adding in the order of the selection, and turns the scores into probabilities with `r2n_softmax`. A model whose output is `TYPE_SCORES` publishes the scores instead: both are returned.

    **How close:** Same float32 operations in the same order as the C++: 6e-8 against the node.

    ```python
    --8<-- "files/python/r2n/r2n_linear_predict.py"
    ```

<a id="r2n_qda_read"></a>

??? example "r2n_qda_read.py: Read the `.r2nd` of QDA"
    **Reproduces:** [decoder_qda](../packages/decoder/qda.md)
    **Takes → gives:** `.r2nd` file → model

    The same reader as the LDA one, for the QDA layout (version 2): besides the linear weights it reads the quadratic matrix of every class (stored row by row).

    ```python
    --8<-- "files/python/r2n/r2n_qda_read.py"
    ```

<a id="r2n_qda_predict"></a>

??? example "r2n_qda_predict.py: QDA"
    **Reproduces:** [decoder_qda](../packages/decoder/qda.md)
    **Takes → gives:** model, PSD feature → probabilities, scores

    For every class: `score = bias + Σ l·x + Σ_row Σ_col x_row · Q(row, col) · x_col`, the three sums added in this order in float32 like `QDA.cpp`; then `r2n_softmax`. The selected features are taken from the PSD exactly as for the LDA.

    **How close:** Same operations in the same order: 1.5e-8 against the node.

    ```python
    --8<-- "files/python/r2n/r2n_qda_predict.py"
    ```

<a id="r2n_gaussian_read"></a>

??? example "r2n_gaussian_read.py: Read the `.r2nd` of the Gaussian decoder"
    **Reproduces:** [decoder_gaussian](../packages/decoder/gaussian.md)
    **Takes → gives:** `.r2nd` file → model

    Reads the Gaussian model (version 2) that comes from a Matlab SMR classifier: priors, selected features, and for every class and prototype the centers and the covariances (diagonal).

    ```python
    --8<-- "files/python/r2n/r2n_gaussian_read.py"
    ```

<a id="r2n_gaussian_predict"></a>

??? example "r2n_gaussian_predict.py: Gaussian decoder"
    **Reproduces:** [decoder_gaussian](../packages/decoder/gaussian.md)
    **Takes → gives:** model, PSD feature → probabilities

    For every class, every prototype *q* gives an activation `Σ_j −0.5·d_j²/v_j − 0.5·ln v_j` (`d` = feature − center, `v` = variance); the class score is the log-sum-exp of its prototypes plus `ln(prior)`. The probabilities are `exp(score − max)` divided by the sum. All in float32, in the order of `Gaussian.cpp`.

    **How close:** 1.5e-7 against the node (one ULP of a probability).

    ```python
    --8<-- "files/python/r2n/r2n_gaussian_predict.py"
    ```

### ML and deep-learning models

<a id="r2n_sklearn_load"></a>

??? example "r2n_sklearn_load.py: Load a scikit-learn model"
    **Reproduces:** [decoder_sklearn](../packages/decoder/sklearn.md)
    **Takes → gives:** model folder (`manifest.yaml` + `model.skops`) → model

    Opens a model of `ros2neuro_decoder_sklearn` the way the plugin does, without ROS: reads the manifest, loads the skops file (trusting the types it contains: the model is the one you chose), finds the classes in the order of the output fields, and turns `features.selection` (channels and frequencies, or bands and components) into index pairs. Any scikit-learn estimator with `predict_proba` works: LDA, logistic regression, random forest, ...

    ```python
    --8<-- "files/python/r2n/r2n_sklearn_load.py"
    ```

<a id="r2n_sklearn_predict"></a>

??? example "r2n_sklearn_predict.py: Predict with a scikit-learn model"
    **Reproduces:** [decoder_sklearn](../packages/decoder/sklearn.md)
    **Takes → gives:** model, 2-D feature → probabilities

    Takes the feature as the node publishes it (`[channels x frequencies]` for a PSD, `[bands x components]` for FBCSP), reorders it by label and value if you pass them, picks the selected pairs (or the whole feature) and calls `predict_proba`. The result is in the order of the output fields, as the node publishes it. It agrees with the plugin's own Python class to 2e-26.

    ```python
    --8<-- "files/python/r2n/r2n_sklearn_predict.py"
    ```

<a id="r2n_braindecode_load"></a>

??? example "r2n_braindecode_load.py: Load a braindecode / PyTorch model"
    **Reproduces:** [decoder_braindecode](../packages/decoder/braindecode.md)
    **Takes → gives:** model folder (`manifest.yaml` + `params.pt`) → network

    Builds the network of `decoder.target` (for example `braindecode.models.ShallowFBCSPNet`) from `decoder.config`, loads the weights of the parameters file and puts it in eval mode on the CPU. Returns the network, the channels it reads (in its order) and the output classes. Any model trained with `mi_training` loads like this.

    ```python
    --8<-- "files/python/r2n/r2n_braindecode_load.py"
    ```

<a id="r2n_braindecode_predict"></a>

??? example "r2n_braindecode_predict.py: Predict with a braindecode / PyTorch model"
    **Reproduces:** [decoder_braindecode](../packages/decoder/braindecode.md)
    **Takes → gives:** model, windows `[n x samples x channels]` → probabilities `[n x K]`

    Picks the channels of the network by label, gives it the windows as `[n, channels, samples]` float32 and returns probabilities: if the network outputs log-probabilities they are exponentiated, otherwise a softmax is applied. The same code as `check_pipeline_dl.py`, which compares it with the network inside the node.

    ```python
    --8<-- "files/python/r2n/r2n_braindecode_predict.py"
    ```

### Integrator and control

<a id="r2n_integrator_exponential"></a>

??? example "r2n_integrator_exponential.py: Exponential integrator"
    **Reproduces:** [integrator_exponential](../packages/integrator/exponential.md)
    **Takes → gives:** `[frames, K]` probabilities, `alpha`, reset frames (0-based) → `[frames, K]`, reset times

    The recursion `state = alpha·state + (1−alpha)·prediction`, in float32. The first prediction of the run becomes the state. At the frames of `reset_frames` the state goes back to 1/K **before** that frame is integrated (the node integrates the frame that contains the CFeedback event and resets after it: the caller passes the frame after). It also returns the time of every reset.

    **How close:** Same recursion: difference 0. Python is 0-based: `reset_frames` and `first` count from 0 (MATLAB: from 1).

    ```python
    --8<-- "files/python/r2n/r2n_integrator_exponential.py"
    ```

<a id="r2n_integrator_buffer"></a>

??? example "r2n_integrator_buffer.py: Buffer integrator"
    **Reproduces:** [integrator_buffer](../packages/integrator/buffer.md)
    **Takes → gives:** `[frames, K]` probabilities, `buffer_size`, `increment`, reset frames (0-based), `init_val` → `[frames, K]`

    A bar that moves: at every frame the class with the highest probability (the first on a tie) goes up by one step and the others go down by the same total, in equal shares (a class that reaches 0 stops and the rest goes to the others). The step is `1/buffer_size` (hard, `increment = 0`) or the winning probability over `buffer_size` (soft, `increment = 1`). At a reset the buffer returns to `init_val` (default 1/K).

    **How close:** Same operations in float32: < 1 ULP. Python is 0-based: `reset_frames` count from 0 (MATLAB: from 1).

    ```python
    --8<-- "files/python/r2n/r2n_integrator_buffer.py"
    ```

<a id="r2n_threshold_winner"></a>

??? example "r2n_threshold_winner.py: Which class touched its threshold"
    **Reproduces:** [control_feedback](../packages/control/feedback.md)
    **Takes → gives:** thresholds, values → index of the winning class (0-based, -1 = none)

    The test `control_feedback` uses to decide a trial: a class is over its own threshold when `value + 1e-6 >= threshold` (in float32). When several are over, the highest wins. It is used to recompute Hit / Miss / Timeout from the integrated values.

    ```python
    --8<-- "files/python/r2n/r2n_threshold_winner.py"
    ```

### Helpers

<a id="r2n_r2nd"></a>

??? example "r2n_r2nd.py: Reader of the `.r2nd` files"
    **Reproduces:** [decoder_lda, decoder_qda, decoder_gaussian](../packages/decoder/index.md)
    **Takes → gives:** file → sequential reader

    A small class that reads the little-endian binary file (strings preceded by their length, float32 and uint32 arrays). The three `*_read` functions use it, so the format is written once. In MATLAB each reader does it with `fread`.

    ```python
    --8<-- "files/python/r2n/r2n_r2nd.py"
    ```


## How close to the MATLAB functions and to the node

Each Python function was compared with its MATLAB twin on the same input (random signals, and the models of `data/models/`): CAR, Laplacian and the 1 Hz high-pass differ by a few ULP of float32 (numpy, MATLAB and Eigen add in different orders), every other function by less than 1e-12; the decoders, the integrators and the winner test give the same numbers. `r2n_sklearn_predict` agrees with the plugin's own Python class to 2e-26. The functions that are not compared with MATLAB (the network) are compared with ROS 2 by the [deep-learning pipeline check](pipeline.md#the-deep-learning-pipeline-in-python).

Differences from MATLAB: arrays are **0-based** (the frames of a reset, the index of the winning class, `-1` = none), the model of a `*_read` is a dict, and the Welch parameters are arguments.

## Use a function in your own analysis

```python
import sys; sys.path.insert(0, 'ros2neuro_python')
import numpy as np
from r2n_butterworth import r2n_butterworth
from r2n_laplacian import r2n_laplacian
from r2n_welch import r2n_welch
from r2n_qda_read import r2n_qda_read
from r2n_qda_predict import r2n_qda_predict

x, _, _ = r2n_butterworth(eeg, 'high', 4, 1, 512)          # eeg: [samples, channels]
x = r2n_laplacian(x, '1 2 3 4; 5 6 7 8; 9 10 11 12; 13 14 15 16')
psd = r2n_welch(x[-512:], 512, 256, 128, 'hamming', np.arange(4, 49, 2))   # [frequencies, channels]
m = r2n_qda_read('qda_test_gdf.r2nd')                       # the model the decoder node loads
p, scores = r2n_qda_predict(m, psd.T.ravel())               # channel-major, as the feature of the node
```

The same with a scikit-learn or a deep-learning model: they read the manifest folder, the same one you give to the decoder node.

```python
from r2n_sklearn_load import r2n_sklearn_load
from r2n_sklearn_predict import r2n_sklearn_predict
from r2n_braindecode_load import r2n_braindecode_load
from r2n_braindecode_predict import r2n_braindecode_predict

lda = r2n_sklearn_load('lda_psd/sklearn')                   # manifest.yaml + model.skops
p = r2n_sklearn_predict(lda, psd.T)                         # psd.T: [channels, frequencies] -> probabilities of lda['classes']

net = r2n_braindecode_load('eegnet_mi_bhbf')                # manifest.yaml + params.pt
p = r2n_braindecode_predict(net, windows)                   # windows: [n, 512, channels] -> [n, K]
```
