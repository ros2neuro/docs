# ros2neuro_integrator: the node and the base class

!!! info ""
    Package: [`ros2neuro_integrator`](https://github.com/ros2neuro/ros2neuro_integrator)

The node and the plugin interface (the parent class) of the integrator family, with what is common to all its plugins. For what the family does and its list of plugins see the [overview](index.md); each plugin has its own page.

## Node behaviour

- Subscribes to a `NeuroPrediction` topic (`input_topic`, default `/prediction`) and publishes a `NeuroPrediction`
  of type `TYPE_SCORES` (`output_topic`, default `~/control`): `decoder` is the name of the integrator, `fields` are the
  ones of the input, `values` the integrated values. It publishes no decision: whoever reads it takes the highest value.
- **Rejection** (`integrator.rejection`): when the confidence of the input is below the value, the previous
  output is held. `-1` disables it.
- **Reset**: a service named `reset` (so `/reset`) and an optional reset on an event
  (`integrator.reset_event`, read on `event_topic`, default `/neuroevent`). Every reset makes the integrator
  publish a message with all values equal to `1/K`.
- Plugin parameters go under `integrator.params.*`.

## Minimal example

```yaml
/integrator:
  ros__parameters:
    input_topic: /classification/prediction
    output_topic: /integrated/raw
    event_topic: /neuroevent
    integrator.name: mi_exponential_integrator
    integrator.type: ros2neuro::integrator::Exponential
    integrator.params.alpha: 0.98
    integrator.rejection: 0.55
    integrator.reset_event: 781
```

## Writing a new integrator

Derive from `ros2neuro::integrator::Integrator`, register the class and export `plugins.xml` to
`ros2neuro_integrator`. The tutorial [Writing an integrator plugin](../../tutorials/integrator-plugin/index.md)
shows the whole process.

---

## Reference (from the package README)

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, `std_srvs`, [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs)
- **At run time**: an integrator plugin package

## Messages and topics

Default node name: `integrator`.

| | Default topic | Type | Changed by |
|---|---|---|---|
| subscribes | `/prediction` | `NeuroPrediction` | `input_topic` |
| subscribes | `/neuroevent` | `NeuroEvent` | `event_topic` (only used for `integrator.reset_event`) |
| publishes | `~/control` | `NeuroPrediction` | `output_topic` |

| | Service | Type | Note |
|---|---|---|---|
| provides | `reset` | `std_srvs/Empty` | relative name, `/reset` with the node at the root |

Messages used:

- `NeuroPrediction`: read
- `NeuroPrediction`: published (the integrated values)
- `NeuroEvent`: read, to reset on an event
- `std_srvs/Empty`: the reset service

<!-- /interfaces -->
## How it works

`integrator_node` (node name `integrator`) loads one integrator plugin and, for every `NeuroPrediction` it receives, asks the
plugin to update its integrated values and publishes them as a `NeuroPrediction`.

!!! note "Input: probabilities"
    The integrators expect predictions of type `TYPE_PROBABILITIES` (non-negative values that sum to 1, one per class): the
    rejection compares the highest value with a probability, the buffer integrator moves probability mass between the classes.
    The decoders of the stack publish probabilities, and every test and launcher of ros2neuro was made with `TYPE_PROBABILITIES`.
    A decoder may declare another `output.type` (scores, logits): it is not refused, but the result of the integration is then
    not defined by these rules.

The published message has:

- `decoder`: the name of the integrator (`integrator.name`);
- `fields`: copied from the prediction (the class names or codes);
- `values`: the integrated values, one per class;
- `type`: always `TYPE_SCORES` (the values are accumulators or smoothed scores, not guaranteed probabilities).

There are no `actions`/`commands`: the winning class is not published, whoever reads the message takes the highest value.

### Rejection

If `integrator.rejection` is set, a prediction whose **highest value is below it** is not integrated: the previous output is
published again (with the header of the new prediction) and the plugin is left untouched. It avoids moving the control on
predictions the decoder is unsure about. It is disabled by default (`-1`), and it has no effect before the first output.

### Reset

The integrated values can be reset in two ways:

- the service `reset` (`std_srvs/srv/Empty`), created with a **relative name**, so with the node at the root it is `/reset`;
- an event: when a `NeuroEvent` with `event_id == integrator.reset_event` arrives on `event_topic`. In a calibration or evaluation (trials) the
  launchers use `781` (CFeedback), so every trial starts from the neutral state.

A reset puts the plugin in its reset state (`1/K` for every class for the exponential integrator, `init_val` for the buffer one;
`K` is the number of classes of the last prediction: its `fields`, or its `values` when a decoder publishes no fields) and
**publishes a message with those values**; the service answers after that. [`ros2neuro_control_feedback`](../control/feedback.md)
waits for that answer and then uses only values made after its request. Before the first prediction there is nothing to reset.

## Parameters

| Parameter | Default | Meaning |
|---|---|---|
| `input_topic` | `/prediction` | the `NeuroPrediction` topic of the decoder |
| `output_topic` | `~/control` | where the integrated `NeuroPrediction` is published |
| `event_topic` | `/neuroevent` | the topic read for `integrator.reset_event` |
| `integrator.type` | (required) | pluginlib class of the integrator, for example [`ros2neuro::integrator::Exponential`](exponential.md) |
| `integrator.name` | `integrator` | written in `NeuroPrediction.decoder` |
| `integrator.rejection` | `-1` (off) | confidence below which a prediction is not integrated, in `[0, 1]` |
| `integrator.reset_event` | `-1` (off) | event id that resets the integrator |
| `integrator.params.*` | | parameters of the plugin (for example `integrator.params.alpha`) |

`integrator.rejection` and the `integrator.params.*` parameters can be changed while the node runs
(`ros2 param set /integrator integrator.params.alpha 0.9`). The node declares every `integrator.params.*` it is given at start
(parameter file or `-p`) and passes all of them to the plugin, at start and when they change; a plugin parameter that was not
given at start cannot be set later (ROS refuses an undeclared parameter). The older names `rejection` and `reset_event` are still accepted.

```yaml
/integrator:
  ros__parameters:
    input_topic: /classification/prediction
    output_topic: /integrated/raw
    event_topic: /neuroevent
    integrator.name: mi_exponential_integrator
    integrator.type: ros2neuro::integrator::Exponential
    integrator.params.alpha: 0.98
    integrator.rejection: 0.55
    integrator.reset_event: 781
```

## Plugins

- [`ros2neuro_integrator_exponential`](exponential.md) ([`ros2neuro::integrator::Exponential`](exponential.md)): exponential moving average;
- [`ros2neuro_integrator_buffer`](buffer.md) ([`ros2neuro::integrator::Buffer`](buffer.md)): per-class accumulator.

## Writing a plugin

Derive from `ros2neuro::integrator::Integrator` and implement:

- `configure()`: read the parameters with `getParam`, return `false` if they are invalid;
- `apply(prediction)`: update the state with one prediction and return an `IntegrationResult` (the integrated values and the
  decision, `-1` if none; the node does not publish the decision);
- `reset(class_count)`: go back to the neutral state (`1/K`) and return it;
- optionally `set_runtime_parameter(parameter)` to accept parameter changes while running.

Export the class with `PLUGINLIB_EXPORT_CLASS(Derived, ros2neuro::integrator::Integrator)`, describe it in a `plugins.xml` and
register that file with `pluginlib_export_plugin_description_file(ros2neuro_integrator plugins.xml)`.
