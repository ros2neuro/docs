# Synchronous manager (Training)

!!! info ""
    Package: [`ros2neuro_manager_synchronous`](https://github.com/ros2neuro/ros2neuro_manager_synchronous) · pluginlib class: `ros2neuro::manager::Training` · part of [Manager](index.md)

Plugin `ros2neuro::manager::Training` of [`ros2neuro_manager`](index.md): calibration and evaluation
protocol. It ports the logic of `game_controller`'s `training_controller` (trial sequence,
phases, blink handling, `protocol_ended`, summary) to the normalized per-class values of the
manager. The whole protocol runs on a thread of the plugin.

Per trial: `Start` -> `Fixation` -> cue (class code) -> `CFeedback` -> outcome (897/898/899),
each with its `+Off`. Events leave only through `emit_event()`.

## Parameters (declared on the manager node)

`modality` (`calibration` | `evaluation`), `trials` (same length as `classes`; error otherwise),
`duration.{begin,start,fixation,cue,feedback_min,feedback_max,boom,timeout,iti,end}`, (ms), and `rest_timeout` (seconds),
`protocol_ended_topic` (`/protocol_ended`, transient_local), `shutdown_on_end` (true).
`classes`, `rest_mode`, `thresholds` come from the core. There is no pause between CF+Off and the outcome event (they have the same
instant), so in the GDF `DUR(781) = POS(outcome) - POS(781)`.

## Outcomes (`evaluate_trial`)

A class *touches* when its normalized value >= its own threshold; with several touching the
highest value wins, at equal value the lowest index (order of `output_classes`).

| target | result |
|---|---|
| class with an output | winner == target -> **Hit** (897); another winner -> **Miss** (898); time over, nobody -> **Timeout** (899), never Miss |
| rest, `rest_mode=timeout` | no threshold to reach; a winner before the end -> **Miss**; none until the end -> **Hit** |
| rest, `rest_mode=class` | a normal class with its threshold; time over -> **Timeout** |

Durations: calibration `feedback_min..feedback_max` for every class (rest included); evaluation
`timeout` for classes with an output, `rest_timeout` (seconds, > 0, default 6) for a rest in timeout.

**`rest_timeout`** (seconds, > 0): **required** when an evaluation has the rest with `rest_mode=timeout` (the plugin refuses to
start without it; the launch files leave it empty on purpose). It is how long the rest lasts: if no threshold is touched for that
time it is a **Hit** (a threshold touched before is a Miss). It is independent from `timeout`, the maximum duration of the other
trials. It replaces the old `duration.timeout_on_rest` (ms). Not needed in a calibration (the rest lasts `feedback_min..feedback_max`
like any class) nor with `rest_mode=class`. The feedback shows the rest Hit with a yellow arc (wheel) or a yellow dot (bars).

`rest_mode` (default `none`): a **calibration** does not need it, the classes are the given ones and the rest is one
of them (cue and trial, no output). An **evaluation** with 783 in `classes` must set `rest_mode` to `timeout` or
`class`, otherwise the plugin refuses to configure.

## Calibration autopilot

Scalar `LinearPilot` / `SinePilot` + scalar -> vector expansion that sums to 1: the target rises
from 1/K to its threshold, the others share the rest. A rest in timeout oscillates around 1/K with an
amplitude below (min threshold - 1/K), so it never touches a threshold. The published `fields` are the
canonical ones. The autopilot follows the clock: one step per 10 ms elapsed (`steps_due()`, a late iteration
makes up for it) and an absolute deadline per tick, so the CFeedback lasts the planned time; a relative sleep per step made it ~3 % longer. After the boom the neutral vector 1/K is published, then the ITI.

## Reset

The integrator resets on the `CFeedback` event (`reset_event: 781` in its config): the plugin does **not**
request it. It calls `expect_reset()` before emitting CFeedback so values are ignored until the epoch
advances; without epoch it recreates the input subscription instead (see the manager README).
An open blink is closed (`Blink+Off`) before `CFeedback+Off`.

## Launch

```bash
ros2 launch ros2neuro_manager_synchronous synchronous.launch.xml modality:=evaluation \
    classes:="[773, 771, 783]" trials:="[10, 10, 5]" thresholds:="[0.8, 0.8]"
```
Declares `classes/rest_mode/thresholds` once and forwards them to manager and feedback
(`feedback_plugin:=ros2neuro::feedback::Bar` for the bars). Close the feedback window with ESC.

## Differences from the old controller

* Thresholds are per class (`[0.8, 0.8]`), not positions of one scalar (`[0.8, 0.2]`).
* `protocol_ended` and the summary are also produced in calibration; the process exits when the protocol
  ends (`shutdown_on_end`).

## Tests

`colcon test --packages-select ros2neuro_manager_synchronous`: outcomes (three rest cases, double
crossing, timeout), durations, trial sequence, autopilot (sum 1, always reaches a Hit, rest never
touches).
