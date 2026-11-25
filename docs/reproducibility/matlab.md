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

## What was checked, and how close it is

| Stage | ROS 2 package | MATLAB function | Compared with | Largest difference |
|---|---|---|---|---|
| CAR | [`filters_car`](../packages/filters/car.md) | `r2n_car` | the node, 327 680 values | 2 ULP |
| DC | [`filters_dc`](../packages/filters/dc.md) | `r2n_dc` | the node, 327 680 values | 4 ULP |
| Laplacian | [`filters_laplacian`](../packages/filters/laplacian.md) | `r2n_laplacian` | the node, 92 160 values | **0** |
| Hann, Hamming, Blackman, Flattop | [`filters_hann`](../packages/filters/hann.md) and the others | `r2n_window` | the node, 327 680 values each | **0** |
| Butterworth low-pass 40 Hz | [`filters_butterworth`](../packages/filters/butterworth.md) | `r2n_butterworth` | the node, 327 680 values | **0** |
| Butterworth high-pass 1 Hz | [`filters_butterworth`](../packages/filters/butterworth.md) | `r2n_butterworth` | the node, 327 680 values | 0.25 ULP |
| Filter chain `dc > hp > lp > car > hann` | [`ros2neuro_filters`](../packages/filters/index.md) | the five above, one after the other | the node, 327 680 values | 5 ULP |
| Welch PSD (ln) | [`processing_spectral`](../packages/processing/spectral.md) | `r2n_welch` | the processing test, on the raw frames | **0** |
| Gaussian decoder | [`decoder_gaussian`](../packages/decoder/gaussian.md) | `r2n_gaussian_read`, `r2n_gaussian_predict` | the decoder test, 1794 predictions | 1.5e-7 |
| Exponential integrator | [`integrator_exponential`](../packages/integrator/exponential.md) | `r2n_integrator_exponential` | the integrator test, 1794 values | **0** |
| LDA decoder | [`decoder_lda`](../packages/decoder/lda.md) | `r2n_linear_read`, `r2n_linear_predict` | the node, 60 features, made-up model | 6e-8 |
| SVM decoder (linear) | [`decoder_svm`](../packages/decoder/svm.md) | `r2n_linear_read`, `r2n_linear_predict` | the node, 60 features, made-up model | 6e-8 |
| QDA decoder | [`decoder_qda`](../packages/decoder/qda.md) | `r2n_qda_read`, `r2n_qda_predict` | the node, 60 features, made-up model | 1.5e-8 |
| Buffer integrator, hard and soft | [`integrator_buffer`](../packages/integrator/buffer.md) | `r2n_integrator_buffer` | the node, 120 predictions each | < 1 ULP |
| FFT (amplitude) | [`processing_spectral`](../packages/processing/spectral.md) | `r2n_fft` | the plugin, 33 windows | < 1 ULP |
| Spectrogram (dB) | [`processing_spectral`](../packages/processing/spectral.md) | `r2n_spectrogram` | the plugin, 25 buffers of 7 segments | < 1 ULP |
| Hit / Miss / Timeout | [`control_feedback`](../packages/control/feedback.md) | `r2n_threshold_winner` | the integrator test, 8 trials | 8 of 8 equal |
| Resets of the integrator | [`integrator`](../packages/integrator/index.md) | `r2n_integrator_exponential`, `r2n_integrator_buffer` | the integrator test: the neutral message of every reset | 8 resets, one per CFeedback |

## Whole pipelines

The `pipeline/` tests chain every step, from the raw samples to the flow that drives the feedback window, and compare each one with ROS 2 (largest difference over about 1 800 messages and 58 000 samples; the filters are in the units of the signal, the later steps in the units of the quantity):

| Step | QDA | LDA | FBCSP + LDA | Tolerance |
|---|---|---|---|---|
| raw | 0 | 0 | 0 | 0 |
| Laplacian | 0.0029 | 0.0029 | | 0.016 |
| band-pass (hp 1 Hz, lp 60 Hz) | 0.00098 | 0.00098 | | 0.031 |
| band chains of FBCSP (8-12 Hz, 16-20 Hz) | | | 0 and 6e-8 | 0.031 |
| Welch PSD (ln) | 2.6e-4 | 2.6e-4 | | 1e-3 |
| FBCSP feature | | | 1.2e-7 | 1e-3 |
| decoder probabilities | 2.6e-5 | 2.5e-5 | 0 | 1e-3 |
| integrator | 1e-6 | 2.5e-6 | 0 | 1e-3 |
| control flow (what the window draws) | 2e-7 | 3e-7 | 2e-7 | 1e-3 |

The deep-learning pipeline is checked in [Python](python.md): band-pass 5e-4, window 3e-4, network 1.4e-6, integrator 5e-7, flow 3e-7. The later steps have an absolute tolerance because the rounding of the filters is amplified by the `ln` of the power; a step fed with the ROS 2 output of the step before (the integrator alone, a decoder on the ROS PSD) agrees to a few ULP.

**ULP** is the distance between two neighbouring float32 numbers. The EEG in the test files is of the order of 10 000 µV, where one
ULP is 0.001 µV: a difference of 2 ULP is the last bit of the number, not a difference of method. The differences of the decoders and
the integrators are in the units of the quantity (probabilities and integrated values are between 0 and 1, so 1e-7 is one ULP there).
The FFT and the spectrogram compute in double, like the node, and round to float32 only at the end: they give the same float32 number.

!!! note "How the tolerance is chosen"
    The check does not use one fixed number. It accepts a few ULP **of the largest input sample** (4 for the single-stage filters,
    8 for the DC and the chain, where the mean and the cascaded stages add rounding). The input sets the scale because the filters add
    values of that size even when what they output is much smaller. A fixed `1e-3` would be right for a signal around 10 000 and
    wrong for any other.

The tests are useful as regression tests too: if you change a plugin and the numbers move, the line of that stage turns to
**FAIL** with the largest difference and where it is.

## Run the checks

You need MATLAB R2019b or newer with the **Signal Processing Toolbox**: the filters are written with the native functions of MATLAB
(`butter` + `filter`, `pwelch`, `hann`, `hamming`, `blackman`, `flattopwin`, `mean`, `var`), so that the check does not depend on how ROS 2 designs
its filters. Reading a GDF (the tests) needs [BIOSIG](https://biosig.sourceforge.net).

Each stage has a test in [`ros2neuro_devel_test`](../packages/devel-test.md): `acquisition/`, `filters/` (each filter alone, and three chains), `processing/`
(Welch, FFT, spectrogram, buffer, FBCSP), `decoder/` (QDA, LDA, Gaussian, LDA on FBCSP, ShallowNet) and `integrator/` (whole pipelines to the exponential and the buffer integrator) and `pipeline/` (the complete pipeline with the feedback window: QDA, LDA, FBCSP + LDA, and a deep-learning model checked in Python). A test replays a GDF
file through the nodes of its stage, with the manager running a protocol so that the session ends by itself, and saves what the nodes published as CSV; its
`check_*.m` redoes the stage in MATLAB from the samples of the same GDF and compares:

```bash
# in the container (about 2 minutes; the session ends by itself)
ros2 launch ~/ros2neuro_ws/src/ros2neuro_devel_test/decoder/qda/decoder_qda.launch.py
```
```matlab
% in MATLAB, in the folder of the test
cd ros2neuro_devel_test/decoder/qda
check_decoder_qda
```

```text
  PASS  input: the raw frames are the samples of the file 58016 samples
  PASS  decoder qda (probabilities)     1.19e-07 (tolerance 4.77e-07)  1798 predictions, 3596 values, 1 ULP of the largest value 1
  PASS  number of trials                8 Start events, protocol trials [4 4]
  ...
check_decoder_qda: 12 checks, 12 passed, 0 failed, 0 known issue(s)
```

Every stage is checked **on its own**, from what ROS 2 published for the stage before (the PSD that a decoder read, the predictions that an integrator
integrated), so a rounding of a few ULP of an input does not grow along the chain and the line of a stage says whether *that* stage agrees. The processing plugins are
checked on the raw frames, which are the samples of the GDF. A message carries the stamp of the last frame it was made from, which is how the check pairs it with the
window of samples. Each check was also run with a parameter changed on the MATLAB side (a cut-off, an overlap, an alpha) and it fails, as it must.

!!! note "The reset can be one frame earlier"
    The rule is that ROS 2 integrates the frame that contains the CFeedback event and resets after it. The events and the values travel on different
    topics and their order is not guaranteed, so now and then the event overtakes the frame and the reset is one frame earlier. MATLAB cannot know the order, so the
    integrator test takes the resets **as ROS 2 made them** (the neutral messages the integrator publishes, which repeat the stamp of the message before) to verify the
    arithmetic, and checks that there is one per CFeedback event and that each is within two frames of its event.

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

## The code of every function

One block per function; each starts with what it reproduces. They are also in the zip.

??? example "r2n_car.m: CAR"
    ```matlab
    --8<-- "files/r2n/r2n_car.m"
    ```

??? example "r2n_dc.m: DC"
    ```matlab
    --8<-- "files/r2n/r2n_dc.m"
    ```

??? example "r2n_laplacian.m: Laplacian"
    ```matlab
    --8<-- "files/r2n/r2n_laplacian.m"
    ```

??? example "r2n_window.m: Hann, Hamming, Blackman, Flattop"
    ```matlab
    --8<-- "files/r2n/r2n_window.m"
    ```

??? example "r2n_butterworth.m: Butterworth"
    ```matlab
    --8<-- "files/r2n/r2n_butterworth.m"
    ```

??? example "r2n_welch.m: Welch PSD"
    ```matlab
    --8<-- "files/r2n/r2n_welch.m"
    ```

??? example "r2n_fft.m: FFT (amplitude spectrum)"
    ```matlab
    --8<-- "files/r2n/r2n_fft.m"
    ```

??? example "r2n_spectrogram.m: spectrogram"
    ```matlab
    --8<-- "files/r2n/r2n_spectrogram.m"
    ```

??? example "r2n_spectral_window.m: the window of FFT and spectrogram"
    ```matlab
    --8<-- "files/r2n/r2n_spectral_window.m"
    ```

??? example "r2n_gaussian_read.m: reads the `.r2nd` of the Gaussian decoder"
    ```matlab
    --8<-- "files/r2n/r2n_gaussian_read.m"
    ```

??? example "r2n_gaussian_predict.m: Gaussian decoder"
    ```matlab
    --8<-- "files/r2n/r2n_gaussian_predict.m"
    ```

??? example "r2n_linear_read.m: reads the `.r2nd` of the LDA and SVM decoders"
    ```matlab
    --8<-- "files/r2n/r2n_linear_read.m"
    ```

??? example "r2n_linear_predict.m: LDA and SVM decoders"
    ```matlab
    --8<-- "files/r2n/r2n_linear_predict.m"
    ```

??? example "r2n_qda_read.m: reads the `.r2nd` of the QDA decoder"
    ```matlab
    --8<-- "files/r2n/r2n_qda_read.m"
    ```

??? example "r2n_qda_predict.m: QDA decoder"
    ```matlab
    --8<-- "files/r2n/r2n_qda_predict.m"
    ```

??? example "r2n_softmax.m: scores to probabilities (LDA, QDA, SVM)"
    ```matlab
    --8<-- "files/r2n/r2n_softmax.m"
    ```

??? example "r2n_integrator_exponential.m: exponential integrator"
    ```matlab
    --8<-- "files/r2n/r2n_integrator_exponential.m"
    ```

??? example "r2n_integrator_buffer.m: buffer integrator"
    ```matlab
    --8<-- "files/r2n/r2n_integrator_buffer.m"
    ```

??? example "r2n_threshold_winner.m: which class touched its threshold"
    ```matlab
    --8<-- "files/r2n/r2n_threshold_winner.m"
    ```

??? example "r2n_yaml_value.m: reads a parameter of a yaml file"
    ```matlab
    --8<-- "files/r2n/r2n_yaml_value.m"
    ```

??? example "r2n_fbcsp.m: FBCSP features"
    ```matlab
    --8<-- "files/r2n/r2n_fbcsp.m"
    ```

??? example "r2n_fbcsp_weights.m: the CSP filters of the Fbcsp plugin as an array"
    ```matlab
    --8<-- "files/r2n/r2n_fbcsp_weights.m"
    ```

??? example "r2n_sklearn_lda_read.m: reads the numbers of a scikit-learn LDA"
    ```matlab
    --8<-- "files/r2n/r2n_sklearn_lda_read.m"
    ```

??? example "r2n_sklearn_lda_predict.m: scikit-learn LDA"
    ```matlab
    --8<-- "files/r2n/r2n_sklearn_lda_predict.m"
    ```

Every `check_*.m` of the repository is one self-contained file (no helper functions): read it from the top to see what is read, what is recomputed and how it is compared.

## What is not covered yet

The stages below have no MATLAB function checked against ROS 2. Contributions are welcome: follow the pattern of `r2n_car.m`
(header, one computation) and add its check to a test folder.

| Stage | Package |
|---|---|
| the deep-learning decoder ([`decoder_braindecode`](../packages/decoder/braindecode.md)): the network cannot be redone with the `r2n` functions; the test of `decoder/shallow/` checks the window it reads in MATLAB and the network in Python against PyTorch | [`decoder_braindecode`](../packages/decoder/braindecode.md) |
| [`control_feedback`](../packages/control/feedback.md): calibration autopilot, `rest_mode`, protocol `control` | [`control_feedback`](../packages/control/feedback.md) |

The evaluation protocol is covered (Hit / Miss / Timeout are recomputed from the integrated values in the integrator test), and the rejection of the
integrator is not reproduced.
