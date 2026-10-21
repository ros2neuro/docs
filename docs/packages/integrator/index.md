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

ROS 2 base package for control integration in ROS2neuro.

It provides:

- a plugin interface for integrators that consume `ros2neuro_msgs/msg/NeuroPrediction`
- a runtime node that publishes `ros2neuro_msgs/msg/NeuroControl`
- optional rejection logic at node level to hold the previous output when the input confidence is below a threshold
- an optional reset service and reset event subscription
