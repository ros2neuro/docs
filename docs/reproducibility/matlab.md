# Reproducibility in MATLAB

[Download and use the functions](download.md) · [Python version](python.md)

Every stage of the chain computed in C++, from the filters to the decoders and the integrators, has a **MATLAB twin**: a short function that does the same
computation, in the same float32 arithmetic, and that is **compared with what the real ROS 2 node published**. You can use
the functions in your own analysis and trust that they give the numbers ROS2neuro gives, because the comparison is repeated on
the same data every time you run the check.

!!! success "Download"
    - **[ros2neuro_matlab.zip](ros2neuro_matlab.zip)**: the `r2n_*` functions (one file each, float32 like ROS 2).

    The same functions are in the `matlab/` folder of [`ros2neuro_devel_test`](https://github.com/ros2neuro/ros2neuro_devel_test/tree/main/matlab),
    next to the tests per stage that check them against a recorded run, and the code of each function is further down this page.

```text
ros2neuro_devel_test/
├── matlab/                   r2n_*.m: one function per stage, copy the ones you need
├── src/                      topic_csv_recorder.py (the node that saves the topics as CSV)
└── acquisition/ filters/ processing/ decoder/ integrator/ pipeline/ feedback/    one folder per test: its launcher (.launch.py), its config/ and its check_*.m
```

## The functions

Every stage of the chain has its function. Click a name to read what it does, how it reproduces the plugin and its code.

| Function | What it reproduces | Takes → gives | Plugin page |
|---|---|---|---|
| **Filters** | | | |
| [`r2n_car`](#r2n_car) | CAR: common average reference | `[samples x channels]` → same shape | [filters_car](../packages/filters/car.md) |
| [`r2n_dc`](#r2n_dc) | DC: remove the mean of each frame | `[samples x channels]`, `block` (32) → `[floor(samples/block)*block x channels]` | [filters_dc](../packages/filters/dc.md) |
| [`r2n_laplacian`](#r2n_laplacian) | Laplacian: spatial filter | `[samples x channels]`, `layout` → same shape | [filters_laplacian](../packages/filters/laplacian.md) |
| [`r2n_window`](#r2n_window) | Hann, Hamming, Blackman, Flattop windows | `[samples x channels]`, `name`, `block` (32) → `[.. x channels]`, window | [filters_hann, filters_hamming, filters_blackman, filters_flattop](../packages/filters/hann.md) |
| [`r2n_butterworth`](#r2n_butterworth) | Butterworth: low-pass and high-pass | `[samples x channels]`, `type`, `order`, `fc`, `fs` → `y`, `b`, `a` | [filters_butterworth](../packages/filters/butterworth.md) |
| **Processing** | | | |
| [`r2n_welch`](#r2n_welch) | Welch: ln of the power spectral density | `[samples x channels]` buffer, the Welch parameters → `[frequencies x channels]` | [processing_spectral (`Welch`)](../packages/processing/spectral.md) |
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
| [`r2n_sklearn_lda_read`](#r2n_sklearn_lda_read) | Read the numbers of a scikit-learn LDA | `lda_weights.yaml` → model | [decoder_sklearn](../packages/decoder/sklearn.md) |
| [`r2n_sklearn_lda_predict`](#r2n_sklearn_lda_predict) | scikit-learn LDA | model, feature → probabilities | [decoder_sklearn](../packages/decoder/sklearn.md) |
| **Integrator and control** | | | |
| [`r2n_integrator_exponential`](#r2n_integrator_exponential) | Exponential integrator | `[frames x K]` probabilities, `alpha`, reset frames → `[frames x K]` | [integrator_exponential](../packages/integrator/exponential.md) |
| [`r2n_integrator_buffer`](#r2n_integrator_buffer) | Buffer integrator | `[frames x K]` probabilities, `buffer_size`, `increment`, reset frames, `init_val` → `[frames x K]` | [integrator_buffer](../packages/integrator/buffer.md) |
| [`r2n_threshold_winner`](#r2n_threshold_winner) | Which class touched its threshold | thresholds, values → winning class | [control_feedback](../packages/control/feedback.md) |
| **Helpers** | | | |
| [`r2n_yaml_value`](#r2n_yaml_value) | Read a parameter from a yaml file | file, key → value |  |

Click a name to jump to its dropdown; it opens by itself. Every dropdown starts with the explanation and ends with the code, which is the file of the zip.

### Filters

<a id="r2n_car"></a>

??? example "r2n_car.m: CAR: common average reference"
    **Reproduces:** [filters_car](../packages/filters/car.md)
    **Takes → gives:** `[samples x channels]` → same shape

    Subtracts from every sample the mean of all the channels at that instant, so what the channels have in common (a drift, the reference) disappears. The plugin does it row by row on each `NeuroFrame`; the function does it on the whole signal at once, because the operation has no memory.

    **How close:** The plugin adds the channels in float32, one after the other; `mean` adds them in another order. The result can differ by 1-2 ULP of the input.

    ```matlab
    --8<-- "files/r2n/r2n_car.m"
    ```

<a id="r2n_dc"></a>

??? example "r2n_dc.m: DC: remove the mean of each frame"
    **Reproduces:** [filters_dc](../packages/filters/dc.md)
    **Takes → gives:** `[samples x channels]`, `block` (32) → `[floor(samples/block)*block x channels]`

    Cuts the signal in blocks of `block` samples (one `NeuroFrame`), and subtracts from every channel the mean of **its** block. It is a high-pass with no memory: the mean is recomputed on every frame. The samples at the end that do not fill a block are dropped, as the node never gets them.

    **How close:** The plugin sums the block in float32 with Eigen; `mean` sums in another order: up to 4 ULP of the input.

    ```matlab
    --8<-- "files/r2n/r2n_dc.m"
    ```

<a id="r2n_laplacian"></a>

??? example "r2n_laplacian.m: Laplacian: spatial filter"
    **Reproduces:** [filters_laplacian](../packages/filters/laplacian.md)
    **Takes → gives:** `[samples x channels]`, `layout` → same shape

    Builds the matrix of the filter from the layout of the electrodes (a grid of channel numbers, `0` where there is no electrode): column *c* has +1 on channel *c* and −1/n on each of its *n* neighbours (left, right, up, down). The signal is then multiplied by that matrix: every channel minus the mean of its neighbours. `layout` is the matrix or the text of the yaml parameter `"1 2 3; 4 5 6; 7 8 9"`, so you can paste the parameter of your launch file.

    **How close:** One matrix product in float32; the order of the additions is not the one of Eigen: a few ULP of the input at most.

    ```matlab
    --8<-- "files/r2n/r2n_laplacian.m"
    ```

<a id="r2n_window"></a>

??? example "r2n_window.m: Hann, Hamming, Blackman, Flattop windows"
    **Reproduces:** [filters_hann, filters_hamming, filters_blackman, filters_flattop](../packages/filters/hann.md)
    **Takes → gives:** `[samples x channels]`, `name`, `block` (32) → `[.. x channels]`, window

    The four window filters are the same operation with a different window: every block of `block` samples (one `NeuroFrame`) is multiplied, sample by sample, by the same window. The windows are the **symmetric** ones (denominator N−1, the one the plugins use) and are rounded to float32 like the plugins. Returns the signal and the window.

    **How close:** A product of two float32 numbers is exact in the arithmetic of both: the result is identical to the node (difference 0).

    ```matlab
    --8<-- "files/r2n/r2n_window.m"
    ```

<a id="r2n_butterworth"></a>

??? example "r2n_butterworth.m: Butterworth: low-pass and high-pass"
    **Reproduces:** [filters_butterworth](../packages/filters/butterworth.md)
    **Takes → gives:** `[samples x channels]`, `type`, `order`, `fc`, `fs` → `y`, `b`, `a`

    Designs the Butterworth filter of the given order and cut-off (normalized to the Nyquist frequency) and runs it **causally** (forward only, as it must be online) over the whole signal, keeping the state from one sample to the next. The plugin does the same frame after frame with the state kept between frames, which gives the same numbers as one pass over the whole signal. The computation is in double, the result is rounded to float32 as the plugin publishes it. A band-pass is two of them, one after the other (high-pass at the lower edge, low-pass at the upper).

    **How close:** Same design, same recursion: the difference is 0 for the low-pass and 0.25 ULP for the 1 Hz high-pass.

    ```matlab
    --8<-- "files/r2n/r2n_butterworth.m"
    ```

### Processing

<a id="r2n_welch"></a>

??? example "r2n_welch.m: Welch: ln of the power spectral density"
    **Reproduces:** [processing_spectral (`Welch`)](../packages/processing/spectral.md)
    **Takes → gives:** `[samples x channels]` buffer, the Welch parameters → `[frequencies x channels]`

    Splits the buffer in segments of `length` samples every `length - overlap`, multiplies each by the window, takes the power spectrum of each and averages them: that is Welch's PSD (one-sided, in power/Hz). The plugin publishes `ln(max(PSD, 1e-12))` at the bins of the frequencies you ask for (`freqs`, in Hz, multiples of `fs/length`). That is what a PSD decoder (QDA, LDA, Gaussian) reads: all the channels, all the frequencies, channel by channel.

    **How close:** The window must be the symmetric one (`r2n_spectral_window`), with no detrending, `nfft = length`: with these choices the difference is 0.

    ```matlab
    --8<-- "files/r2n/r2n_welch.m"
    ```

<a id="r2n_fft"></a>

??? example "r2n_fft.m: FFT: amplitude spectrum"
    **Reproduces:** [processing_spectral (`FFT`)](../packages/processing/spectral.md)
    **Takes → gives:** `[window_length x channels]`, `fs`, window, `apply_log` → `[bins x channels]`, frequencies

    Multiplies the buffer by the window, takes the FFT and keeps the first N/2+1 bins (the one-sided spectrum). The amplitude is `|FFT| / N`, doubled on every bin but the first and the last (the energy of the negative frequencies). With `apply_log` it is expressed as `20·log10`. Computed in double like the node and rounded to float32 at the end.

    **How close:** The node and the function compute the same double and round once: the float32 numbers are the same (< 1 ULP).

    ```matlab
    --8<-- "files/r2n/r2n_fft.m"
    ```

<a id="r2n_spectrogram"></a>

??? example "r2n_spectrogram.m: Spectrogram"
    **Reproduces:** [processing_spectral (`Spectrogram`)](../packages/processing/spectral.md)
    **Takes → gives:** `[analysis_length x channels]`, `fs`, `window_length`, `overlap`, window, `apply_log` → `[segments x bins x channels]`, frequencies, times

    Cuts the buffer in overlapping segments, windows each one and computes its power spectral density (`|FFT|² / (fs·Σw²)`, doubled on the inner bins). The result is a time-frequency map; in dB when `apply_log` (`10·log10`). Also returns the frequency of every bin and the time of the centre of every segment. The feature published by the node has the same shape with the channel varying fastest.

    **How close:** Double precision like the node, rounded to float32 at the end: < 1 ULP.

    ```matlab
    --8<-- "files/r2n/r2n_spectrogram.m"
    ```

<a id="r2n_spectral_window"></a>

??? example "r2n_spectral_window.m: Window of FFT and spectrogram"
    **Reproduces:** [processing_spectral](../packages/processing/spectral.md)
    **Takes → gives:** name, `n` → window of `n` values

    The window used by `r2n_welch`, `r2n_fft` and `r2n_spectrogram`: rectangular, Hann, Hamming, Blackman or flat-top, **symmetric** (denominator n−1) and in double (not rounded to float32: that is `r2n_window`, for the filters).

    ```matlab
    --8<-- "files/r2n/r2n_spectral_window.m"
    ```

<a id="r2n_fbcsp"></a>

??? example "r2n_fbcsp.m: FBCSP features"
    **Reproduces:** [processing_fbcsp](../packages/processing/fbcsp.md)
    **Takes → gives:** one `[buffer x channels]` per band, `W` `[bands x components x channels]` → one feature vector

    The input is the signal of every band **already band-passed** (the node reads one filtered topic per band; here, `r2n_butterworth` high-pass then low-pass). For each band the window is projected on the CSP filters (`z = x · W'`), the variance of every component is taken and normalized by the sum of the variances of that band; the feature is its logarithm. The vector is band after band (`index = band · components + component`). `r2n_fbcsp_weights` rearranges the flat `filters` parameter of the plugin in the array this function takes.

    **How close:** Double arithmetic, float32 at the end: 1e-7 against the node.

    ```matlab
    --8<-- "files/r2n/r2n_fbcsp.m"
    ```

<a id="r2n_fbcsp_weights"></a>

??? example "r2n_fbcsp_weights.m: CSP filters as an array"
    **Reproduces:** [processing_fbcsp](../packages/processing/fbcsp.md)
    **Takes → gives:** flat `filters`, bands, components, channels → `[bands x components x channels]`

    The `filters` parameter of the Fbcsp plugin is a flat list ordered `[band][component][channel]`, channel varying fastest. This reorders it in the 3-D array `r2n_fbcsp` takes.

    ```matlab
    --8<-- "files/r2n/r2n_fbcsp_weights.m"
    ```

### Decoders

<a id="r2n_softmax"></a>

??? example "r2n_softmax.m: Softmax of the scores"
    **Reproduces:** [decoder_lda, decoder_qda, decoder_svm](../packages/decoder/index.md)
    **Takes → gives:** scores `[K]` → probabilities `[K]`

    How LDA, QDA and SVM turn their scores into probabilities: `exp(score − max)` (the maximum is subtracted so that nothing overflows) divided by the sum, added **in order** in float32 like the C++. If the sum is not above the float32 epsilon the values are returned as they are, as the C++ does.

    ```matlab
    --8<-- "files/r2n/r2n_softmax.m"
    ```

<a id="r2n_linear_read"></a>

??? example "r2n_linear_read.m: Read the `.r2nd` of LDA and SVM"
    **Reproduces:** [decoder_lda, decoder_svm](../packages/decoder/lda.md)
    **Takes → gives:** `.r2nd` file → model

    Reads the binary model that the decoder node loads (header `R2NDEC1`, little endian, versions 1 and 2) skipping the fields the prediction does not use. You get the selected features (the pairs channel / frequency, 0-based), the weights (one row per class), the bias, the classes and the frequencies. A linear SVM has the same file layout as the LDA.

    ```matlab
    --8<-- "files/r2n/r2n_linear_read.m"
    ```

<a id="r2n_linear_predict"></a>

??? example "r2n_linear_predict.m: LDA and linear SVM"
    **Reproduces:** [decoder_lda, decoder_svm](../packages/decoder/lda.md)
    **Takes → gives:** model, PSD feature → probabilities, scores

    Takes from the feature (all the channels × all the frequencies, channel by channel) the values the model selected, computes for every class `score = bias + Σ w·x` adding in the order of the selection, and turns the scores into probabilities with `r2n_softmax`. A model whose output is `TYPE_SCORES` publishes the scores instead: both are returned.

    **How close:** Same float32 operations in the same order as the C++: 6e-8 against the node.

    ```matlab
    --8<-- "files/r2n/r2n_linear_predict.m"
    ```

<a id="r2n_qda_read"></a>

??? example "r2n_qda_read.m: Read the `.r2nd` of QDA"
    **Reproduces:** [decoder_qda](../packages/decoder/qda.md)
    **Takes → gives:** `.r2nd` file → model

    The same reader as the LDA one, for the QDA layout (version 2): besides the linear weights it reads the quadratic matrix of every class (stored row by row).

    ```matlab
    --8<-- "files/r2n/r2n_qda_read.m"
    ```

<a id="r2n_qda_predict"></a>

??? example "r2n_qda_predict.m: QDA"
    **Reproduces:** [decoder_qda](../packages/decoder/qda.md)
    **Takes → gives:** model, PSD feature → probabilities, scores

    For every class: `score = bias + Σ l·x + Σ_row Σ_col x_row · Q(row, col) · x_col`, the three sums added in this order in float32 like `QDA.cpp`; then `r2n_softmax`. The selected features are taken from the PSD exactly as for the LDA.

    **How close:** Same operations in the same order: 1.5e-8 against the node.

    ```matlab
    --8<-- "files/r2n/r2n_qda_predict.m"
    ```

<a id="r2n_gaussian_read"></a>

??? example "r2n_gaussian_read.m: Read the `.r2nd` of the Gaussian decoder"
    **Reproduces:** [decoder_gaussian](../packages/decoder/gaussian.md)
    **Takes → gives:** `.r2nd` file → model

    Reads the Gaussian model (version 2) that comes from a Matlab SMR classifier: priors, selected features, and for every class and prototype the centers and the covariances (diagonal).

    ```matlab
    --8<-- "files/r2n/r2n_gaussian_read.m"
    ```

<a id="r2n_gaussian_predict"></a>

??? example "r2n_gaussian_predict.m: Gaussian decoder"
    **Reproduces:** [decoder_gaussian](../packages/decoder/gaussian.md)
    **Takes → gives:** model, PSD feature → probabilities

    For every class, every prototype *q* gives an activation `Σ_j −0.5·d_j²/v_j − 0.5·ln v_j` (`d` = feature − center, `v` = variance); the class score is the log-sum-exp of its prototypes plus `ln(prior)`. The probabilities are `exp(score − max)` divided by the sum. All in float32, in the order of `Gaussian.cpp`.

    **How close:** 1.5e-7 against the node (one ULP of a probability).

    ```matlab
    --8<-- "files/r2n/r2n_gaussian_predict.m"
    ```

<a id="r2n_sklearn_lda_read"></a>

??? example "r2n_sklearn_lda_read.m: Read the numbers of a scikit-learn LDA"
    **Reproduces:** [decoder_sklearn](../packages/decoder/sklearn.md)
    **Takes → gives:** `lda_weights.yaml` → model

    MATLAB cannot open a scikit-learn file. `data/models/export_lda_weights.py` writes the numbers of the `StandardScaler` + `LinearDiscriminantAnalysis` pipeline (mean, scale, coefficients, intercept, classes, selected features) in a yaml, after checking in Python that they give the same `predict_proba`; this function reads them. Python needs no such step: `r2n_sklearn_load` opens the model directly.

    ```matlab
    --8<-- "files/r2n/r2n_sklearn_lda_read.m"
    ```

<a id="r2n_sklearn_lda_predict"></a>

??? example "r2n_sklearn_lda_predict.m: scikit-learn LDA"
    **Reproduces:** [decoder_sklearn](../packages/decoder/sklearn.md)
    **Takes → gives:** model, feature → probabilities

    `z = (x − mean) / scale`, `d = coef·z + intercept`; with two classes `p = 1/(1 + e^{−d})` for the second class of scikit-learn and its complement for the first; with more classes a softmax. In double, as scikit-learn does, rounded to float32 like the published prediction, in the order of the decoder's output fields.

    ```matlab
    --8<-- "files/r2n/r2n_sklearn_lda_predict.m"
    ```

### Integrator and control

<a id="r2n_integrator_exponential"></a>

??? example "r2n_integrator_exponential.m: Exponential integrator"
    **Reproduces:** [integrator_exponential](../packages/integrator/exponential.md)
    **Takes → gives:** `[frames x K]` probabilities, `alpha`, reset frames → `[frames x K]`

    The recursion `state = alpha·state + (1−alpha)·prediction`, in float32. The first prediction of the run becomes the state. At the frames of `reset_frames` the state goes back to 1/K **before** that frame is integrated (the node integrates the frame that contains the CFeedback event and resets after it: the caller passes the frame after). It also returns the time of every reset.

    **How close:** Same recursion: difference 0.

    ```matlab
    --8<-- "files/r2n/r2n_integrator_exponential.m"
    ```

<a id="r2n_integrator_buffer"></a>

??? example "r2n_integrator_buffer.m: Buffer integrator"
    **Reproduces:** [integrator_buffer](../packages/integrator/buffer.md)
    **Takes → gives:** `[frames x K]` probabilities, `buffer_size`, `increment`, reset frames, `init_val` → `[frames x K]`

    A bar that moves: at every frame the class with the highest probability (the first on a tie) goes up by one step and the others go down by the same total, in equal shares (a class that reaches 0 stops and the rest goes to the others). The step is `1/buffer_size` (hard, `increment = 0`) or the winning probability over `buffer_size` (soft, `increment = 1`). At a reset the buffer returns to `init_val` (default 1/K).

    **How close:** Same operations in float32: < 1 ULP.

    ```matlab
    --8<-- "files/r2n/r2n_integrator_buffer.m"
    ```

<a id="r2n_threshold_winner"></a>

??? example "r2n_threshold_winner.m: Which class touched its threshold"
    **Reproduces:** [control_feedback](../packages/control/feedback.md)
    **Takes → gives:** thresholds, values → winning class

    The test `control_feedback` uses to decide a trial: a class is over its own threshold when `value + 1e-6 >= threshold` (in float32). When several are over, the highest wins. It is used to recompute Hit / Miss / Timeout from the integrated values.

    ```matlab
    --8<-- "files/r2n/r2n_threshold_winner.m"
    ```

### Helpers

<a id="r2n_yaml_value"></a>

??? example "r2n_yaml_value.m: Read a parameter from a yaml file"
    **Reproduces:** the checks of the tests
    **Takes → gives:** file, key → value

    Reads `key: value` from a yaml parameter file of ros2neuro (flat keys such as `processing.params.wlength`): a number, a list `[a, b, c]`, `true`/`false` or text. The checks use it to read every parameter from the **same file** the launcher gives to the node, so no number is typed twice. (In Python use `yaml.safe_load`.)

    ```matlab
    --8<-- "files/r2n/r2n_yaml_value.m"
    ```

## Use a function in your own analysis

Put the `matlab/` folder on the path and call the function on a `[samples x channels]` matrix:

```matlab
addpath('ros2neuro_devel_test/matlab');

x   = single(eeg);                              % your signal, samples x channels
y   = r2n_dc(x, 32);                            % remove the mean of every 32-sample frame, as the DC filter does
y   = r2n_butterworth(y, 'high', 4, 1, 512);    % 4th-order high-pass at 1 Hz, fs 512 Hz
y   = r2n_laplacian(y, '1 2 3; 4 5 6; 7 8 9');  % the layout you give to the Laplacian filter
psd = r2n_welch(double(y(1:512, :)), struct('fs', 512, 'length', 256, 'overlap', 128, 'window', 'hann', 'freqs', 4:2:48));
```

Each function says in its header which ROS 2 plugin it reproduces, what it expects and what it returns, and each one is a
single file with no dependency on the others (except: a `*_predict` takes what its `*_read` returns, `r2n_linear_predict` and
`r2n_qda_predict` use `r2n_softmax`, `r2n_fft` and `r2n_spectrogram` use `r2n_spectral_window`), so you can copy just the ones you need. The yaml reader `r2n_yaml_value(file, key)` reads a parameter from the same file the node loads, which is how
the checks of the tests per stage read every parameter from the same yaml the launchers use, to avoid typing a number twice.

!!! tip "A few ULP of difference are expected"
    The ROS 2 plugins compute in float32 with Eigen, which adds the values one after the other in float32. MATLAB's `mean` and its matrix product add in
    another order, so the DC, the CAR and the Laplacian can differ from the node by a few ULP of the input (the largest difference measured is 2 ULP). That is why
    the tolerances are written in ULP of the largest input sample and not as a fixed number.

## What is not covered yet

The stages below have no MATLAB function checked against ROS 2. Contributions are welcome: follow the pattern of `r2n_car.m`
(header, one computation) and add its check to a test folder.

| Stage | Package |
|---|---|
| the deep-learning decoder ([`decoder_braindecode`](../packages/decoder/braindecode.md)): the network cannot be redone with the `r2n` functions; the test of `decoder/shallow/` checks the window it reads in MATLAB and the network in Python against PyTorch | [`decoder_braindecode`](../packages/decoder/braindecode.md) |
| [`control_feedback`](../packages/control/feedback.md): calibration autopilot, `rest_mode`, protocol `control` | [`control_feedback`](../packages/control/feedback.md) |

The evaluation protocol is covered (Hit / Miss / Timeout are recomputed from the integrated values in the integrator test), and the rejection of the
integrator is not reproduced.
