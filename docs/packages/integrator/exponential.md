# Exponential integrator

!!! info ""
    Package: [`ros2neuro_integrator_exponential`](https://github.com/ros2neuro/ros2neuro_integrator_exponential) · pluginlib class: `ros2neuro::integrator::Exponential` · part of [Integrator](index.md)

Exponential moving integration for `ros2neuro_msgs/msg/NeuroPrediction`.

The plugin outputs integrated probabilities as `ros2neuro_msgs/msg/NeuroControl`.

Parameters:

- `alpha`: smoothing factor in `[0.0, 1.0]`
