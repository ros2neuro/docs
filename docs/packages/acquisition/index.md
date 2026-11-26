# Acquisition

!!! info ""
    Package: [`ros2neuro_acquisition`](https://github.com/ros2neuro/ros2neuro_acquisition)

The acquisition package is the entry point of the signal chain. It provides the generic `acquisition` node, the
`NeuroDevice` plugin interface and the state machine that turns a device into ROS 2 topics and services. It knows
nothing about a specific amplifier: the device driver is a **plugin that you must select**.

!!! important "Select one plugin"
    The node does nothing useful until the parameter `acquisition.plugin` names one of the plugins below.

## What is in this menu

| Page | What you find |
|---|---|
| [Base class: `ros2neuro_acquisition`](base.md) | the node, its topics and parameters, the plugin interface and how to write a new plugin |
| [Available plugins](#available-plugins) | the plugins of the family, each with its own page |

## Available plugins

| Plugin | pluginlib class | Use it to |
|---|---|---|
| [Dummy](dummy.md) | [`ros2neuro::acquisition::DummyDevice`](dummy.md) | generate synthetic EEG/EMG/trigger data, no hardware |
| [XDF / GDF replay](xdf.md) | [`ros2neuro::acquisition::XDFDevice`](xdf.md) | replay a recorded file as if it were live |
| [LSL](lsl.md) | [`ros2neuro::acquisition::LSLDevice`](lsl.md) | read a Lab Streaming Layer stream |
| [eegdev](eegdev.md) | [`ros2neuro::acquisition::EGDDevice`](eegdev.md) | read a device supported by the eegdev library |
| [ANT Neuro](antneuro.md) | [`ros2neuro::acquisition::EEGODevice`](antneuro.md) | ANT Neuro amplifiers (hardware required) |
| [g.USBamp](gusbamp.md) | [`ros2neuro::acquisition::GUSBampDevice`](gusbamp.md) | g.tec g.USBamp (hardware required) |
