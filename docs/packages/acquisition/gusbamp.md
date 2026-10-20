# g.USBamp device

!!! info ""
    Package: [`ros2neuro_acquisition_gusbamp`](https://github.com/ros2neuro/ros2neuro_acquisition_gusbamp) · pluginlib class: `ros2neuro::acquisition::GUSBampDevice` · part of [Acquisition](index.md)

`ros2neuro_acquisition_gusbamp` provides the direct g.tec g.USBamp backend for
`ros2neuro_acquisition`.

Use g.USBamp hardware through this package and plugin:

```text
ros2neuro::acquisition::GUSBampDevice
```

## Executable

```bash
ros2 run ros2neuro_acquisition_gusbamp acquisition_gusbamp
```

The package also installs a convenience launch file that uses the generic
`ros2neuro_acquisition` runtime:

```bash
ros2 launch ros2neuro_acquisition_gusbamp gusbamp_acquisition.launch.xml
```

## Parameters

All parameters are expected under the acquisition node device prefix. With the
current plugin runtime that prefix is `acquisition`.

- `acquisition.samplerate`
- `acquisition.framerate`
- `acquisition.device`
- `acquisition.channels`
- `acquisition.enable_trigger_line`
- `acquisition.scan_dio`
- `acquisition.slave_mode`
- `acquisition.enable_sc`
- `acquisition.bandpass_filter`
- `acquisition.notch_filter`
- `acquisition.bipolar_derivation`
- `acquisition.sensors.eeg.enable`
- `acquisition.sensors.eeg.name`
- `acquisition.sensors.eeg.labels`
- `acquisition.triggers.trigger.enable`
- `acquisition.triggers.trigger.name`
- `acquisition.triggers.trigger.labels`
