# Manager

!!! info ""
    Package: [`ros2neuro_manager`](https://github.com/ros2neuro/ros2neuro_manager)

The manager runs the **trials** of a calibration or an evaluation. It writes the phases of every trial (Start, Fixation, cue,
CFeedback...) on the event bus and listens to the same bus, where [`ros2neuro_control_feedback`](../control/feedback.md) writes
the outcome (Hit / Miss / Timeout): that is what ends the continuous feedback and lets the manager go on with the next trial.
It does not read the integrator, does not reset it and does not talk to the feedback: that is the [control](../control/index.md)
layer. The core is shared by all protocols; the protocol itself is a **plugin that you must select** with the parameter `plugin`.

The manager reads only its own parameters. What it shares with [`ros2neuro_control_feedback`](../control/feedback.md) and
[the feedback](../feedback/index.md) (the `classes`, the `rest_mode`, the ids of the events) is **the same parameter in each of the
three**, written once for every node (a `/**` section of the parameter file, see [Shared parameters](../../concepts/shared-parameters.md)):
nobody asks the manager for anything, and there is no code shared between the three. The thresholds are the only thing it does not
know: they are control's. See [Protocols](../../concepts/protocols.md) for the concepts behind them.

## Available plugins

| Plugin | pluginlib class | Protocol |
|---|---|---|
| [Synchronous](synchronous.md) | [`ros2neuro::manager::Synchronous`](synchronous.md) | calibration and evaluation: random order of the trials, Start, Fixation, cue, CFeedback, waits for the outcome |
| [Asynchronous](asynchronous.md) | [`ros2neuro::manager::Asynchronous`](asynchronous.md) | free control: no trials, writes no event (the reset at the threshold is in [`ros2neuro_control_feedback`](../control/feedback.md)) |

## Topics and services

| | Name (default) | Type |
|---|---|---|
| subscribes | `/neuroevent` (`event_topic`) | `NeuroEvent` |
| publishes | `/neuroevent` (`event_topic`) | `NeuroEvent` |

## Minimal example

```yaml
/**:                          # the same for the manager, control and the feedback
  ros__parameters:
    classes: [773, 771]
    rest_mode: none
    thresholds: [0.7, 0.7]    # the manager ignores them

/manager:
  ros__parameters:
    plugin: ros2neuro::manager::Synchronous
    trials: [10, 10]
    duration.begin: 5000
```

Complete launch files that run every protocol (the constant `PROTOCOL` at the top of each file) are in the `feedback/` folder of [`ros2neuro_devel_test`](../devel-test.md).

## Writing a new protocol

Derive from `ros2neuro::manager::Manager` (`configure`, `start`, `stop`, `on_event`), use only
`ManagerContext` (`emit_event`, `request_shutdown`, `now`...), and export it with
`PLUGINLIB_EXPORT_CLASS` and `pluginlib_export_plugin_description_file(ros2neuro_manager plugins.xml)`. The
asynchronous plugin is the smallest example.

---

## Reference (from the package README)

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, `builtin_interfaces`, [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)
- **At run time**: a protocol plugin package ([`ros2neuro_manager_synchronous`](synchronous.md) or `_asynchronous`), and [`ros2neuro_control_feedback`](../control/feedback.md) for the outcomes

## Messages and topics

Default node name: `manager`.

| | Default topic | Type | Changed by |
|---|---|---|---|
| subscribes | `/neuroevent` | `NeuroEvent` | `event_topic` (the outcome that ends the continuous feedback) |
| publishes | `/neuroevent` | `NeuroEvent` | `event_topic` (the phases of the trials) |

The manager calls no service.

Messages used:

- `NeuroEvent`: published (the protocol events) and read (the bus)

## Example configuration

The classes, the `rest_mode` and the thresholds are the same for the manager, control and the feedback: they go in a `/**` section, so
every node that loads the file takes them (a node ignores the ones it does not declare). The manager does not read the thresholds.

```yaml
/**:
  ros__parameters:
    classes: [773, 771]
    rest_mode: none
    thresholds: [0.7, 0.7]                    # control's and the feedback's; changeable while running on /control
    # event.hit: 897 ...                      # the ids of the events: the defaults are the ones of the project

/manager:
  ros__parameters:
    plugin: ros2neuro::manager::Synchronous      # or ros2neuro::manager::Asynchronous
    event_topic: /neuroevent
```

The plugin-specific parameters (trials, durations...) are in the README of each protocol plugin.

<!-- /interfaces -->
```
manager --Start, Fixation, cue, CFeedback--------------------> /neuroevent --> control_feedback
manager <--CFeedback+Off, Hit / Miss / Timeout----------------- /neuroevent <-- control_feedback
```

The manager decides **when** things happen (order and timing of the phases); [`ros2neuro_control_feedback`](../control/feedback.md) decides **what
happens during the continuous feedback** (autopilot, thresholds, outcome) and closes the trial. A protocol is a **plugin** (pluginlib, base class
`ros2neuro::manager::Manager`): [`ros2neuro_manager_synchronous`](synchronous.md) (calibration/evaluation trials) or
[`ros2neuro_manager_asynchronous`](asynchronous.md) (continuous control: nothing to write).

## The protocol parameters: the same value in every node

Nobody asks the manager for anything. The parameters that describe the protocol are **the same parameters in every node that needs
them**, written once for every node (a `/**` section of the parameter file, which each of those nodes loads):

| Parameter | What | Read by |
|---|---|---|
| `classes`, `rest_mode` | the classes of the trials, in order; `none` \| `timeout` \| `class` | manager, control_feedback, feedback |
| `event.start`, `event.fixation`, `event.cfeedback`, `event.hit`, `event.miss`, `event.timeout`, `event.off`, `event.shown` | the ids of the events (defaults 1, 786, 781, 897, 898, 899, 32768, 16384) | manager, control_feedback, feedback |
| `thresholds` | one per class with a classifier output | control_feedback, feedback (the manager ignores them) |

The durations of the trials (`duration.*`) are the manager's own; the ones of the continuous feedback (`duration.feedback_min`,
`duration.feedback_max`, `duration.timeout`, `rest_timeout`) are [`ros2neuro_control_feedback`](../control/feedback.md)'s.

### The ids of the events

Declared with `event.*` (checked at start: positive, all different, `event.off` and `event.shown` above the others, `event.shown` a power of two because the display events are recognised by its bit; manager, control and feedback refuse other values) and available to the
plugins as `ManagerContext::events()`. `event.off` is added to the id of the event it closes; `event.shown` is the flag of the display
events of the feedback, and every class code is below it. To change an id give the same value to the manager, control and the feedback (a `/**` section does it).

### Class codes are free

Any integer in 1..`event.shown`-1 that is not the id of an event is a valid class code (`501`, `502`, ...): 771/773/769/770 are only the
codes the project uses. The cue of a class is emitted as an event with the code of the class, so the ids of the events are **reserved**
and refused with the reason (Start, Fixation, CFeedback, Hit, Miss, Timeout). The **rest (783)** is the only code with a meaning (and the
only one with a color of its own: yellow, in the feedback). The names of the known codes (`BOTH_FEET (771)`, ...) only serve the logs.

### `rest_mode`

`none` (default) | `timeout` | `class`. The manager reads it and checks it: unsupported value, or `class` without 783 in
`classes`, is a configuration error. What it means is the classifier side's: with 783 in `classes`, `timeout` makes the rest a trial with
a cue and no classifier output (in an evaluation it is a Hit if no threshold is touched for `rest_timeout`), `class` makes it a normal class
with its own output and threshold; a calibration needs neither. Whether an evaluation or a control with 783 says `timeout` or `class` is
checked by [`ros2neuro_control_feedback`](../control/feedback.md).

## The event bus

`ManagerContext::emit_event(id)` is the single place that writes events: on `/neuroevent`, with `header.stamp = now()`. The manager
writes the phases of a trial (Start, Fixation, the cue, CFeedback, the end of the first three) and the end of the outcome. **It does not
write** the end of the continuous feedback nor the outcome: they come from [`ros2neuro_control_feedback`](../control/feedback.md), the node that knows the
thresholds. Every event of the bus (also the ones the manager wrote) is given to the plugin through `on_event()`. The recorder keys event
types on (`event_id`, `family_id`): never put counters in `family_id`/`description`.

## Parameters

| name | default | |
|---|---|---|
| `plugin` | (required) | [`ros2neuro::manager::Synchronous`](synchronous.md) / [`ros2neuro::manager::Asynchronous`](asynchronous.md) |
| `classes`, `rest_mode` | `[773, 771]`, `none` | the classes of the protocol |
| `event.*` | see above | the ids of the events |
| `event_topic` | `/neuroevent` | the bus: written and read |

Number arrays accept both `[1, 1]` and `[0.8, 0.8]` spellings. `classes` and `rest_mode` are read once. The manager does not read
`thresholds` (a `/**` section that has them for other nodes is fine).

## Writing a plugin

Derive from `Manager` (`configure/start/stop/on_event`), export it with `PLUGINLIB_EXPORT_CLASS` and
`pluginlib_export_plugin_description_file(ros2neuro_manager plugins.xml)`. The plugin may run its own thread; `ManagerContext` is
thread-safe (`layout`, `events`, `emit_event`, `now`, `request_shutdown(failed)`). Never spin inside callbacks. A plugin that holds the
`shared_ptr` of the node must let it go: the node calls `release_plugin()` before exiting. A plugin reads
its own parameters from the node: nobody asks the manager for them.

## Tests

`colcon test --packages-select ros2neuro_manager`: the ids of the events (defaults, validation, changed ids), the class codes (reserved,
out of range, following the configured ids), the protocol layout, and `test_manager_node` (a test plugin loaded by the node: it writes on
the bus, it hears the bus including its own events, the event ids / classes / rest_mode are parameters of the node, a missing
or unknown plugin or invalid ids do not configure).
