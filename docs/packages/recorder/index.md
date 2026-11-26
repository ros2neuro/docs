# Recorder

!!! info ""
    Package: [`ros2neuro_recorder`](https://github.com/ros2neuro/ros2neuro_recorder)

The recorder writes the data and the events of a session to a file. The package provides the `NeuroRecorder`
plugin interface and the `recorder` node, which manages the open / setup / run / close lifecycle. The storage
format belongs to the plugin.

!!! important "Select one plugin"
    Set the parameter `plugin`. Today the only backend is [XDF / GDF](xdf.md),
    [`ros2neuro::recorder::XDFRecorder`](xdf.md), which writes GDF or BDF through `xdffileio`.

## What is in this menu

| Page | What you find |
|---|---|
| [Base class: `ros2neuro_recorder`](base.md) | the node, its topics and parameters, the plugin interface and how to write a new plugin |
| [Available plugins](#available-plugins) | the plugins of the family, each with its own page |

## Available plugins

| Plugin | pluginlib class | Use it to |
|---|---|---|
| [XDF / GDF](xdf.md) | [`ros2neuro::recorder::XDFRecorder`](xdf.md) | write GDF or BDF through `xdffileio` |
