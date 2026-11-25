# Control feedback (Feedback)

!!! info ""
    Package: [`ros2neuro_control_feedback`](https://github.com/ros2neuro/ros2neuro_control_feedback) · pluginlib class: `ros2neuro::control::Feedback` · part of [Control](index.md)

Plugin of [`ros2neuro_control`](index.md) (pluginlib class `ros2neuro::control::Feedback`) that drives the feedback (wheel,
bars). It is the node that knows the thresholds: it reads the `NeuroPrediction` of the integrator, maps and normalizes it,
decides the outcome of a trial (Hit / Miss / Timeout) and builds the flow that [`ros2neuro_feedback`](../feedback/index.md) shows. The trials
themselves (order, Start, Fixation, cue, CFeedback) are run by the manager, which this plugin listens to. **Every parameter is the
plugin's own, nobody is asked for anything**: the `classes`, the `rest_mode`, the ids of the events (`event.*`) and the `thresholds` are the
same values that the manager and the feedback use, written once for every node (a `/**` section of the parameter file); the durations of
the continuous feedback, `rest_timeout`, `input_fields` and the topics are its own. The thresholds can be changed while running in every
protocol: the plugin puts the ones in force in the flow, so the feedback follows them.

| | |
|---|---|
| **Layer** | Control |
| **Kind** | Plugin of [`ros2neuro_control`](index.md) (pluginlib class `ros2neuro::control::Feedback`) |
| **Reads** | `NeuroPrediction` (through the control node, `input_topic`), `/neuroevent` (`NeuroEvent`, `event_topic`) |
| **Publishes** | `/control_feedback/probabilities` (`NeuroControl`, `control_topic`: the flow of the feedback: values and thresholds, with the header of the `NeuroPrediction`), `/neuroevent` (the end of the continuous feedback and the outcome: Hit / Miss / Timeout) |
| **Calls** | service `/reset` (`std_srvs/Empty`) of the integrator, through the control node |
| **Run** | `ros2 launch ros2neuro_control_feedback control_feedback.launch.xml protocol:=evaluation` |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, `std_msgs`, `std_srvs`, [`ros2neuro_control`](index.md), [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)
- **At run time** (to see something): [`ros2neuro_feedback`](../feedback/index.md) with a drawing plugin, [`ros2neuro_manager`](../manager/index.md) with [`ros2neuro_manager_synchronous`](../manager/synchronous.md) for calibration / evaluation

## Messages and topics

The topics belong to the control node (the integrator input) and to the plugin (the rest).

| | Default topic | Type | Changed by |
|---|---|---|---|
| subscribes | `/integrated/raw` | `NeuroPrediction` | `input_topic` (of the control node) |
| subscribes | `/neuroevent` | `NeuroEvent` | `event_topic` |
| publishes | `/control_feedback/probabilities` | `NeuroControl` | `control_topic` |
| publishes | `/neuroevent` | `NeuroEvent` | `event_topic` (**only** the end of the continuous feedback and 897 Hit / 898 Miss / 899 Timeout) |

| | Service | Type | Note |
|---|---|---|---|
| calls | `/reset` | `std_srvs/Empty` | `reset_service` of the control node; only in `control` |

Messages used:

- `NeuroPrediction`: read (the integrator output; its `fields` are class codes or names, the `values` are accumulators or probabilities)
- `NeuroEvent`: read (the bus) and written (only the end of the continuous feedback and the outcomes)
- `NeuroControl`: published, the flow of the feedback (the values and the thresholds, with the header of the `NeuroPrediction` they come from)

<!-- /interfaces -->
## What it does

The parameter `protocol` chooses the behavior. It is the same plugin for the three.

| `protocol` | What the feedback sees | What the plugin writes on the event bus |
|---|---|---|
| `calibration` | the **autopilot**: during the continuous feedback the target class rises from 1/K to its threshold (the rest wanders around 1/K); the integrator values are not shown | the close of the feedback and the Hit (always; the rest: Hit when its time is over) |
| `evaluation` | the **real values** of the integrator, only during the continuous feedback | the close of the feedback and Hit / Miss on the first threshold touched or Timeout when `duration.timeout` is over |
| `control` | every value of the integrator, all the time | nothing; the integrator is reset when a class reaches its threshold |

### The events

The plugin never starts a trial. It hears the bus, where the manager writes the phases, and acts on these:

| Event | What the plugin does |
|---|---|
| class code (the **cue**, 773 / 771 / ...) | remembers the class of the coming trial: the target of the autopilot, or the class that makes a Hit |
| `781` CFeedback | the continuous feedback starts: the autopilot runs, or the evaluation begins to look at the values |

When the trial is decided it writes, in this order:

1. `781 + 32768`: the **end of the continuous feedback**;
2. `897` / `898` / `899`: the **outcome**, Hit / Miss / Timeout.

The manager hears the outcome, closes it after the boom (outcome plus `32768`, the time the feedback shows it) and goes on with Start,
Fixation, cue, CFeedback of the next trial. Anything else is
refused (`FeedbackContext::emit_event` logs an error and sends nothing): Start, Fixation, the cue and the start of the continuous
feedback belong to the manager. This holds for calibration and for evaluation. `control` writes no event.

```
manager --- Start, Fixation, cue, 781 ----------------------------->  bus (/neuroevent)  --->  control_feedback
manager <-- 781+Off, 897 / 898 / 899 -------------------------------  bus  <---  control_feedback
manager --- outcome+Off (after the boom), then Start ... (next trial) --->  bus
```

### The flow of the feedback

The flow (`control_topic`, a `NeuroControl`) is **the control signal of the feedback**, built from every `NeuroPrediction` the plugin
uses:

| Field | Content |
|---|---|
| `header` | **the header of the `NeuroPrediction` it comes from** (same `stamp`, same `frame_id`): whoever follows the flow is in step with the predictions, and two outputs made from the same prediction (this flow, a command for a robot) can be paired by it |
| `fields` / `values` | the `K` class codes and their normalized values, then `K` entries `threshold:<code>` with the thresholds in force (they can change while running: the feedback moves its markers) |
| `actions` / `commands` | `seq`, a progressive counter |

The phases of the trials (Start, Fixation, cue, CFeedback, the outcome) are **not** in the flow: the feedback reads them from the event bus
`/neuroevent`, where the manager and this plugin write them. In a calibration the values are the autopilot's, not a prediction's:
the header carries the stamp of the moment (`now()`).

### Parameters of the plugin

Nothing is asked: every parameter is read from the node itself.

| Shared with the manager and the feedback (the same values, written once for every node) | |
|---|---|
| `classes`, `rest_mode` | the protocol classes, in order. The plugin builds its own layout from them: the output classes (the rest has none with `rest_mode` `timeout` / `none`), `K`, the neutral vector |
| `event.start`, `event.fixation`, `event.cfeedback`, `event.hit`, `event.miss`, `event.timeout`, `event.off`, `event.shown` | the ids of the events it listens to and writes (defaults 1, 786, 781, 897, 898, 899, 32768, 16384) |
| `thresholds` | one per output class, checked against `K`; changeable while running (`ros2 param set /control thresholds "[0.8, 0.8]"`), in every protocol; a wrong size, a value outside (0, 1] or not above 1/K (it would be met right after a reset) is refused. With the buffer integrator and a non-uniform `init_val`, keep the thresholds above it too (control does not know `init_val`) |

| Its own | |
|---|---|
| `duration.feedback_min`, `duration.feedback_max`, `duration.timeout`, `rest_timeout` | calibration and evaluation (see below) |
| `input_fields` | the codes the model publishes, in the order of the classes, when they are not the classes' |

The integrator publishes accumulators or smoothed scores, not probabilities: the plugin maps the `fields` to the classes (an integer
string is that code, otherwise a name of the catalog) and normalizes (`v_i/sum`; sum <= 0 -> uniform 1/K) before using the values. If the
configuration cannot be used (invalid ids, a rest without `rest_mode` in an evaluation or a control, thresholds of the wrong size, wrong
durations) the plugin logs the reason and does not configure: the node stops with exit code 1.

### Reset (control)

When a class reaches its threshold the plugin calls `request_reset()` of the control node. From then on nothing is forwarded or
decided until (1) the integrator has answered the reset service (it answers once it has reset) and (2) a value made from data of
after the request arrives (its `header.stamp`, the time of the data, at or after the request). The values themselves are not
looked at, so a reset to any state works (e.g. a non-uniform `init_val` of the buffer integrator). If no such value arrives within
1 s the plugin logs an **error** and stops the node with exit code 1 (the pipeline is broken).

In calibration / evaluation the integrator resets on its own on the CFeedback event (`integrator.reset_event: 781`): the plugin
drops the queued values (`flush_input()`) and, in evaluation, ignores every value stamped before the CFeedback (the state of before
the reset, possibly still on its way): only values made after the CFeedback are shown and decide the trial.

## Outcomes (`evaluate_trial`)

A class *touches* when its normalized value >= its own threshold; with several touching the highest value wins, at equal
value the lowest index (order of `output_classes`).

| target | result |
|---|---|
| class with an output | winner == target -> **Hit** (897); another winner -> **Miss** (898); time over, nobody -> **Timeout** (899), never Miss |
| rest, `rest_mode=timeout` | no threshold to reach; a winner before the end -> **Miss**; none until the end -> **Hit** |
| rest, `rest_mode=class` | a normal class with its threshold; time over -> **Timeout** |

Durations (the plugin's own parameters): calibration `duration.feedback_min..feedback_max` for every class (rest included); evaluation
`duration.timeout` for classes with an output, `rest_timeout` (seconds) for a rest in timeout. Checked at configure:
`0 < feedback_min <= feedback_max <= 600000` ms, `0 < timeout <= 600000` ms, `0 < rest_timeout <= 600` s. They must also stay below
the `duration.outcome_wait` of the manager (60 s by default), or the manager gives up before the outcome: control cannot check it
(it does not ask the manager), the manager warns when `outcome_wait` is below 30 s.

**`rest_timeout`** (seconds, in (0, 600]): **required** when an evaluation has the rest with `rest_mode=timeout` (the plugin refuses to
configure without it). It is how long the rest lasts: if no threshold is touched for that time it is a **Hit** (a threshold touched
before is a Miss). It is independent from `duration.timeout`, the maximum duration of the other trials. Not needed in a
calibration (the rest lasts `feedback_min..feedback_max` like any class) nor with `rest_mode=class`. The feedback shows the rest
Hit with a yellow arc (wheel) or a yellow dot (bars). With 783 in `classes`, an evaluation or a control must set `rest_mode` to
`timeout` or `class`, otherwise the plugin refuses to configure; a calibration does not need it.

## Calibration autopilot

Scalar `LinearPilot` / `SinePilot` + scalar -> vector expansion that sums to 1: the target rises from 1/K to its threshold, the
others share the rest. A rest in timeout oscillates around 1/K with an amplitude below (min threshold - 1/K), so it never
touches a threshold. The autopilot follows the clock: one step per 10 ms elapsed (`steps_due()`, a late tick makes up for it), so
the continuous feedback lasts the planned time. The duration of every trial is drawn at random between `duration.feedback_min`
and `duration.feedback_max` when the CFeedback event arrives.

## Parameters

| Parameter | Default | Meaning |
|---|---|---|
| `protocol` | (required) | `calibration` \| `evaluation` \| `control` |
| `thresholds` | `[0.8, 0.8]` | one per class with a classifier output, in the order of `classes`; changeable while running, in every protocol |
| `classes`, `rest_mode`, `event.*` | `[773, 771]`, `none`, the stack's ids | the protocol: the same values as the manager and the feedback |
| `duration.feedback_min`, `duration.feedback_max` | `4000`, `5500` | calibration: ms, the autopilot of every trial lasts a random time between the two (`min <= max`) |
| `duration.timeout` | `10000` | evaluation: ms of continuous feedback without touching a threshold: Timeout |
| `rest_timeout` | (none) | evaluation with `rest_mode: timeout` and a rest (783): **required**, seconds without touching a threshold to be a Hit |
| `input_fields` | (none) | model code of each class, same order as `classes`, when the model publishes other codes |
| `control_topic` | `/control_feedback/probabilities` | the flow of the feedback |
| `event_topic` | `/neuroevent` | the event bus |

`input_topic` and `reset_service` are parameters of the control node. The plugin checks the durations (`feedback_min <= feedback_max`, no
negative value, `rest_timeout` present when it is needed).

## Launch

`launch/control_feedback.launch.xml` starts the control node with this plugin and the feedback node, and gives them the shared values
(`classes`, `rest_mode`, `thresholds`) and the durations. The manager is started separately ([`ros2neuro_manager_synchronous`](../manager/synchronous.md),
[`ros2neuro_manager_asynchronous`](../manager/asynchronous.md)) with the same `classes` and `rest_mode`, or by the launchers of [`ros2neuro_devel_test`](../devel-test.md), which start the
whole chain with one `layout.yaml`.

```bash
ros2 launch ros2neuro_control_feedback control_feedback.launch.xml protocol:=calibration
ros2 launch ros2neuro_manager_synchronous synchronous.launch.xml          # the trials (give it the same classes / rest_mode)
```

## No shared code with the manager or the feedback

The layout, the catalog of the class names, the mapping of the integrator fields, the flow builder, the autopilot and the evaluation of a trial
(`trial_logic.hpp`) are this package's own. The manager and the feedback have what they need (their own, smaller): what is the manager's
(the protocol, the ids of the events) is the same **parameter** in each node, not shared in code.

## Tests

`colcon test --packages-select ros2neuro_control_feedback`

- logic without ROS: `layout`, `fields_map`, `flow` (header, values, thresholds), `reset_wait`, `trial_logic` (the outcome of a trial), `autopilot`, `asynchronous_logic` (the threshold that triggers a reset);
- `test_feedback_core`: the plugin writes only the end of the feedback and the outcome on the bus and refuses the rest (the end of the outcome is the manager's);
- `test_feedback_plugin`: the plugin loaded by the node of [`ros2neuro_control`](index.md), with a helper node that plays the integrator, the manager (events) and the feedback: the three protocols (autopilot with and without the rest, Hit / Miss / Timeout, the rest in timeout, no trial without a cue, the classes and the ids of the events as parameters, the thresholds changed while running), the flow (the header of the prediction, the thresholds in force, no phase in it, neutral first) and the configuration that is refused (a rest without `rest_mode`, wrong durations, `rest_timeout` missing);
- `test_feedback_reset_timeout`: no value after a reset -> the node stops with an error (in its own executable, because the node shuts the process down).

## MATLAB replication

The plugin in MATLAB, to replay offline what the node does online. It uses only native MATLAB functions: the first class over its threshold decides Hit or Miss (what control writes on the event bus). Each function says in its header which plugin it reproduces. It is compared with the real node by `check_integrator_exponential` in [`ros2neuro_devel_test`](../devel-test.md), which also draws MATLAB and ros2neuro on top of each other and their difference. [Download all the functions](../../reproducibility/download.md).

???+ example "r2n_threshold_winner.m"
    ```matlab
    --8<-- "files/r2n/r2n_threshold_winner.m"
    ```

Use it:

```matlab
addpath('ros2neuro_devel_test/matlab');      % or the folder of the downloaded zip
w = r2n_threshold_winner([0.7 0.7], integrated_row);   % 0 if no class is over its threshold
```
