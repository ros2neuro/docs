# SSVEP

!!! warning "TODO"
    The training of SSVEP decoders is not written yet. This page is a placeholder.

ROS2neuro was tested with motor imagery only; SSVEP needs a [processing](../packages/processing/index.md) plugin of its own (for example spectral features at the stimulation frequencies) and its own trainer. When it exists, it will produce a model folder like the one of [MI](mi/models.md) and will be loaded by a [decoder](../packages/decoder/index.md) plugin.

Back to [BCI decoders training](index.md).
