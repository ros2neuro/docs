# Packages: the tests of every stage

!!! info ""
    Package: [`ros2neuro_devel_test`](https://github.com/ros2neuro/ros2neuro_devel_test) · part of [Reproducibility](../index.md)

Every stage of the stack has a test that runs without hardware: it replays a **GDF file** through the real nodes of the stage, saves what ROS 2 computed as CSV, and a check redoes the stage from the samples of the same GDF, in MATLAB or in Python, and compares. PASS / FAIL for every line; the check errors if one fails. This section has **one page per package** with the tests of its plugins, and the general information on how the tests are built and run.

## The pages of this section

| Page | What is tested | Functions that replay it |
|---|---|---|
| [Acquisition](acquisition.md) | the XDF plugin publishes the GDF exactly; the trials of the manager | none |
| [Filters](filters.md) | every filter alone and three chains | [DC, CAR, Laplacian, windows, Butterworth](../matlab.md#filters) |
| [Processing](processing.md) | Welch, FFT, spectrogram, Buffer, FBCSP | [Welch, FFT, spectrogram, FBCSP](../matlab.md#processing) |
| [Decoder](decoder.md) | QDA, LDA, Gaussian, LDA on FBCSP, ShallowNet | [`.r2nd` readers and predictors](../matlab.md#decoders), [scikit-learn and braindecode loaders](../python.md#ml-and-deep-learning-models) |
| [Integrator](integrator.md) | whole pipelines ending in each integrator, resets, outcomes | [exponential and buffer integrators](../matlab.md#integrator-and-control) |
| [Control](control.md) | Hit / Miss / Timeout recomputed from the integrated values | [`r2n_threshold_winner`](../matlab.md#r2n_threshold_winner) |
| [Manager](manager.md) | the trials of a calibration and an evaluation | none |
| [Feedback](feedback.md) | the windows, to be looked at | none |
| [Visualizer](visualizer.md) | the helpers that do not need a display | none |
| [Pipeline](../pipeline.md) | the **complete** pipelines, from the raw samples to the flow of the feedback | all of them |

## What was checked, and how close it is

| Stage | ROS 2 package | function | Python function | Compared with | Largest difference |
|---|---|---|---|---|---|
| CAR | [`filters_car`](../../packages/filters/car.md) | [`r2n_car`](../matlab.md#r2n_car) | [`r2n_car`](../python.md#r2n_car) | the node, 327 680 values | 2 ULP |
| DC | [`filters_dc`](../../packages/filters/dc.md) | [`r2n_dc`](../matlab.md#r2n_dc) | [`r2n_dc`](../python.md#r2n_dc) | the node, 327 680 values | 4 ULP |
| Laplacian | [`filters_laplacian`](../../packages/filters/laplacian.md) | [`r2n_laplacian`](../matlab.md#r2n_laplacian) | [`r2n_laplacian`](../python.md#r2n_laplacian) | the node, 92 160 values | **0** |
| Hann, Hamming, Blackman, Flattop | [`filters_hann`](../../packages/filters/hann.md) and the others | [`r2n_window`](../matlab.md#r2n_window) | [`r2n_window`](../python.md#r2n_window) | the node, 327 680 values each | **0** |
| Butterworth low-pass 40 Hz | [`filters_butterworth`](../../packages/filters/butterworth.md) | [`r2n_butterworth`](../matlab.md#r2n_butterworth) | [`r2n_butterworth`](../python.md#r2n_butterworth) | the node, 327 680 values | **0** |
| Butterworth high-pass 1 Hz | [`filters_butterworth`](../../packages/filters/butterworth.md) | [`r2n_butterworth`](../matlab.md#r2n_butterworth) | [`r2n_butterworth`](../python.md#r2n_butterworth) | the node, 327 680 values | 0.25 ULP |
| Filter chain `dc > hp > lp > car > hann` | [`ros2neuro_filters`](../../packages/filters/index.md) | the five above, one after the other | the same functions | the node, 327 680 values | 5 ULP |
| Welch PSD (ln) | [`processing_spectral`](../../packages/processing/spectral.md) | [`r2n_welch`](../matlab.md#r2n_welch) | [`r2n_welch`](../python.md#r2n_welch) | the processing test, on the raw frames | **0** |
| Gaussian decoder | [`decoder_gaussian`](../../packages/decoder/gaussian.md) | [`r2n_gaussian_read`](../matlab.md#r2n_gaussian_read), [`r2n_gaussian_predict`](../matlab.md#r2n_gaussian_predict) | [`r2n_gaussian_read`](../python.md#r2n_gaussian_read), [`r2n_gaussian_predict`](../python.md#r2n_gaussian_predict) | the decoder test, 1794 predictions | 1.5e-7 |
| Exponential integrator | [`integrator_exponential`](../../packages/integrator/exponential.md) | [`r2n_integrator_exponential`](../matlab.md#r2n_integrator_exponential) | [`r2n_integrator_exponential`](../python.md#r2n_integrator_exponential) | the integrator test, 1794 values | **0** |
| LDA decoder | [`decoder_lda`](../../packages/decoder/lda.md) | [`r2n_linear_read`](../matlab.md#r2n_linear_read), [`r2n_linear_predict`](../matlab.md#r2n_linear_predict) | [`r2n_linear_read`](../python.md#r2n_linear_read), [`r2n_linear_predict`](../python.md#r2n_linear_predict) | the node, 60 features, made-up model | 6e-8 |
| SVM decoder (linear) | [`decoder_svm`](../../packages/decoder/svm.md) | [`r2n_linear_read`](../matlab.md#r2n_linear_read), [`r2n_linear_predict`](../matlab.md#r2n_linear_predict) | [`r2n_linear_read`](../python.md#r2n_linear_read), [`r2n_linear_predict`](../python.md#r2n_linear_predict) | the node, 60 features, made-up model | 6e-8 |
| QDA decoder | [`decoder_qda`](../../packages/decoder/qda.md) | [`r2n_qda_read`](../matlab.md#r2n_qda_read), [`r2n_qda_predict`](../matlab.md#r2n_qda_predict) | [`r2n_qda_read`](../python.md#r2n_qda_read), [`r2n_qda_predict`](../python.md#r2n_qda_predict) | the node, 60 features, made-up model | 1.5e-8 |
| Buffer integrator, hard and soft | [`integrator_buffer`](../../packages/integrator/buffer.md) | [`r2n_integrator_buffer`](../matlab.md#r2n_integrator_buffer) | [`r2n_integrator_buffer`](../python.md#r2n_integrator_buffer) | the node, 120 predictions each | < 1 ULP |
| FFT (amplitude) | [`processing_spectral`](../../packages/processing/spectral.md) | [`r2n_fft`](../matlab.md#r2n_fft) | [`r2n_fft`](../python.md#r2n_fft) | the plugin, 33 windows | < 1 ULP |
| Spectrogram (dB) | [`processing_spectral`](../../packages/processing/spectral.md) | [`r2n_spectrogram`](../matlab.md#r2n_spectrogram) | [`r2n_spectrogram`](../python.md#r2n_spectrogram) | the plugin, 25 buffers of 7 segments | < 1 ULP |
| Hit / Miss / Timeout | [`control_feedback`](../../packages/control/feedback.md) | [`r2n_threshold_winner`](../matlab.md#r2n_threshold_winner) | [`r2n_threshold_winner`](../python.md#r2n_threshold_winner) | the integrator test, 8 trials | 8 of 8 equal |
| Resets of the integrator | [`integrator`](../../packages/integrator/index.md) | [`r2n_integrator_exponential`](../matlab.md#r2n_integrator_exponential), [`r2n_integrator_buffer`](../matlab.md#r2n_integrator_buffer) | [`r2n_integrator_exponential`](../python.md#r2n_integrator_exponential), [`r2n_integrator_buffer`](../python.md#r2n_integrator_buffer) | the integrator test: the neutral message of every reset | 8 resets, one per CFeedback |


## The tests

Every test replays the same **GDF file** (`data/test.gdf`, 16 EEG channels + trigger, 512 Hz, 250 s; `data/test_mi.gdf` for the deep-learning model) through real ros2neuro nodes, and the **check** redoes the same computation offline, from the samples of the file, and compares it with what ROS 2 published. For MATLAB the reference uses the **native functions** (`butter` + `filter`, `pwelch`, `hann` / `hamming` / `blackman` / `flattopwin`, `mean`, `var`, the matrix product): the functions `matlab/r2n_*.m` are ours but thin wrappers around them, released so that anyone can **replay offline what was done online**. Every check prints PASS / FAIL lines, **errors if one fails**, and draws one figure per step: above the signal of MATLAB and the signal of ros2neuro, below their difference, with the time axes linked (zoom one, the other follows). In the figures of the integrator and of the control flow the **threshold** the classes had to reach is drawn, and every trial is a coloured band from CFeedback to its outcome (**green Hit, red Miss, grey Timeout**, with its cue); where the flow does not exist (outside the trials) the line is broken instead of joining the segments.

| Folder | What it tests | Launcher | Check | Figures |
|---|---|---|---|---|
| `acquisition/` | the **XDF acquisition** plugin: it publishes the GDF exactly (every sample, 32 per frame, 16 frames/s) and the manager's 6 trials (events, durations, outcomes) | `acquisition` | `check_acquisition` (MATLAB) | signal, difference, timing; tables of signal, events and trials |
| `filters/single_filter/` | **every filter** alone: dc, hp, lp, car, laplacian, hann, hamming, blackman, flattop (nine nodes on the same frames) | `filters_single` | `check_filters_single` | one per filter |
| `filters/chain/` | three chains: hp-lp, hp-lp-laplacian, and every filter together | `filters_chain` | `check_filters_chains` | one per chain |
| `processing/welch/` `fft/` `spectrogram/` `buffer/` `fbcsp/` | **every processing plugin** on the raw frames (`fbcsp`: nine band chains, then the plugin) | `processing_<plugin>` | `check_processing_<plugin>` | one per plugin |
| `decoder/qda/` `lda/` `gaussian/` `fbcsp_lda/` `shallow/` | **some decoders**, each on its own feature: QDA, LDA, Matlab SMR Gaussian classifier, LDA (scikit-learn) on FBCSP, ShallowNet (deep learning) | `decoder_<decoder>` | `check_decoder_<decoder>` (+ `check_decoder_shallow.py` for the network, + `check_decoder_fbcsp_laplacian.py`) | probabilities |
| `integrator/exponential/` `buffer/` | **whole pipelines** ending in each integrator: raw, Laplacian, band-pass, Welch, QDA, integrator (and the resets, the outcome of every trial) | `integrator_<kind>` | `check_integrator_<kind>` | one per step, all linked |
| `pipeline/qda/` `lda/` `fbcsp/` `dl/` | the **complete pipeline with the feedback window**, four of them: QDA (wheel), LDA (bars), FBCSP + LDA (wheel), ShallowNet (wheel) | `pipeline_<name>` | `check_pipeline_<name>` (MATLAB); `check_pipeline_dl.py` (**Python**: ROS 2 against scipy and PyTorch) | one per step, all linked |
| `feedback/wheel/` `bars2/` `bars4/` | the feedback windows: the **wheel** and the **bars** (2 and 4 classes), **to be looked at**. This is the test to run on a **new computer after installing**: nothing is saved or checked, if the window moves the install is good | `feedback_<wheel\|bars2\|bars4>` | (none) | the window |

The tests of `acquisition/`, `filters/` and `processing/` run the manager in **calibration** (the autopilot drives the feedback, no classifier needed); the others in **evaluation**. The manager and the control are in every test so that the session has a structure (events) and **ends by itself** when the trials are over: calibration 6 trials, about a minute; evaluation 8 trials, 2-3 minutes. **`pipeline/`** is the folder to read to know exactly what is done online: every step of the chain, with the parameters, is written in its launcher and its check.


## Run the checks

You need MATLAB R2019b or newer with the **Signal Processing Toolbox**: the filters are written with the native functions of MATLAB
(`butter` + `filter`, `pwelch`, `hann`, `hamming`, `blackman`, `flattopwin`, `mean`, `var`), so that the check does not depend on how ROS 2 designs
its filters. Reading a GDF (the tests) needs [BIOSIG](https://biosig.sourceforge.net).

Each stage has a test in [`ros2neuro_devel_test`](index.md): `acquisition/`, `filters/` (each filter alone, and three chains), `processing/`
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


## After installing ros2neuro on a new computer

Run the feedback test: it starts the whole chain and opens the window.
```bash
ros2 launch ros2neuro_devel_test feedback_wheel.launch.py     # the wheel (2 classes)
ros2 launch ros2neuro_devel_test feedback_bars4.launch.py     # the bars with 4 classes
```
If the window opens and moves through the trials, the packages, the models, the display and the OpenGL driver work. It records nothing, so it works from the apt install too.


## Layout

```
data/            test.gdf, test_mi.gdf (the only thing the tests share, with models/: decoder models and the scripts that make them)
matlab/          r2n_*.m: one MATLAB function per stage (see its README)
python/          r2n_*.py: the same functions in Python, plus the loaders of the .r2nd, scikit-learn and braindecode models
src/             topic_csv_recorder.py (the recorder node)
acquisition/ filters/ processing/ decoder/ integrator/ pipeline/ feedback/     one folder per test: launcher, config/ (EVERY yaml the test needs: acquisition, layout, protocol, ...), check_*.m (self-contained: no helper functions, read it top to bottom), runs/ (the CSV)
```


## How a test is built

* **Every launcher** (`<name>.launch.py`) starts the recorder and the stage under test first, then (after 6 s, `DELAY`) the acquisition (XDF plugin, replay of the GDF, 16 frames/s of 32 samples), the manager and the control (a protocol; they shut the launch down when they end).
* **The recorder** (`src/topic_csv_recorder.py`, parameter `streams`, one item `"name=type:/topic[:every=N][:max=M]"` per file) writes one CSV per stream: a frame stream has **one row per sample**, a feature, a prediction, the flow and the events one row per message; floats are float32 with 9 digits. Every row carries the **header stamp**, which is how MATLAB pairs a message with its frame.
* **MATLAB**: each stage is checked **on its own**, from what ROS 2 published for the stage before, because a rounding of a few ULP of an input is amplified by the `ln` of a power. The filters use the native functions of MATLAB, so the check does not depend on how ROS 2 designs its own.
* **Tolerances** are in ULP of float32 at the largest value: 4 for a single filter, 8 for the DC and chains, 4 for a feature or prediction, 0 where nothing is computed.


## The models of the decoder tests

| Model | Where | Made by |
|---|---|---|
| QDA (3 PSD features, split of the signal on FC3 @ 12 Hz): not a motor-imagery classifier | `data/models/qda_psd/` | made earlier |
| LDA on the PSD (40 features, Fisher selection), TEST model | `data/models/lda_psd/` | `data/models/make_test_models.py` (mi_training, the 20 trials of `data/test.gdf`) |
| Gaussian (BOTH_HANDS / BOTH_FEET) | `data/models/gaussian/` | the Matlab SMR Gaussian classifier converted to `.r2nd` (`.smr.mat` is the original) |
| Gaussian with 4 classes (769, 770, 771, 773), FICTITIOUS: shows the 4 bars | `data/models/gaussian_4class/` | made up |
| LDA on FBCSP: 9 bands 4-40 Hz, 6 components, LDA on 8 selected features, classes 769 / 770, trained on real calibration runs | `data/models/fbcsp_lda/`, a copy of `mi_training/models/fbcsp` (`lda_weights.yaml`: the numbers for MATLAB, made by `data/models/export_lda_weights.py`) | mi_training |
| ShallowNet (braindecode ShallowFBCSPNet) | `ros2neuro_decoder_braindecode/extra/eegnet_mi_bhbf/` | trained with mi_training |

The test models are trained on a handful of trials: **their accuracy means nothing**, they are there to show that ROS 2 and MATLAB give the same probabilities. `test_mi.gdf` (channels FZ, FC1, ... CP4) is for ShallowNet; the others use `test.gdf` (Fz, FC3, ... CP4).


## Known issues the tests show

* **Trigger channel** (`check_acquisition`, line `KNOWN`): the GDF has a trigger channel that is all 0; the acquisition publishes -2147483648 for every sample (`XDFDevice` converts the float trigger channel of this GDF to int32 wrongly). The EEG is exact. It is a KNOWN line, not a failure; when it is fixed the line becomes PASS.
* **The deep network cannot be redone with the `r2n` functions**: MATLAB checks the filter, the 512-sample window the network reads and the session; the network is checked in Python against PyTorch / braindecode.
* **Found and fixed by these tests**: `ros2neuro_decoder` did not know `NeuroFeature::TYPE_MATRIX` in the `input.type` of a manifest, so the scikit-learn decoder could not load an FBCSP model in the real node (`DecoderManifest.cpp`).
* `filter_chain_node` declares `input_topic` and `output_topic` twice: `-p input_topic:=...` crashes it. The launchers remap the topics instead.


