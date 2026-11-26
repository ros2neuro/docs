# Integrator

!!! info ""
    Package: [`ros2neuro_integrator`](https://github.com/ros2neuro/ros2neuro_integrator)

The integrator turns the noisy stream of `NeuroPrediction` values of the decoder into a smoother `NeuroPrediction`
(`type = TYPE_SCORES`), so that a single wrong prediction does not move the feedback. The package provides the `Integrator` plugin interface and
`integrator_node`.

!!! important "Select one plugin"
    Set `integrator.type` to one of the classes below.

## What is in this menu

| Page | What you find |
|---|---|
| [Base class: `ros2neuro_integrator`](base.md) | the node, its topics and parameters, the plugin interface and how to write a new plugin |
| [Available plugins](#available-plugins) | the plugins of the family, each with its own page |

## Available plugins

| Plugin | pluginlib class | Behaviour |
|---|---|---|
| [Exponential](exponential.md) | [`ros2neuro::integrator::Exponential`](exponential.md) | exponential moving average of the probabilities (`alpha`) |
| [Buffer](buffer.md) | [`ros2neuro::integrator::Buffer`](buffer.md) | one accumulator per class, the winner goes up and the others down |
