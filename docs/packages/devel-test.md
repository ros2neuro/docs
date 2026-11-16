# Tests of every stage

!!! info ""
    Package: [`ros2neuro_devel_test`](https://github.com/ros2neuro/ros2neuro_devel_test) · part of [Packages](index.md)

Tests of every stage of the stack, without hardware: each one replays a **GDF file** through the nodes of one stage, saves what ROS 2 computed as CSV, and a MATLAB file redoes the stage from the samples of the same GDF and compares. PASS / FAIL for every line; the check errors if one fails. The package also holds the three complete pipelines that show the feedback (wheel, 2 bars, 4 bars), the data and the models the tests use, and the MATLAB functions that redo every stage.

<!-- at-a-glance -->
| | |
|---|---|
| **Layer** | Tools |
| **Kind** | Python launchers, test data and models, MATLAB checks, and one small node (`src/topic_csv_recorder.py`) |
| **Reads** | a GDF file of `data/` (replayed by the XDF acquisition plugin) |
| **Publishes** | the pipeline of the stage under test, up to the feedback window in `feedback/` |
| **Run** | `ros2 launch ~/ros2neuro_ws/src/ros2neuro_devel_test/decoder/qda/decoder_qda.launch.py` (container), then `check_decoder_qda` in MATLAB (folder of the test) |
<!-- /at-a-glance -->

<!-- interfaces -->
## Dependencies

- **ROS 2 packages**: none to build
- **At run time**: the packages of the pipeline you launch (acquisition, filters, processing, decoder, integrator, manager, control, feedback), which `package.xml` lists as run-time dependencies
- **On the computer that runs the checks**: MATLAB (R2019b or newer) with the **Signal Processing Toolbox** (`butter`, `filter`, `hann`, ...) and [BIOSIG](https://biosig.sourceforge.net) (`sload`, to read the GDF)

## Messages and topics

Messages used:

- none: launchers, parameter files and the nodes of `src/` that only read topics (`NeuroFrame`, `NeuroFeature`, `NeuroPrediction`, `NeuroControl`, `NeuroEvent`)

<!-- /interfaces -->
## The tests

Every folder has its launcher(s) (`<name>.launch.py`), its `config/` and the MATLAB file(s) that check it (`check_*.m`):

| Folder | What it tests | Launcher | Check (MATLAB, in that folder) |
|---|---|---|---|
| `acquisition/` | the acquisition publishes the GDF exactly (every sample, 32 per frame, 16 frames/s); the manager runs 6 trials | `acquisition` | `check_acquisition` |
| `filters/single_filter/` | each filter alone: dc, hp, lp, car, laplacian, hann, hamming, blackman, flattop (nine nodes on the same frames) | `filters_single` | `check_filters_single` |
| `filters/chain/` | three chains: hp-lp, hp-lp-laplacian, and every filter together (dc, hp, lp, car, laplacian and the four windows) | `filters_chain` | `check_filters_chains` |
| `processing/welch/` `fft/` `spectrogram/` `buffer/` `fbcsp/` | the plugins of `ros2neuro_processing`, on the raw frames (`fbcsp`: four band chains, then the plugin) | `processing_<plugin>` | `check_processing_<plugin>` |
| `decoder/qda/` `lda/` `gaussian/` | the decoder on the Welch PSD | `decoder_<decoder>` | `check_decoder_<decoder>` |
| `decoder/fbcsp_lda/` | an LDA (scikit-learn plugin) on FBCSP features | `decoder_fbcsp_lda` | `check_decoder_fbcsp` |
| `decoder/shallow/` | ShallowNet (braindecode) on a window of 512 samples | `decoder_shallow` | `check_decoder_shallow` (MATLAB) + `check_decoder_shallow.py` (Python) |
| `integrator/exponential/` `buffer/` | the integrator, the reset at every CFeedback, the outcome of every trial | `integrator_<kind>` | `check_integrator_<kind>` |
| `feedback/wheel/` `bars2/` `bars4/` | the complete pipeline up to the wheel, 2 bars or 4 bars: **to be seen**, nothing is saved or checked | `feedback_<wheel\|bars2\|bars4>` | (none) |

The tests of `acquisition/`, `filters/` and `processing/` run the manager in **calibration** (no classifier is needed: the autopilot drives the feedback); those of `decoder/` and `integrator/` in **evaluation** (the classifier and the integrator decide every trial); `feedback/` takes `protocol:=calibration | evaluation | control`. The manager and the control are part of every test so that the session has a structure (events) and **ends by itself** when the trials are over: calibration 6 trials, about a minute; evaluation 8 trials, about two minutes (the first 15 s wait for the deep-learning model to load).

## Run a test

Two steps, no script. Every test folder has its launcher (`<name>.launch.py`, with the commands in its docstring) and its `check_*.m`.

```bash
# 1. in the container (docker/README.md): the session; it ends by itself when the trials are over
distrobox enter ros2neuro
cd ~/ros2neuro_ws && colcon build --packages-select ros2neuro_devel_test && source install/setup.bash   # after changing a yaml
ros2 launch ~/ros2neuro_ws/src/ros2neuro_devel_test/decoder/qda/decoder_qda.launch.py
```
```matlab
% 2. in MATLAB, in the folder of the test
cd ~/ros2neuro_ws/src/ros2neuro_devel_test/decoder/qda
check_decoder_qda
```

The launcher records the CSV in `<test folder>/runs/run_<date>/` (not pushed; `latest.txt` names the newest) and the check takes the newest, or `check_x(gdf_file, run_folder)`. Launch arguments: `gdf_file:=...`, `out:=...`; the feedback launchers also `protocol:=calibration|evaluation|control`. Nodes that listen are started first and the acquisition, manager and control after 6 s, so every node gets frame 0 (MATLAB then reproduces filters from sample 0). Two sessions at once need different `ROS_DOMAIN_ID`. The ShallowNet network is also checked in Python, in the container: `python3 decoder/shallow/check_decoder_shallow.py` (torch and braindecode). BIOSIG is looked for in `BIOSIG_PATH`, `/usr/local/share/biosig/matlab`, `~/Local/Matlab/biosig`, `~/biosig`.

## Layout

```
data/            test.gdf, test_mi.gdf; config/ (yaml shared by the tests); models/ (decoder models and the scripts that make them)
matlab/          r2n_*.m: one MATLAB function per stage (see its README)
src/             r2n_session.py (what every launcher uses), topic_csv_recorder.py (the recorder node), t_*.m (helpers of the checks)
acquisition/ filters/ processing/ decoder/ integrator/ feedback/     one folder per test: launcher, config/, check_*.m, runs/
```

## How a test is built

* **`src/r2n_session.py`** is used by every launcher: the recorder and the stage under test start first, then (after 6 s) the acquisition (XDF plugin, replay of the GDF, 16 frames/s of 32 samples), the manager and the control (a protocol; they shut the launch down when they end).
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

## What was removed

The launchers that used to be here (`gaussian_*`, `qda_*`, `eegnet_*`, `sklearn_*`, the `*_rest` and `qda_custom_codes` variants, `gaussian_4class_matlab`, `timing_check`), `mi_loop.launch.xml` (the ANT Neuro loop) and `check_evaluation.m` with its recorded example: the tests above replace them (`feedback/` has the complete pipelines, `decoder/` and `integrator/` the checks of the middle of the chain).
