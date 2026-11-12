# Hardware-free test launchers

!!! info ""
    Package: [`ros2neuro_devel_test`](https://github.com/ros2neuro/ros2neuro_devel_test) · part of [Packages](index.md)

Launch files, parameter files and example models to run the whole stack end to end. It has almost no code (only the node that saves the topics for the MATLAB check, and the check itself): `mi_loop` runs a motor-imagery loop with an ANT Neuro amplifier, and the hardware-free launchers replay a GDF file through the full chain, from the acquisition to the wheel or the bars, with the Gaussian, QDA or EEGNet decoders.

| | |
|---|---|
| **Layer** | Tools |
| **Kind** | Launchers and example assets (plus one capture script and the MATLAB check of the whole chain) |
| **Reads** | a GDF file, or an ANT Neuro amplifier for `mi_loop` |
| **Publishes** | the whole pipeline, up to the feedback window |
| **Run** | `ros2 launch ros2neuro_devel_test gaussian_bars.launch.xml protocol:=calibration`<br>`ros2 launch ros2neuro_devel_test mi_loop.launch.xml` (hardware) |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages**: none
- **At run time**: the packages of the pipeline you launch (acquisition, filters, processing, decoder, integrator, manager, feedback, recorder), which `package.xml` lists as run-time dependencies

## Messages and topics

Messages used:

- none: launchers and parameter files only

<!-- /interfaces -->
## `mi_loop`: a motor-imagery loop with an ANT Neuro amplifier

The pipeline included uses:

- acquisition from an ANT Neuro eego amplifier, through [`ros2neuro_acquisition_antneuro`](acquisition/antneuro.md);
- a recorder that writes to a file, `XDFRecorder`;
- live visualisation with [`ros2neuro_visualizer`](visualizer.md);
- a Laplacian filter;
- a PSD computed with Welch;
- a Gaussian decoder, [`ros2neuro_decoder_gaussian`](decoder/gaussian.md);
- an exponential integrator with `alpha = 0.98` and `rejection = 0.55`.

Main launch file: `launch/mi_loop.launch.xml`. Configuration: `config/mi_loop_configuration.yaml`. Example decoder:
`extra/b4_bhbf_20230706.smr/manifest.yaml` and `extra/b4_bhbf_20230706.smr/b4_bhbf_20230706.smr.r2nd`.

```bash
ros2 launch ros2neuro_devel_test mi_loop.launch.xml
```

Tool to convert a Matlab decoder:

```bash
ros2 run ros2neuro_decoder_converters r2n_decoder_converter
```

Notes:

- the parameters of the nodes are in `config/mi_loop_configuration.yaml`;
- the decoder manifest is passed with the launch argument `decoder_manifest`;
- the Laplacian configuration assumes a standard 16-channel EEG layout: if your file uses another order, adapt
  `config/mi_loop_configuration.yaml`.

## Whole-chain tests without hardware (GDF replay)

Hardware-free launchers to test the whole chain, **from the acquisition of a GDF file to the wheel or the bars**, with the
Gaussian, QDA and EEGNet (deep-learning) decoders. These launchers live in `launch/<folder>/` next to `mi_loop`: launch files (`.xml`), their yaml parameter files and the decoder models
(`manifest.yaml` + `.r2nd`). The only code is the node that saves the topics as CSV for the MATLAB check (`scripts/topic_csv_recorder.py`) and the MATLAB check itself (`matlab/`). Every launcher starts **every node explicitly**:

```
acquisition -> filters -> welch -> decoder -> integrator -> control (plugin Feedback) -> feedback (wheel | bars)      (+ recorder)
                                                               ^   |
                                           manager (trials) <--+---+--> /neuroevent
```

The **control** node ([`ros2neuro_control`](control/index.md) with the plugin [`ros2neuro_control_feedback`](control/feedback.md)) reads the integrator, knows the thresholds and
builds the flow of the feedback; the **manager** runs the trials of a calibration / evaluation and writes the phases on the event bus
(`/neuroevent`). They talk through the bus: the manager writes Start, Fixation, cue and CFeedback; control hears them, drives the feedback
and writes the outcome (Hit / Miss / Timeout), which the manager hears to close the trial.

With a classic decoder (Gaussian, QDA) the processing between the filters and the decoder is a `welch_node`; with the EEGNet decoder
it is a `buffer_node` (a window of the signal) and the decoder is the Python one ([`ros2neuro_decoder_py`](decoder/python.md)).

## Layout

```
scripts/               topic_csv_recorder.py   (saves the topics of the chain as CSV, for the MATLAB check)
matlab/                check_evaluation.m (whole chain), check_functions.m (every stage), r2n/ (one function per stage), README.md   (data/ and results/ are not pushed)
launch/
  gaussian/            gaussian_wheel.launch.xml   gaussian_bars.launch.xml
    config/            pipeline.yaml  layout.yaml  protocol_calibration.yaml  protocol_evaluation.yaml  protocol_control.yaml
                       integrator_exponential.yaml  integrator_buffer.yaml  feedback_wheel.yaml  feedback_bars.yaml  recorder.yaml
    (no model/)        uses extra/b4_bhbf_20230706.smr/               (BOTH_HANDS / BOTH_FEET)
  qda/                 qda_wheel.launch.xml        qda_bars.launch.xml
    config/            (same files, no integrator_*.yaml)
    model/             manifest.yaml  qda_test_gdf.r2nd
  qda_custom_codes/    qda_custom_codes_wheel.launch.xml   qda_custom_codes_bars.launch.xml   (classes 501 / 502, only config/layout.yaml)
  gaussian_rest/       gaussian_rest_wheel.launch.xml   gaussian_rest_bars.launch.xml   (classes 773 / 771 + REST 783, rest_mode timeout; only layout.yaml + protocol_*.yaml)
  gaussian_4class/     gaussian_4class_bars.launch.xml        (4 bars, a different threshold each)
                       gaussian_4class_matlab.launch.xml      (the same in evaluation, with a GDF and a CSV of every topic: for matlab/check_evaluation.m)
    config/            (same files, no wheel; matlab_trials.yaml: the 8 trials of the MATLAB run)
    model/             manifest.yaml  fake_4class_gaussian.r2nd
  gaussian_4class_rest/  gaussian_4class_rest_bars.launch.xml   (the 4-class launcher with the REST, rest_mode timeout; only layout.yaml + protocol_*.yaml)
  eegnet/              eegnet_wheel.launch.xml   eegnet_bars.launch.xml   (deep-learning model, braindecode plugin or Python node, buffer_node instead of welch)
  eegnet_rest/         eegnet_rest_wheel.launch.xml   eegnet_rest_bars.launch.xml   (the EEGNet launchers with the REST)
  sklearn/             sklearn_wheel.launch.xml   sklearn_bars.launch.xml   (scikit-learn plugin, the Laplacian + Welch chain of gaussian)
  sklearn_4class/      sklearn_4class_bars.launch.xml   (scikit-learn plugin, fictitious 4-class model, 4 bars)
  timing_check/        timing_check.launch.py   (see below)
```

`ros2 launch` finds a launch file by its name, wherever it is in the package, so the names are unique
(`ros2 launch ros2neuro_devel_test gaussian_wheel.launch.xml`). Nothing to source but the workspace:

```bash
distrobox enter ros2neuro
cd ~/ros2neuro_ws && colcon build --packages-select ros2neuro_devel_test     # once, and after editing any file here
source /opt/ros/jazzy/setup.bash && source install/setup.bash
```

## Launching

Arguments of every launcher: `protocol` (`calibration` | `evaluation` | `control`, default `evaluation`), `integrator` (`exponential` | `buffer`,
default `exponential`: loads `config/integrator_<integrator>.yaml`; not in the `qda*` launchers yet), `gdf_file` (default
`ros2neuro_devel_test/extra/test.gdf`; the `eegnet*` launchers use `ros2neuro_decoder_py/extra/test_mi.gdf` and also have `model_path` and `decoder:=plugin|python`), `record` (default `true`: writes a GDF in `recordings_dir` (default `src/ros2neuro_devel_test/recordings/` of the workspace, derived from the install prefix) when the session ends; `record:=false` skips it). `gaussian_4class_bars` also has `capture` (default `false`: `capture:=true` saves a CSV of every topic in `capture_dir`, as `gaussian_4class_matlab` does).

```bash
ros2 launch ros2neuro_devel_test gaussian_wheel.launch.xml protocol:=calibration
ros2 launch ros2neuro_devel_test gaussian_bars.launch.xml  protocol:=evaluation
ros2 launch ros2neuro_devel_test qda_wheel.launch.xml      protocol:=control
ros2 launch ros2neuro_devel_test qda_bars.launch.xml       protocol:=evaluation record:=false
ros2 launch ros2neuro_devel_test gaussian_4class_bars.launch.xml protocol:=control
ros2 launch ros2neuro_devel_test gaussian_rest_wheel.launch.xml protocol:=evaluation   # with the REST (rest_timeout in protocol_evaluation.yaml)
ros2 launch ros2neuro_devel_test gaussian_rest_bars.launch.xml  protocol:=calibration
ros2 launch ros2neuro_devel_test qda_custom_codes_wheel.launch.xml protocol:=evaluation   # classes 501 / 502 instead of 773 / 771
```

**The layout must be the same in control, the manager and the feedback.** The classes, the rest mode and the thresholds are shared parameters and every node
reads its own copy from the file it is given. The launchers with the rest (`gaussian_rest`, `gaussian_4class_rest`, `eegnet_rest`) give the layout of their
own folder (`$(var rest)/layout.yaml`) to **all three**: if the feedback got the layout without the rest it would not know it, and it would draw neither the cue (the
yellow circle) nor the yellow dot of a rest that ends without touching a threshold, with no message at all. `python3 scripts/check_launch_layouts.py` checks it
for every launcher (exit code 1 if one of them differs): run it after editing a launcher.

| protocol | manager plugin | control (plugin `Feedback`) | what drives the feedback |
|---|---|---|---|
| `calibration` | `Synchronous` | autopilot, writes Hit | the autopilot (the classifier runs but is not read) |
| `evaluation` | `Synchronous` | thresholds, writes Hit / Miss / Timeout | the real classifier output |
| `control` | `Asynchronous` (writes nothing) | forwards the values, resets the integrator at the threshold | the real classifier output |

Manager and control are started with `on_exit="shutdown"`: when the protocol ends (manager), if nobody writes the outcome of a trial
within `duration.outcome_wait`, or, in control, if the integrator's reset message does not arrive within 1 s, the whole session ends.
Remove the attribute in the launch file to keep the other nodes up.

## How to test everything, step by step

**1. Build** (in the `ros2neuro` container; the first time it takes a while):

```bash
distrobox enter ros2neuro
cd ~/ros2neuro_ws
source /opt/ros/jazzy/setup.bash
colcon build                                    # the whole workspace (or --packages-select <package>)
source install/setup.bash
```

After editing a yaml or launch file of this package: `colcon build --packages-select ros2neuro_devel_test` (delete `build/` and `install/` of the
package after removing files from it).

**2. Launch the Gaussian 4-class pipeline** and watch it (four bars, no hardware):

```bash
ros2 launch ros2neuro_devel_test gaussian_4class_bars.launch.xml protocol:=evaluation record:=false
```

What to see: Start, Fixation, a cue, the bars moving, Hit / Miss / Timeout, and at the end `Summary: hit=.. miss=.. timeout=..` in the log (the
session ends by itself). With `protocol:=calibration` an autopilot moves the bars; with `protocol:=control` there are no trials and the control log says
`Reset requested: ... reached 0.7 (threshold ...)` each time a class reaches its threshold. In a second terminal (same `source`, same `ROS_DOMAIN_ID`):

```bash
ros2 topic echo /neuroevent --field event_id                           # the phases (manager) and the outcome (control)
ros2 topic echo /control_feedback/probabilities --field header.stamp   # the flow: same stamp as the NeuroPrediction it comes from
ros2 topic echo /integrated/raw --field header.stamp                   # ... compare: they are the same
ros2 param set /control thresholds "[0.5, 0.5, 0.5, 0.5]"              # the markers of the bars move
ros2 param list /manager ; ros2 param list /control ; ros2 param list /feedback     # every node has its own parameters
```

**3. The launcher that leaves everything to check in MATLAB** (the same pipeline, in evaluation, 8 trials, about 2 minutes, it ends by itself):

```bash
ros2 launch ros2neuro_devel_test gaussian_4class_matlab.launch.xml
```

It saves a GDF (raw EEG and events) in `recordings/` and a CSV of every topic in `matlab/data/run_<date>/`. Then, in MATLAB:

```matlab
cd ~/ros2neuro_ws/src/ros2neuro_devel_test/matlab
check_evaluation
```

It loads the GDF and the yaml of the launcher, applies the filters, the decoder and the integrator (reset at every trial), draws every step
with the thresholds and the Fixation / cue / CFeedback / Hit / Miss marked, and compares with ROS 2. See `matlab/README.md` (in the package).

**4. The unit and integration tests** of the packages (no display; about 3 minutes; not at the same time as a launcher in the same ROS domain: `export ROS_DOMAIN_ID=<n>`):

```bash
colcon test --packages-select ros2neuro_control ros2neuro_manager ros2neuro_manager_synchronous ros2neuro_manager_asynchronous \
    ros2neuro_control_feedback ros2neuro_feedback ros2neuro_feedback_wheel ros2neuro_feedback_bar ros2neuro_integrator
colcon test-result --verbose            # every package with 0 failures
```

**5. The other launchers** (`gaussian_*`, `qda_*`, `eegnet_*`, with the rest, with other class codes) are the same pipeline with another model or other classes:
launch each one with each protocol (`protocol:=calibration | evaluation | control`, `record:=false`) and look for the same things.

## Check an evaluation in MATLAB (`matlab/`)

`gaussian_4class_matlab.launch.xml` records an evaluation of the 4-class pipeline (a GDF with the raw EEG and the events, and a CSV of every topic written by
`scripts/topic_csv_recorder.py`), and **`matlab/check_evaluation.m` redoes it in MATLAB** (with the functions of `matlab/r2n/`): it loads the GDF and the yaml used by the launcher,
applies the Laplacian, the Welch PSD, the Gaussian decoder and the exponential integrator with the reset at the start of every trial, recomputes the outcome of
every trial and compares every step with what ROS 2 published. Four figures, ROS 2 against MATLAB, each with Start, Fixation, cue, CFeedback and Hit / Miss / Timeout marked:
filters (C3 and C4: raw, filtered by ROS 2 and by MATLAB, their difference), the features of `/processing/psd`, the classification, the integration with the thresholds.

On the reference run (8 trials) all the outcomes recomputed from the integrated values are the ones of ROS 2 (8 of 8), the Laplacian and the Welch PSD are identical to ROS 2, the
probabilities differ by 1e-7 and the integrator by 1e-7 (one float32 ULP), and the 8 resets are the ones ROS 2 made (usually at the frame the rule gives, now and then one frame earlier because the events and the values travel on different topics). The CSV and the results are **not pushed** (`.gitignore`).
The stages are also available one by one, as functions you can copy (`matlab/r2n/`), with `matlab/check_functions.m` that checks all of them against ROS 2:
see [Reproducibility in MATLAB](../reproducibility/matlab.md).
What it does, how to run it and the things to know about the reset: `matlab/README.md` (in the package).

## The yaml files (`<folder>/config/`)

| file | node(s) | what |
|---|---|---|
| `pipeline.yaml` | acquisition, filters, welch, decoder, integrator | the processing chain (framerate, Laplacian, PSD 4:2:48 Hz). Two values come from the launcher: the GDF file and the model manifest |
| `integrator_<name>.yaml` | integrator | plugin and parameters of the integrator chosen with `integrator:=` (`alpha` / `rejection` / `reset_event` for the exponential one); in `qda/` the integrator is still in `pipeline.yaml` |
| `layout.yaml` | every node that needs it (`/**`) and `/control` | `/**`: `classes`, `rest_mode`, `thresholds`, the same for the manager, control and the feedback, which **all load this file** (nobody asks anybody). `/control`: `input_fields` (control's, when present) |
| `protocol_<protocol>.yaml` | `/manager` and `/control` | two sections in one file. `/manager`: plugin, durations of the trials, number of `trials`, `outcome_wait`. `/control`: plugin `Feedback`, `protocol`, topics, the length of the continuous feedback (`feedback_min/max`, `timeout`: control's own parameters); the evaluation one documents `rest_timeout` |
| `feedback_wheel.yaml` / `feedback_bars.yaml` | feedback | plugin, fps, window title, topics (the layout comes from `layout.yaml`) |
| `recorder.yaml` | recorder | output folder, subject, GDF type |

Edit them and relaunch (rebuild `ros2neuro_devel_test` after editing: the launch files use the installed copies). The thresholds can also be changed
**while running**, and the markers of the feedback follow: `ros2 param set /control thresholds "[0.8, 0.8]"`. Rules that bite:
- `thresholds` has one value per class **with a classifier output**, in the order of `classes`. These models have 2 outputs (4 in
  `gaussian_4class`), so a rest (783) in `classes` can only be `rest_mode: timeout` (no output, no threshold).
- With `rest_mode: timeout` an evaluation REQUIRES `rest_timeout` (seconds the rest must last without touching a threshold to be a
  Hit, independent from `duration.timeout`); a calibration does not need it. With 783 in `classes` an evaluation or control with
  `rest_mode: none` is refused. The wheel accepts exactly 2 outputs; the bars any number.
- Never write `$(var ...)` in a yaml comment: it is substituted there too.

## Other class codes

Class codes are free (any code in 1..16383 that is not an event id; only the rest, 783, is special) and the colors never depend on them: a class is
colored by its position in `classes`. To try other codes **edit `classes` in `layout.yaml`** (and the length of `trials` in the `/manager` section of `protocol_*.yaml`):
- **calibration**: nothing else (the autopilot needs no classifier);
- **evaluation / control**: the model publishes ITS codes (773/771 here). Add `input_fields` to `layout.yaml`: the model code of each class, in the same
  order as `classes`, e.g. `classes: [501, 502]` + `input_fields: [773, 771]`. Without it control says which codes the model sends.
`launch/qda_custom_codes/` is exactly that, ready: the QDA launchers with only `config/layout.yaml` different.

## The models

- **gaussian**: the real Gaussian decoder of `ros2neuro_devel_test` (b4, 3 PSD features: FC3 @ 12 Hz, FC2 @ 12 Hz, FC2 @ 14 Hz).
- **qda**: a QDA **fitted on the PSD features of `test.gdf`** (the same 3 features and chain), classes 773 / 771 = a split of the replayed
  signal on the median of FC3 @ 12 Hz. It is not a trained motor-imagery classifier: it only exercises the QDA decoder and what follows.
- **gaussian_4class**: a **fictitious** 4-class Gaussian (LEFT_HAND, RIGHT_HAND, BOTH_FEET, BOTH_HANDS) whose prototypes sit at four
  levels of the same 3 features, so replaying the file the four outputs take turns. Only to check a feedback with several bars.

- **sklearn**, **sklearn_4class**: the chain of gaussian (Laplacian, Welch) with the plugin `ros2neuro::decoder::Sklearn`, configured like
  every decoder (`decoder.manifest` in `pipeline.yaml`). The models are MADE UP, written by `scripts/make_sklearn_models.py` from the PSD of
  `test.gdf` (needs mne, scikit-learn, skops): `sklearn/model` is StandardScaler + LogisticRegression on a **selection** of 6 values (C3, Cz,
  C4 at 10 and 12 Hz) of the 773 / 771 trials (checks `features.mode: selection`; thresholds 0.62, because its integrated value seldom
  reaches 0.7); `sklearn_4class/model` is a RandomForest on the whole PSD with fictitious labels (quartiles of C3 - C4 at 12 Hz) and
  `output.fields` in another order than the classes of the model (checks that the plugin follows `output.fields`).
- **eegnet**: a braindecode ShallowFBCSPNet (`extra/eegnet_mi_bhbf` of [`ros2neuro_decoder_braindecode`](decoder/braindecode.md), both hands / both feet) on its own
  recording `test_mi.gdf` (of `ros2neuro_decoder_py`), with a 4-14 Hz band-pass and a 512-sample window. `decoder:=plugin` (default) runs it in the
  C++ decoder node, configured like every decoder with `decoder.manifest` in `pipeline.yaml` (the `decoder.type` of the manifest,
  `ros2neuro::decoder::Braindecode`, picks the plugin); `decoder:=python` in the Python node of `ros2neuro_decoder_py`
  (`config/decoder_python.yaml`): same model folder, identical predictions. The model takes a while to load, so
  `duration.begin` is 15 s.

A classic model is a `manifest.yaml` plus a binary `.r2nd`: the manifest points to it (`decoder.path`), the weights cannot live in yaml.

The Welch node publishes the natural logarithm of the PSD, so every classic model here declares `unit: ln(power/Hz)` (the decoder refuses a different unit).
`b4_bhbf` is a converted Matlab SMR Gaussian classifier (reconverted with `--feature-unit "ln(power/Hz)"`). `qda_test_gdf` and `fake_4class_gaussian` were first
written for features in dB (`10*log10`): they were rescaled for `ln` with `x_dB = (10/ln 10) * x_ln` (Gaussian: centers / 4.343, covariances / 4.343²;
QDA: linear weights × 4.343, quadratic weights × 4.343², bias unchanged), which gives exactly the same probabilities as before.

## Timing check (`launch/timing_check/`)

Checks whether the durations written in the events (what the recorder puts in the GDF) match the planned ones. The manager and control run a calibration with
**every duration fixed and known** (`config/protocol_timing.yaml`: start, fixation, cue, boom 500 ms, iti 100 ms, continuous
feedback (CF, 781) exactly **4000 ms** for every trial, rest included) and `timing_monitor.py` listens to `/neuroevent` (the same stamps the recorder
uses for `POS`). When the protocol ends it prints, per trial and per phase, the measured duration, the error against the planned one and the same
duration in samples at 512 Hz, which is what `h.EVENT.DUR` gives in MATLAB (BioSig's `sopen` builds `DUR` from the On/Off pairs `TYP` / `TYP + 0x8000`:
`DUR = POS(off) - POS(on)`; the GDF itself has no DUR column). A phase is `OK` if it is within 15 ms (one 10 ms tick + the 1/512 s quantization of `POS`).

```bash
ros2 launch ros2neuro_devel_test timing_check.launch.py                                  # no window, ~60 s: table + verdict in the console
ros2 launch ros2neuro_devel_test timing_check.launch.py feedback:=wheel                  # with the wheel (or feedback:=bars)
ros2 launch ros2neuro_devel_test timing_check.launch.py feedback:=wheel record:=true     # also leaves a GDF in recordings_dir to load with sload
```
A `FAIL` verdict makes the monitor exit with code 1, which the launch prints as `process has died ... exit code 1`: it is the verdict, not a crash.
Edit `config/layout.yaml` / `config/protocol_timing.yaml` (then rebuild `ros2neuro_devel_test`) to try other classes or durations.

Result on this workspace (calibration, linear autopilot): every phase is within 1 ms of the planned value, the CF of the classes with a classifier output included
(+0.6 ms on 4000 ms). The autopilot follows the clock (one step per 10 ms elapsed, absolute tick deadlines): with
a relative `sleep` per step the CF lasted ~3 % more than planned (+130 ms on 4000), and that was the difference between the console and `h.EVENT.DUR`.
The end of the continuous feedback and the outcome are written by control; the manager closes the outcome after the boom. Mind that `POS(next event) - POS(current)` after the boom is boom + `duration.iti`
(the ITI starts after the boom's Off), while `DUR` is the boom alone.

## Things to know
- Evaluation hit/miss on a looped GDF only shows that the chain works: the file is not synchronized with the cues.
- The integrator's reset service is `/reset` (a relative name), set in the `/control` section of `protocol_*.yaml`.
- Hard to see in the logs but important: the feedback reads `/control_feedback/probabilities`, the flow that control builds from the integrator values (the events stay on `/neuroevent`, the feedback hears them there).
- A low threshold on the exponential integrator is crossed again a few predictions after each reset, so the control resets often.
- The feedback does not print its latency (`latency_log_period_s: 0.0` in `feedback_*.yaml`; set seconds to see `Latency stamp->draw` lines).
- Close a feedback window with ESC. Watch the events with `ros2 topic echo /neuroevent`.
- Not here yet: `lda` and `svm` folders (copy `qda/`, change the model and the decoder name).
