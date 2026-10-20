# Manager

!!! info ""
    Package: [`ros2neuro_manager`](https://github.com/ros2neuro/ros2neuro_manager)

The manager sits between the integrator and the feedback and runs the **protocol**. The core is shared by all
protocols; the protocol itself is a **plugin that you must select** with the parameter `plugin`.

The core owns, in one place each: the catalog of event and class codes, the mapping of the integrator `fields`
to classes, the normalisation of the values, the emission of events and the reset handling. See
[Protocols](../../concepts/protocols.md) for the concepts behind them.

## Available plugins

| Plugin | pluginlib class | Protocol |
|---|---|---|
| [Synchronous](synchronous.md) | `ros2neuro::manager::Training` | calibration and evaluation (`modality`): trial sequence, cues, outcomes |
| [Asynchronous](asynchronous.md) | `ros2neuro::manager::Control` | free control: resets the integrator when a class reaches its threshold |

## Topics and services

| | Name (default) | Type |
|---|---|---|
| subscribes | `/integrated/raw` (`integrated_topic`) | `NeuroControl` |
| publishes | `/manager_control/probabilities` (`control_topic`) | `NeuroControl` |
| publishes | `/neuroevent` (`event_topic`) | `NeuroEvent` |
| service client | `/integrator/reset` (`reset_service`, launchers use `/reset`) | `std_srvs/Empty` |

## Minimal example

```yaml
/**:                       # shared layout, also loaded by the feedback
  ros__parameters:
    classes: [773, 771]
    rest_mode: none
    thresholds: [0.7, 0.7]

/manager:
  ros__parameters:
    plugin: ros2neuro::manager::Training
    modality: calibration
    trials: [10, 10]
    reset_service: /reset
```

Complete launch files for every protocol are in [`ros2neuro_devel_test`](../devel-test.md).

## Writing a new protocol

Derive from `ros2neuro::manager::ManagerPlugin` (`configure`, `start`, `stop`, `on_input`), use only
`ManagerContext` (`emit_event`, `publish_values`, `request_reset`...), and export it with
`PLUGINLIB_EXPORT_CLASS` and `pluginlib_export_plugin_description_file(ros2neuro_manager plugins.xml)`. The
asynchronous plugin is the smallest example.

---

## Reference (from the package README)

Core of the protocol manager. It sits between the integrator and the feedback:

```
integrator --/integrated/raw--> manager (+ plugin) --control_topic (flow)--> feedback
                                   |  ^                                        
                       /neuroevent |  | /integrator/reset (std_srvs/Empty)
```

It owns, in ONE place each: the code/event catalog, the `fields` -> class mapping,
the normalization, the event emission, and the reset handling. A protocol is a
**plugin** (pluginlib, base class `ros2neuro::manager::ManagerPlugin`):
`ros2neuro_manager_synchronous` (calibration/evaluation) or `ros2neuro_manager_asynchronous`.

## Class codes are free; the catalog is a convenience (`catalog.hpp`)

Any integer in 1..16383 that is not the id of an event is a valid class code (`501`, `502`, ...): 771/773/769/770 are only the codes the
project uses. The cue of a class is emitted as an event with the code of the class, so these ids are **reserved** and refused with the reason:
1 Start, 781 CFeedback, 786 Fixation, 897/898/899 Hit/Miss/Timeout, 1024 Blink (16384 and 32768 are the Shown / Off flags).
The **rest (783) is the only code with a meaning** (and the only one with a color: yellow). The catalog just gives names to the codes the
project knows, for the `fields` of the integrator and for the logs (`BOTH_FEET (771)`; a code without a name is shown as `501`):

| code | name |
|---|---|
| 783 | `REST` |
| 769 / 770 | `LEFT_HAND` / `RIGHT_HAND` |
| 771 / 773 | `BOTH_FEET` / `BOTH_HANDS` |
| 730 / 731 / 750 / 751 | `BOTTOM_LEFT` / `BOTTOM_RIGHT` / `MI_LEFT` / `MI_RIGHT` |

Events: Start 1, Fixation 786, CFeedback 781, Hit 897, Miss 898, Timeout 899, Blink 1024, Off 32768 (added to the id it closes), Shown 16384
(added to the id of what the feedback has shown). Colors never depend on the code: the feedback colors a class by its position.

## Fields mapping (`fields_map.hpp`, the only implementation)

For every `fields[i]` of the integrator message: (1) a whole-integer string is that code;
(2) otherwise it is normalized (upper case, spaces/`-` -> `_`) and looked up in the catalog;
(3) an unknown or duplicated name discards the message with a throttled error listing the
accepted names. The position of a class in the vector is found by its code: **the order of
the integrator outputs does not matter**. The order that matters is the one of the
`classes` parameter (feedback layout).

## Model codes different from the classes (`input_fields`)

The integrator publishes the codes of the **model**. If they are the ones of `classes`, nothing to do. If not (the model says 773/771 but
the experiment calls the classes 501/502), `input_fields: [773, 771]` says which model code stands for each class, in the order of `classes`
(codes or names; a rest in timeout has no output and is not listed). The manager maps them: events, flow, feedback and logs use the classes' codes.
Without the map the message is discarded with an error that says which codes the model should send. Calibration needs none of this.

## Layout and the three roles of REST

Parameters shared with the feedback: `classes` (codes, order matters), `rest_mode`
(`none` | `timeout` | `class`, default `none`), `thresholds`.

* `protocol_classes` = `classes` (rest included: it has trials and cues).
* `output_classes` = `classes` minus 783 when `rest_mode=timeout` (same order); `K = |output_classes|`.
* `thresholds` has exactly `K` values, in the order of `output_classes` (a rest in timeout has none).

Roles of the rest: **A. trial/cue** (always, if 783 is in `classes`); **B. classifier output**
(only with `rest_mode=class`); **C. evaluation** (training: see its README).

`rest_mode=none` (default) means "not said": the layout treats a 783 as `timeout` (trial and cue, no output, no
threshold). A **calibration** needs nothing more (the rest is just one of the given classes). An **evaluation** or
a **control** with 783 in `classes` must say `timeout` or `class`, otherwise `configure()` fails.
`rest_mode=class` without 783 in `classes` is a configuration error (the old value `bar` is gone).

Configuration errors (`configure()` fails): class code reserved or out of range; duplicate classes;
unsupported `rest_mode`; `rest_mode=class` without 783 (evaluation/control: 783 without `rest_mode`); fewer than 2 output classes;
`thresholds.size() != K`; thresholds outside (0, 1]. Warning: a threshold <= 1/K.

## Input handling

Each `NeuroControl` from the integrator: map fields -> check (set of codes == `output_classes`,
`values.size() == fields.size()`; empty `fields` falls back to the `output_classes` order with a
one-time warning, needs `values.size() == K`) -> reorder -> **normalize** `v_i / sum`
(negative/non-finite count as 0; sum <= 0 gives the uniform 1/K; a vector that already sums to 1
is left alone). The integrator publishes per-class accumulators in [0, 1] that do not sum to 1:
only the normalized vector is ever used. Invalid messages are dropped with a throttled error;
the protocol keeps running. The field map is logged at the first valid message.

## Flow towards the feedback

`control_topic` (default `/manager_control/probabilities`) is the ONLY source of the feedback.
`NeuroControl` in canonical form: `fields` = codes of `output_classes` as strings, `values` =
normalized vector, `actions/commands`: `seq` (progressive counter), optionally `event`
(command = catalog id) or `outcome` (897/898/899). A message carries at most one of the two.

`ManagerContext::emit_event(id)` is the single place that emits events: first on
`/neuroevent` (`header.stamp = now()`), then on the flow with the same stamp. The recorder keys
event types on (`event_id`, `family_id`): never put counters in `family_id`/`description`.

## Reset

A reset is a **service call**, not a topic: `std_srvs/srv/Empty` on `reset_service` (default `/integrator/reset`; the
integrator creates it as the relative name `reset`, i.e. **`/reset`**, so the launchers pass `reset_service:=/reset`). The
integrator can also reset on an event (`integrator.reset_event`, `/neuroevent`): training relies on that (CFeedback, 781).
Either way, **every reset makes the integrator publish a message whose values are all 1/K** on its output topic.

**Control (`request_reset()`).** From the moment the request is sent, the values coming from the integrator are the ones of
before the reset, so until the reset message arrives they are neither forwarded to the feedback nor given to the plugin for
decisions (the feedback keeps showing the last value). The first message with all values = 1/K (tolerance 1e-3 on each
normalized value) ends the wait and is used like any other. While waiting no other reset is requested.
* **Timeout**: if that message does not arrive within **1000 ms** (fixed) something in the pipeline does not work (the
  integrator does not publish, or the service does not reset it): the manager logs an **error** and **shuts down** (exit
  code 1). `asynchronous.launch.xml` starts it with `on_exit="shutdown"`, so the whole session (feedback and pipeline launched
  in the same file) ends with it.
* **Resets asked by someone else** do not disturb it: they also produce a neutral message, which at most ends the wait a
  little early (the neutral message of our own request then follows as an ordinary message).
* A threshold <= 1/K (warned at start) is met by the neutral vector itself: it would ask for a reset at every message.

**Training.** The plugin does not ask for the reset (the integrator does it on CFeedback). Before emitting CFeedback it
calls `expect_reset()`: if the integrator messages carry an `epoch` action (reset counter) the values are ignored until it
advances (capped by `reset_ack_timeout_ms`); without epoch the plugin recreates the input subscription instead, to drop the
stale queue. The integrators in this workspace do not publish the epoch. If they did, the integrator should put the counter in
`actions`/`commands` of every message it publishes (reset and rejection included) and increment it at every reset.

## Parameters

| name | default | |
|---|---|---|
| `plugin` | (required) | `ros2neuro::manager::Training` / `ros2neuro::manager::Control` |
| `classes`, `rest_mode`, `thresholds` | `[773, 771]`, `none`, `[0.8, 0.8]` | shared layout |
| `input_fields` | (empty) | optional, manager only: the code the model/integrator uses for each output, in the order of `classes` (rest in timeout excluded); see below |
| `integrated_topic` | `/integrated/raw` | |
| `control_topic` | `/manager_control/probabilities` | flow |
| `event_topic` | `/neuroevent` | also read for Blink / Blink+Off |
| `reset_service` | `/integrator/reset` | |
| `reset_ack_timeout_ms` | 2000 | training only: how long values are ignored after CFeedback if the epoch never advances |

Number arrays accept both `[1, 1]` and `[0.8, 0.8]` spellings. `classes`/`rest_mode` cannot change
at runtime; `thresholds` can only if the plugin allows it (control does).

## Writing a plugin

Derive from `ManagerPlugin` (`configure/start/stop/on_input`), export it with
`PLUGINLIB_EXPORT_CLASS` and `pluginlib_export_plugin_description_file(ros2neuro_manager plugins.xml)`.
The plugin may run its own thread; `ManagerContext` is thread-safe. Never spin inside callbacks.

## Tests

`colcon test --packages-select ros2neuro_manager` (pure gtest, no ROS running): layout and
configuration checks, fields mapping (numeric/named/order), set and size checks, normalization
(sum <= 0 included), reset gate with epoch and fallback, flow format.
