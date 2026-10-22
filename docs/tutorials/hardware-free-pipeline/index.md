# Running the whole pipeline without hardware

In this tutorial you start a complete ROS2neuro pipeline on your computer, from the acquisition to the feedback
the subject would see, **without an amplifier**. The EEG comes from a GDF file that is replayed as if it were
live. You will run a calibration, look at what each node publishes, and see where each piece of the
[architecture](../../concepts/architecture.md) lives.

It takes about 10 minutes and needs no code. It is also the quickest way to check that your installation works.

**You need** ROS2neuro [installed](../../installation.md) (from apt, or built in a workspace) with the package [`ros2neuro_devel_test`](../../packages/devel-test.md), and a display for the
feedback window.

## 1. What will run

The launcher starts one node per stage of the chain:

```mermaid
flowchart LR
    ACQ["acquisition<br/>XDFDevice (GDF replay)"] --> FIL["filters<br/>Laplacian"]
    FIL --> WEL["welch<br/>PSD 4:2:48 Hz"]
    WEL --> DEC["decoder<br/>Gaussian"]
    DEC --> INT["integrator<br/>Exponential"]
    INT --> MAN["manager<br/>Training plugin"]
    MAN --> FB["feedback<br/>Bar plugin"]
    MAN -.->|"events"| REC["recorder<br/>(optional)"]
```

| Node | Package | Plugin or model |
|---|---|---|
| `acquisition` | [`ros2neuro_acquisition`](../../packages/acquisition/index.md) | [`ros2neuro::acquisition::XDFDevice`](../../packages/acquisition/xdf.md), replays `test.gdf` in a loop at 16 frames per second |
| `filters` | [`ros2neuro_filters`](../../packages/filters/index.md) | Laplacian spatial filter |
| `welch` | [`ros2neuro_processing_spectral`](../../packages/processing/spectral.md) | power spectral density, 4 to 48 Hz in steps of 2 |
| `decoder` | [`ros2neuro_decoder`](../../packages/decoder/index.md) | [`ros2neuro::decoder::Gaussian`](../../packages/decoder/gaussian.md), model `b4_bhbf_20230706.smr` (both hands / both feet) |
| `integrator` | [`ros2neuro_integrator`](../../packages/integrator/index.md) | [`ros2neuro::integrator::Exponential`](../../packages/integrator/exponential.md), `alpha 0.98` |
| `manager` | [`ros2neuro_manager`](../../packages/manager/index.md) | [`ros2neuro::manager::Training`](../../packages/manager/synchronous.md) |
| `feedback` | [`ros2neuro_feedback`](../../packages/feedback/index.md) | [`ros2neuro::feedback::Bar`](../../packages/feedback/bar.md), one bar per class |
| `recorder` | [`ros2neuro_recorder`](../../packages/recorder/index.md) | [`ros2neuro::recorder::XDFRecorder`](../../packages/recorder/xdf.md), writes GDF (skipped with `record:=false`) |

!!! note "The `welch` node depends on the decoder"
    This pipeline uses a classic decoder (Gaussian), which reads a power spectrum, so a Welch node sits between the filters and
    the decoder. The launchers `eegnet_bars` and `eegnet_wheel` use a deep-learning decoder instead, which reads a window of
    the signal: there the `welch` node is replaced by a `buffer` node. See [Processing](../../packages/processing/index.md).

## 2. Launch it

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 launch ros2neuro_devel_test gaussian_bars.launch.xml protocol:=calibration record:=false
```

The arguments:

| Argument | Values | Meaning |
|---|---|---|
| `protocol` | `calibration`, `evaluation`, `control` | which [protocol](../../concepts/protocols.md) the manager runs (default `evaluation`) |
| `record` | `true`, `false` | write the session to a GDF file (default `true`) |
| `integrator` | `exponential`, `buffer` | which integrator plugin (default `exponential`) |
| `gdf_file` | path | which file to replay |

A window with two bars opens. The log shows each node loading its plugin:

```text
[acquisition]: Loaded plugin 'ros2neuro::acquisition::XDFDevice'
[manager]: Layout: protocol classes [BOTH_HANDS (773), BOTH_FEET (771)], output classes [...], rest_mode=none, K=2
[decoder]:   Decoder configured. input='/features' output='~/prediction' type='ros2neuro::decoder::Gaussian'
[manager]: Training (calibration): 6 trials
[manager]: Trial 1/6 (class: BOTH_FEET (771) | duration: 5366 ms)
```

In a **calibration** the manager drives the bars with an autopilot (the target class rises towards its
threshold), as the subject would do when training a classifier. In an **evaluation** the bars follow the real
output of the classifier, and in **control** the manager resets the integrator when a class reaches its
threshold. Try the three:

```bash
ros2 launch ros2neuro_devel_test gaussian_bars.launch.xml protocol:=evaluation record:=false
ros2 launch ros2neuro_devel_test gaussian_bars.launch.xml protocol:=control record:=false
```

!!! note "Calibration and evaluation on a replayed file"
    The GDF is not synchronised with the cues, so the hits and misses of an evaluation only show that the chain
    works, not that the classifier is good.

The session ends by itself when the protocol ends: the manager is started with `on_exit="shutdown"`. Close the
window with ESC to end it earlier.

## 3. Look inside

Open a second terminal, source the workspace and inspect the running graph.

**The nodes**

```bash
ros2 node list
```

```text
/acquisition
/decoder
/feedback
/filters
/integrator
/manager
/welch
```

**The topics and their types**

```bash
ros2 topic list -t
```

```text
/acquisition/neurodata          [ros2neuro_msgs/msg/NeuroFrame]
/acquisition/neurodata_info     [ros2neuro_msgs/msg/NeuroFrameInfo]
/processing/filtered            [ros2neuro_msgs/msg/NeuroFrame]
/processing/psd                 [ros2neuro_msgs/msg/NeuroFeature]
/classification/prediction      [ros2neuro_msgs/msg/NeuroPrediction]
/integrated/raw                 [ros2neuro_msgs/msg/NeuroControl]
/manager_control/probabilities  [ros2neuro_msgs/msg/NeuroControl]
/neuroevent                     [ros2neuro_msgs/msg/NeuroEvent]
```

Each one is a stage of the chain of [Topics and services](../../concepts/topics.md). Follow the data from the
acquisition to the feedback:

```bash
ros2 topic hz /acquisition/neurodata                        # 16 Hz: the frame rate
ros2 topic echo /processing/psd --field shape --once       # the shape of the PSD feature
ros2 topic echo /classification/prediction --field values  # decoder output, per class
ros2 topic echo /integrated/raw --field values             # after the integrator
ros2 topic echo /manager_control/probabilities             # what the feedback draws
```

**The events**

```bash
ros2 topic echo /neuroevent --field event_id
```

During a calibration trial you see the sequence of the [protocol](../../concepts/protocols.md#event-codes):

```text
1        Start
786      Fixation
773      cue of the class (here BOTH_HANDS)
781      CFeedback: the continuous feedback starts
897      Hit
```

each followed by its *Off* (the same id plus 32768: `32769`, `33554`, `33541`, `33549`, `33665`). These are the events
the recorder writes in the GDF file next to the signal.

!!! warning "Check shape and axes"
    Print the `shape` and `axes` of the PSD feature before you use it in your own node. The order of the axes
    (channels and frequency) depends on the node and its configuration. See [Messages](../../concepts/messages.md#neurofeature).

## 4. Where the parameters are

Everything is in `ros2neuro_devel_test/launch/gaussian/config/`:

| File | Configures |
|---|---|
| `pipeline.yaml` | acquisition, filters, welch, decoder (the processing chain) |
| `integrator_exponential.yaml`, `integrator_buffer.yaml` | the integrator |
| `layout.yaml` | `classes`, `rest_mode`, `thresholds`: loaded by the manager **and** the feedback |
| `manager_calibration.yaml`, `manager_evaluation.yaml`, `manager_control.yaml` | the protocol: trials, durations |
| `feedback_bars.yaml`, `feedback_wheel.yaml` | the drawing |
| `recorder.yaml` | where and how to record |

Try changing something. For example, in `layout.yaml` change `thresholds: [0.7, 0.7]` to `[0.9, 0.9]` and in
`manager_calibration.yaml` change `trials`. After editing, rebuild the package, because the launch files use the
installed copies:

```bash
colcon build --packages-select ros2neuro_devel_test
source install/setup.bash
```

## 5. Other launchers

| Launcher | What it shows |
|---|---|
| `gaussian_wheel.launch.xml` | the same pipeline with the wheel (exactly two classes) |
| `qda_bars.launch.xml`, `qda_wheel.launch.xml` | a QDA decoder instead of the Gaussian |
| `gaussian_rest_bars.launch.xml` | classes plus the rest (783), `rest_mode: timeout` |
| `gaussian_4class_bars.launch.xml` | four bars with different thresholds |
| `qda_custom_codes_bars.launch.xml` | free class codes (501 and 502) |

The full list and the rules for the layout are in [`ros2neuro_devel_test`](../../packages/devel-test.md).

## 6. Record a session

With `record:=true` (the default) the recorder writes a GDF file with the EEG and the events when the session
ends, in `recordings_dir` (by default `src/ros2neuro_devel_test/recordings/` of the workspace):

```bash
ros2 launch ros2neuro_devel_test gaussian_bars.launch.xml protocol:=calibration recordings_dir:=/tmp/recordings
```

The file can be replayed with the same `XDFDevice`, which closes the loop: a recording of a real session is the
input of the next hardware-free test.

## What you learned

- every stage is a node, and the stages are chained only by topics;
- the plugin of each stage is selected by a parameter in a YAML file;
- the manager adds the protocol on top of the signal chain and publishes the events;
- you can replace the amplifier with a file, and nothing else changes.

Next: [Looking at the signals with the visualizer](../visualizer/index.md).
