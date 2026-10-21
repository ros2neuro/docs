# Hardware-free test launchers

!!! info ""
    Package: [`ros2neuro_devel_test`](https://github.com/ros2neuro/ros2neuro_devel_test) · part of [Packages](index.md)

Development package to try an end-to-end motor-imagery `ros2neuro` pipeline. It contains only launch files, YAML
parameter files and example decoder models, no code.

It has two parts: the **`mi_loop`** launcher, which needs hardware, and the **hardware-free launchers** that
replay a GDF file (described in the next section, and the ones to use for the tutorials).

## `mi_loop`: the pipeline with an ANT Neuro amplifier

The pipeline uses:

- acquisition from an ANT Neuro eego amplifier, through [`ros2neuro_acquisition_antneuro`](acquisition/antneuro.md);
- a file recorder, `XDFRecorder`;
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
gaussian and qda decoders. These launchers live in `launch/<folder>/` next to `mi_loop`: launch files (`.xml`), their yaml parameter files and the decoder models
(`manifest.yaml` + `.r2nd`): no scripts, no code. Every launcher starts **every node explicitly**:

```
acquisition -> filters -> welch -> decoder -> integrator -> manager -> feedback (wheel | bars)      (+ recorder)
```

## Layout

```
launch/
  gaussian/            gaussian_wheel.launch.xml   gaussian_bars.launch.xml
    config/            pipeline.yaml  layout.yaml  manager_calibration.yaml  manager_evaluation.yaml  manager_control.yaml
                       feedback_wheel.yaml  feedback_bars.yaml  recorder.yaml
    (no model/)        uses extra/b4_bhbf_20230706.smr/               (BOTH_HANDS / BOTH_FEET)
  qda/                 qda_wheel.launch.xml        qda_bars.launch.xml
    config/            (same files)
    model/             manifest.yaml  qda_test_gdf.r2nd
  qda_custom_codes/    qda_custom_codes_wheel.launch.xml   qda_custom_codes_bars.launch.xml   (classes 501 / 502, only config/layout.yaml)
  gaussian_rest/       gaussian_rest_wheel.launch.xml   gaussian_rest_bars.launch.xml   (classes 773 / 771 + REST 783, rest_mode timeout; only layout.yaml + manager_*.yaml)
  gaussian_4class/     gaussian_4class_bars.launch.xml        (4 bars, a different threshold each)
    config/            (same files, no wheel)
    model/             manifest.yaml  fake_4class_gaussian.r2nd
```

`ros2 launch` finds a launch file by its name, wherever it is in the package, so the names are unique
(`ros2 launch ros2neuro_devel_test gaussian_wheel.launch.xml`). Nothing to source but the workspace:

```bash
distrobox enter ros2neuro
cd ~/ros2neuro_ws && colcon build --packages-select ros2neuro_devel_test     # once, and after editing any file here
source /opt/ros/<distro>/setup.bash && source install/setup.bash
```

## Launching

Arguments of every launcher: `protocol` (`calibration` | `evaluation` | `control`, default `evaluation`), `gdf_file` (default
`ros2neuro_devel_test/extra/test.gdf`), `record` (default `true`: writes a GDF in `recordings_dir` (default `src/ros2neuro_devel_test/recordings/` of the workspace, derived from the install prefix) when the session ends; `record:=false` skips it).

```bash
ros2 launch ros2neuro_devel_test gaussian_wheel.launch.xml protocol:=calibration
ros2 launch ros2neuro_devel_test gaussian_bars.launch.xml  protocol:=evaluation
ros2 launch ros2neuro_devel_test qda_wheel.launch.xml      protocol:=control
ros2 launch ros2neuro_devel_test qda_bars.launch.xml       protocol:=evaluation record:=false
ros2 launch ros2neuro_devel_test gaussian_4class_bars.launch.xml protocol:=control
ros2 launch ros2neuro_devel_test gaussian_rest_wheel.launch.xml protocol:=evaluation   # with the REST (rest_timeout 6 s in manager_evaluation.yaml)
ros2 launch ros2neuro_devel_test gaussian_rest_bars.launch.xml  protocol:=calibration
ros2 launch ros2neuro_devel_test qda_custom_codes_wheel.launch.xml protocol:=evaluation   # classes 501 / 502 instead of 773 / 771
```

| protocol | manager plugin | what drives the feedback |
|---|---|---|
| `calibration` | `Training` | the autopilot (the classifier runs but is not read) |
| `evaluation` | `Training` | the real classifier output |
| `control` | `Control` | the real classifier output; the manager resets the integrator when a class reaches its threshold |

The manager is started with `on_exit="shutdown"`: when the protocol ends (or, in control, if the integrator's reset message does
not arrive within 1 s) the whole session ends. Remove the attribute in the launch file to keep the other nodes up.

## The yaml files (`<folder>/config/`)

| file | node(s) | what |
|---|---|---|
| `pipeline.yaml` | acquisition, filters, welch, decoder, integrator | the processing chain (framerate, Laplacian, PSD 4:2:48 Hz, integrator `alpha` / `rejection` / `reset_event`). Two values come from the launcher: the GDF file and the model manifest |
| `layout.yaml` | manager **and** feedback (key `/**`) | `classes`, `rest_mode`, `thresholds` (+ `input_fields`, read by the manager only), declared once so both build the same layout |
| `manager_<protocol>.yaml` | manager | plugin, topics, durations, number of `trials`; the evaluation one documents `rest_timeout` |
| `feedback_wheel.yaml` / `feedback_bars.yaml` | feedback | plugin, fps, window title, topics |
| `recorder.yaml` | recorder | output folder, subject, GDF type |

Edit them and relaunch (rebuild `ros2neuro_devel_test` after editing: the launch files use the installed copies). Rules that bite:
- `thresholds` has one value per class **with a classifier output**, in the order of `classes`. These models have 2 outputs (4 in
  `gaussian_4class`), so a rest (783) in `classes` can only be `rest_mode: timeout` (no output, no threshold).
- With `rest_mode: timeout` an evaluation REQUIRES `rest_timeout` (seconds the rest must last without touching a threshold to be a
  Hit, independent from `duration.timeout`); a calibration does not need it. With 783 in `classes` an evaluation or control with
  `rest_mode: none` is refused. The wheel accepts exactly 2 outputs; the bars any number.
- Never write `$(var ...)` in a yaml comment: it is substituted there too.

## Other class codes

Class codes are free (any code in 1..16383 that is not an event id; only the rest, 783, is special) and the colors never depend on them: a class is
colored by its position in `classes`. To try other codes **edit `classes` in `layout.yaml`** (and the length of `trials` in the manager yaml):
- **calibration**: nothing else (the autopilot needs no classifier);
- **evaluation / control**: the model publishes ITS codes (773/771 here). Add `input_fields` to `layout.yaml`: the model code of each class, in the same
  order as `classes`, e.g. `classes: [501, 502]` + `input_fields: [773, 771]`. Without it the manager says which codes the model sends.
`launch/qda_custom_codes/` is exactly that, ready: the QDA launchers with only `config/layout.yaml` different.

## The models

- **gaussian**: the real Gaussian decoder of `ros2neuro_devel_test` (b4, 3 PSD features: FC3 @ 12 Hz, FC2 @ 12 Hz, FC2 @ 14 Hz).
- **qda**: a QDA **fitted on the PSD features of `test.gdf`** (the same 3 features and chain), classes 773 / 771 = a split of the replayed
  signal on the median of FC3 @ 12 Hz. It is not a trained motor-imagery classifier: it only exercises the QDA decoder and what follows.
- **gaussian_4class**: a **fictitious** 4-class Gaussian (LEFT_HAND, RIGHT_HAND, BOTH_FEET, BOTH_HANDS) whose prototypes sit at four
  levels of the same 3 features, so replaying the file the four outputs take turns. Only to check a feedback with several bars.

A model is a `manifest.yaml` plus a binary `.r2nd`: the manifest points to it (`decoder.path`), the weights cannot live in yaml.

## Timing check (`launch/timing_check/`)

Checks whether the durations written in the events (what the recorder puts in the GDF) match the planned ones. The manager runs a calibration with
**every duration fixed and known** (`config/manager_timing.yaml`: start, fixation, cue, boom 500 ms, iti 100 ms, continuous
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
Edit `config/layout.yaml` / `config/manager_timing.yaml` (then rebuild `ros2neuro_devel_test`) to try other classes or durations.

Result on this workspace (calibration, linear autopilot): every phase is within 1 ms of the planned value, the CF of the classes with a classifier output included
(+0.6 ms on 4000 ms). The autopilot follows the clock (one step per 10 ms elapsed, absolute tick deadlines): with
a relative `sleep` per step the CF lasted ~3 % more than planned (+130 ms on 4000), and that was the difference between the console and `h.EVENT.DUR`.
The outcome event has the same instant as CF+Off (no pause between them). Mind that `POS(next event) - POS(current)` after the boom is boom + `duration.iti`
(the ITI starts after the boom's Off), while `DUR` is the boom alone.

## Things to know
- Evaluation hit/miss on a looped GDF only shows that the chain works: the file is not synchronized with the cues.
- The integrator's reset service is `/reset` (a relative name), set in `manager_*.yaml`.
- A low threshold on the exponential integrator is crossed again a few predictions after each reset, so the control resets often.
- The feedback does not print its latency (`latency_log_period_s: 0.0` in `feedback_*.yaml`; set seconds to see `Latency stamp->draw` lines).
- Close a feedback window with ESC. Watch the events with `ros2 topic echo /neuroevent`.
- Not here yet: `lda` and `svm` folders (copy `qda/`, change the model and the decoder name).
