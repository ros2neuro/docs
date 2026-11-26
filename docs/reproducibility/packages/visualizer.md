# Visualizer: tests

!!! info ""
    Package: [Visualizer](../../packages/visualizer.md) · part of [Reproducibility](../index.md) › [Packages](index.md)

```bash
colcon test --packages-select ros2neuro_visualizer
```

Three gtests cover the non-GUI helpers: `test_signal_buffer` (ring buffer order, zero padding, chunks larger than the
window), `test_filter_pipeline` (CAR and single-channel reference) and `test_spectrum_averager` (off, rolling and
cumulative averaging).
