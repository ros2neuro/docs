# Synchronous manager (Synchronous)

!!! info ""
    Package: [`ros2neuro_manager_synchronous`](https://github.com/ros2neuro/ros2neuro_manager_synchronous) · pluginlib class: `ros2neuro::manager::Synchronous` · part of [Manager](index.md)

Plugin `ros2neuro::manager::Synchronous` of [`ros2neuro_manager`](index.md): the trials of a calibration or an evaluation. It ports the logic of
`game_controller`'s `training_controller` (trial sequence, phases, `protocol_ended`, summary). The whole
protocol runs on a thread of the plugin.

It runs the **trials**; it does not decide them. During the continuous feedback [`ros2neuro_control_feedback`](../control/feedback.md) takes over (autopilot
in a calibration, thresholds in an evaluation): it closes the continuous feedback and writes the outcome on the event bus;
the plugin hears the outcome, closes it after the boom and goes on. It reads its own parameters (the durations of the trials) and the
shared ones (`classes`, `rest_mode`, the ids of the events); nobody asks it for anything, and it knows nothing of the durations of the
continuous feedback, which are control's.
Calibration and evaluation are the same thing for the manager: what changes is what `ros2neuro_control_feedback` does (its parameter
`protocol`).

| | |
|---|---|
| **Layer** | Manager (protocol) |
| **Kind** | Plugin of [`ros2neuro_manager`](index.md) (pluginlib class `ros2neuro::manager::Synchronous`) |
| **Reads** | the outcome (897 / 898 / 899) on `/neuroevent`, through the manager node |
| **Publishes** | the trial events on `/neuroevent` (through the manager node), `/protocol_ended` |
| **Run** | `ros2 launch ros2neuro_manager_synchronous synchronous.launch.xml` (together with [`ros2neuro_control_feedback`](../control/feedback.md)) |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, `std_msgs`, [`ros2neuro_manager`](index.md), [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)
- **ROS 2 packages** (run only): [`ros2neuro_control_feedback`](../control/feedback.md) (the outcomes), [`ros2neuro_feedback`](../feedback/index.md), [`ros2neuro_feedback_wheel`](../feedback/wheel.md), [`ros2neuro_feedback_bar`](../feedback/bar.md)

## Messages and topics

Default node name: `manager` (the node of [`ros2neuro_manager`](index.md)).

| | Default topic | Type | Changed by |
|---|---|---|---|
| publishes | `/protocol_ended` | `std_msgs/Empty` (`transient_local`) | `protocol_ended_topic` |
| publishes | `/neuroevent` | `NeuroEvent` | through the manager node (`event_topic`) |
| subscribes | `/neuroevent` | `NeuroEvent` | through the manager node: the outcome of every trial |

Messages used:

- `NeuroEvent`: the phases and the end of the outcome (published), the outcome (read), through the manager node
- `std_msgs/Empty`: the end of the protocol

## Example configuration

The evaluation protocol of the Gaussian pipeline of [`ros2neuro_devel_test`](../devel-test.md) (`config/protocol_evaluation.yaml`, `/manager` part; the
`/control` part is for [`ros2neuro_control_feedback`](../control/feedback.md); the layout is in `layout.yaml`):

```yaml
/manager:
    ros__parameters:
        plugin: ros2neuro::manager::Synchronous
        event_topic: /neuroevent
        trials: [3, 3]                  # one value per class of `classes`, in the same order
        protocol_ended_topic: /protocol_ended
        shutdown_on_end: true
        # durations in ms
        duration.begin: 3000                  # wait before the first trial
        duration.start: 1000
        duration.fixation: 2000
        duration.cue: 1000
        duration.boom: 1000                      # ms the outcome is shown: from the outcome to its end (the manager closes it)
        duration.iti: 100
        duration.end: 2000
        # longest wait for the outcome after CFeedback: nothing -> the pipeline is broken
        duration.outcome_wait: 60000
```

<!-- /interfaces -->
## Per trial

```
wait duration.begin (the first time)
Start -> Fixation -> cue (class code) -> CFeedback -> [ control_feedback: CFeedback+Off, Hit / Miss / Timeout ]
      -> [boom] -> outcome+Off -> [iti] -> next trial
```

Start, Fixation and the cue are followed by their `+Off`. After `CFeedback` the manager writes nothing until the trial is closed:
[`ros2neuro_control_feedback`](../control/feedback.md) decides the trial, closes the continuous feedback (`CFeedback+Off`),
and writes the outcome. The manager waits for it, closes it after `duration.boom` (`outcome+Off`), then the ITI and the next trial.
In the GDF `DUR(781)` is `POS(781+Off) - POS(781)` and `DUR(outcome)` is the boom.

**Order of the trials.** For every class of `classes`, `trials[i]` trials; the whole sequence is shuffled (random order), the same way in
calibration and in evaluation. The length of the continuous feedback of each trial is not decided here: in a calibration it is random
between `duration.feedback_min` and `duration.feedback_max` of [`ros2neuro_control_feedback`](../control/feedback.md), in an evaluation it is its `duration.timeout`
(they are control's own parameters: the manager does not know them).

**Start of the protocol.** The plugin waits `duration.begin` ms before the first trial (set it long enough for the pipeline to be
up: the DL decoders take a while to load).

**No outcome.** If the outcome does not arrive within `duration.outcome_wait` ms of CFeedback (is [`ros2neuro_control_feedback`](../control/feedback.md) running
and reading the integrator?) the manager logs an **error** and stops with exit code 1 (`on_exit="shutdown"` ends the whole launch).

**End.** After the last trial and `duration.end` the plugin publishes `/protocol_ended` (latched), prints
`Summary: hit=.. miss=.. timeout=.. accuracy=..%` (counted from the outcomes it heard) and, with `shutdown_on_end`, stops the node.

## Parameters (declared on the manager node)

`trials` (same length as `classes`; error otherwise), `duration.{begin,start,fixation,cue,boom,iti,end}` (ms, not negative; `boom` is how long the outcome is shown, then the manager closes it),
`duration.outcome_wait` (ms, > 0, default 60000), `protocol_ended_topic` (`/protocol_ended`, transient_local), `shutdown_on_end` (true).
`classes` and `rest_mode` come from the core (the same values as in [`ros2neuro_control_feedback`](../control/feedback.md) and the feedback: write them once, in a
`/**` section). The manager does not know the durations of the continuous feedback (`duration.feedback_min` / `feedback_max` /
`timeout`, `rest_timeout`): they are parameters of `ros2neuro_control_feedback`.

## Launch

```bash
ros2 launch ros2neuro_manager_synchronous synchronous.launch.xml classes:="[773, 771, 783]" rest_mode:=timeout \
    trials:="[10, 10, 5]" begin:=5000
ros2 launch ros2neuro_control_feedback control_feedback.launch.xml protocol:=evaluation classes:="[773, 771, 783]" rest_mode:=timeout rest_timeout:=2.0
```

The launch declares `classes/rest_mode` for the manager: pass the same values to `control_feedback.launch.xml`. The
launchers of [`ros2neuro_devel_test`](../devel-test.md) start the whole chain with one layout file (a `/**` section that every node loads).

## Differences from the old controller

* Thresholds are per class (`[0.8, 0.8]`), not positions of one scalar (`[0.8, 0.2]`), and they belong to [`ros2neuro_control_feedback`](../control/feedback.md).
* `protocol_ended` and the summary are also produced in calibration; the process exits when the protocol ends (`shutdown_on_end`).

## Tests

`colcon test --packages-select ros2neuro_manager_synchronous`: the trial sequence (counts, shuffle, any code), and
`test_synchronous_plugin`, the plugin loaded by the node of [`ros2neuro_manager`](index.md) with a helper node that plays
[`ros2neuro_control_feedback`](../control/feedback.md) (it answers CFeedback with the close of the feedback and Hit / Miss / Timeout): the ten events of
every trial in order, the manager writes the phases and the end of the outcome, the outcome is closed after the boom, the next trial waits for the outcome, every class
the requested number of times, `protocol_ended`, the wait of `duration.begin`, wrong `trials` / durations. `test_synchronous_no_outcome` (its own executable, the node shuts the process down):
the trial is never closed -> the manager stops with an error.

## Cueing paradigm

The trial structure of `Synchronous` (fixation, then a **cue** that tells the subject which class to perform, then the feedback)
follows the cueing paradigm introduced by Posner. The asynchronous protocol (`Asynchronous`, see
[`ros2neuro_manager_asynchronous`](asynchronous.md)) has no cues: the subject controls freely.

Reference: M. I. Posner, "Orienting of attention", *Quarterly Journal of Experimental Psychology*, 32(1), 3-25, 1980.
doi: [10.1080/00335558008248231](https://doi.org/10.1080/00335558008248231)
