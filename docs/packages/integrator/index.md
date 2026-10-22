# Integrator

!!! info ""
    Package: [`ros2neuro_integrator`](https://github.com/ros2neuro/ros2neuro_integrator)

The integrator turns the noisy stream of `NeuroPrediction` values into a smoother `NeuroControl`, so that a
single wrong prediction does not move the feedback. The package provides the `Integrator` plugin interface and
`integrator_node`.

!!! important "Select one plugin"
    Set `integrator.type` to one of the classes below.

## Available plugins

| Plugin | pluginlib class | Behaviour |
|---|---|---|
| [Exponential](exponential.md) | [`ros2neuro::integrator::Exponential`](exponential.md) | exponential moving average of the probabilities (`alpha`) |
| [Buffer](buffer.md) | [`ros2neuro::integrator::Buffer`](buffer.md) | one accumulator per class, the winner goes up and the others down |

## Node behaviour

- Subscribes to a `NeuroPrediction` topic (`input_topic`, default `/prediction`) and publishes a `NeuroControl`
  (`output_topic`, default `~/control`).
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
| publishes | `~/control` | `NeuroControl` | `output_topic` |

| | Service | Type | Note |
|---|---|---|---|
| provides | `reset` | `std_srvs/Empty` | relative name, `/reset` with the node at the root |

Messages used:

- `NeuroPrediction`: read
- `NeuroControl`: published
- `NeuroEvent`: read, to reset on an event
- `std_srvs/Empty`: the reset service

<!-- /interfaces -->
## How it works

`integrator_node` (node name `integrator`) loads one integrator plugin and, for every `NeuroPrediction` it receives, asks the
plugin to update its integrated values and publishes them as a `NeuroControl`.

The published message has:

- `source`: the name of the integrator (`integrator.name`);
- `fields`: copied from the prediction (the class names or codes);
- `values`: the integrated values, one per class;
- `actions = ["selection"]` and `commands = [i]`, where `i` is the index of the winning class (the decision of the plugin, or
  the highest value if the plugin gives none).

### Rejection

If `integrator.rejection` is set, a prediction whose **highest value is below it** is not integrated: the previous output is
published again (with the header of the new prediction) and the plugin is left untouched. It avoids moving the control on
predictions the decoder is unsure about. It is disabled by default (`-1`), and it has no effect before the first output.

### Reset

The integrated values can be reset in two ways:

- the service `reset` (`std_srvs/srv/Empty`), created with a **relative name**, so with the node at the root it is `/reset`;
- an event: when a `NeuroEvent` with `event_id == integrator.reset_event` arrives on `event_topic`. In a training protocol the
  launchers use `781` (CFeedback), so every trial starts from the neutral state.

A reset puts the plugin in its neutral state (`1/K` for every class, `K` being the number of classes of the last prediction) and
**publishes a message with those values**. The manager relies on that message to know that the reset has happened. Before the
first prediction there is nothing to reset.

## Parameters

| Parameter | Default | Meaning |
|---|---|---|
| `input_topic` | `/prediction` | the `NeuroPrediction` topic of the decoder |
| `output_topic` | `~/control` | where the `NeuroControl` is published |
| `event_topic` | `/neuroevent` | the topic read for `integrator.reset_event` |
| `integrator.type` | (required) | pluginlib class of the integrator, for example [`ros2neuro::integrator::Exponential`](exponential.md) |
| `integrator.name` | `integrator` | written in `NeuroControl.source` |
| `integrator.rejection` | `-1` (off) | confidence below which a prediction is not integrated, in `[0, 1]` |
| `integrator.reset_event` | `-1` (off) | event id that resets the integrator |
| `integrator.params.*` | | parameters of the plugin (for example `integrator.params.alpha`) |

`integrator.rejection` and the `integrator.params.*` parameters can be changed while the node runs
(`ros2 param set /integrator integrator.params.alpha 0.9`). The older names `rejection` and `reset_event` are still accepted.

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
  decision, `-1` if none);
- `reset(class_count)`: go back to the neutral state (`1/K`) and return it;
- optionally `set_runtime_parameter(parameter)` to accept parameter changes while running.

Export the class with `PLUGINLIB_EXPORT_CLASS(Derived, ros2neuro::integrator::Integrator)`, describe it in a `plugins.xml` and
register that file with `pluginlib_export_plugin_description_file(ros2neuro_integrator plugins.xml)`.

## Tests

`colcon test --packages-select ros2neuro_integrator`
