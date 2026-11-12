# Messages and data library

!!! info ""
    Packages: [`ros2neuro_msgs`](https://github.com/ros2neuro/ros2neuro_msgs) · [`ros2neuro_data`](https://github.com/ros2neuro/ros2neuro_data) · part of [Packages](index.md)

Two small packages sit under every other node.

| Package | What it is |
|---|---|
| `ros2neuro_msgs` | the ROS 2 interfaces: the contract between all nodes |
| `ros2neuro_data` | in-memory C++ types that mirror the messages, with validation and conversion |

## ros2neuro_msgs

Defines `NeuroFrame`, `NeuroFrameInfo`, `NeuroSensor`, `NeuroSensorInfo`, `NeuroTrigger`, `NeuroTriggerInfo`,
`NeuroAxis`, `NeuroFeature`, `NeuroPrediction`, `NeuroControl` and `NeuroEvent`.

The fields, the sample-major layout, the type constants and the QoS recommendations are described in
[Messages and data types](../concepts/messages.md). Dependencies: `ament_cmake`, `rosidl_default_generators`,
`rosidl_default_runtime`, `std_msgs`.

```bash
colcon build --packages-select ros2neuro_msgs
source install/setup.bash
ros2 interface show ros2neuro_msgs/msg/NeuroFrame
```

## ros2neuro_data

A support library for plugins. Its role is to keep acquisition code independent from ROS message objects:

1. a device fills a `ros2neuro::data::NeuroFrame`;
2. the frame is validated;
3. the frame is converted to `ros2neuro_msgs::msg::NeuroFrame`;
4. the node publishes the message.

### Types

| Type | Notes |
|---|---|
| `ros2neuro::data::NeuroSignal<T>` | common sampled-signal structure: `name`, `samples`, `channels`, `min_value`, `max_value`, `data` (getters and setters) |
| `NeuroSensor`, `NeuroTrigger` | the analog (`float`) and digital (`int32`) specialisations; `NeuroSensor` adds `type`, `unit`, `labels`, `NeuroTrigger` adds `unit`, `labels` |
| `NeuroAxis` | one semantic axis of a feature |
| `NeuroFeature` | tensor with `header`, `name`, `type`, `window_length`, `shape`, `axes`, `data`, `unit`, `description` |
| `NeuroFrame` | the chunk with its sensors and triggers |
| `NeuroEvent` | plain struct mirroring the `NeuroEvent` message |

`NeuroFeature` is separate from `NeuroSignal<T>` because a feature is not limited to a time-by-channel matrix.

### Layout

For sampled signals the flat `data` vector is sample-major: `index = sample * channels + channel`. With 3 channels
and 2 samples: `[s0c0, s0c1, s0c2, s1c0, s1c1, s1c2]`.

### Validation and conversion

| Function | Purpose |
|---|---|
| `is_valid(x, &error)` | returns `false` and fills `error` if the object is inconsistent |
| `validate(x)` | same check, throws on failure |
| `to_msg(x)` | runtime type to ROS message |
| `from_msg(msg)` | ROS message to runtime type |
| `to_msg_info(x)` / `from_msg_info(msg, x)` | runtime type to/from `NeuroFrameInfo`, `NeuroSensorInfo`, `NeuroTriggerInfo` |

They are overloaded for `NeuroAxis`, `NeuroSensor`, `NeuroTrigger`, `NeuroFeature` and `NeuroFrame` (`to_msg` /
`from_msg` also for `NeuroEvent`). The checks cover non-empty required fields, an axis with both `labels` and `values`, shape and data-size consistency, axis consistency and consistency between a frame and
its signals.

### Example

```cpp
#include "ros2neuro_data/NeuroFrame.h"
#include "ros2neuro_data/NeuroSensor.h"
#include "ros2neuro_data/NeuroDataConvert.h"
#include "ros2neuro_data/NeuroDataValidate.h"
#include "ros2neuro_msgs/msg/neuro_sensor_info.hpp"

ros2neuro::data::NeuroFrame frame;
frame.set_device_id("dev0");
frame.set_samples(4);
frame.set_samplerate(256.0f);

ros2neuro::data::NeuroSensor eeg;
eeg.set_name("eeg");
eeg.set_type(ros2neuro_msgs::msg::NeuroSensorInfo::TYPE_EEG);
eeg.set_unit("uV");
eeg.resize(4, 2);        // samples, channels
eeg.set_labels({"C3", "C4"});
eeg.at(0, 0) = 1.0f;     // at(sample, channel)
eeg.at(0, 1) = 2.0f;

frame.add_sensor(eeg);

ros2neuro::data::validate(frame);
auto msg = ros2neuro::data::to_msg(frame);
```

```bash
colcon build --packages-select ros2neuro_data
```
