# Shared parameters

Some values appear in the yaml of **several nodes or plugins** and must be the same everywhere. This page says how the stack handles
them: which ones are **global** (one section loaded by every node that needs them), and which ones are still copied in each yaml, so
you can decide what else deserves a global parameter.

**No node asks another node for a parameter.** Every node declares and reads its own parameters; a value that several nodes share is the
same parameter in each of them (same name, same default), and the parameter file gives it to all of them at once. One exception: the
feedback has no default for `classes` and `thresholds` (the manager and control default to `[773, 771]` and `[0.8, 0.8]`), so they must
be given to it.

## Global parameters: the `/**` section

ROS 2 gives **one value to every node** with the wildcard `/**` in a parameter file. A node takes the parameters it declares and ignores the
others, so the same file can be given to the manager, to control and to the feedback:

```yaml
/**:
  ros__parameters:
    classes: [773, 771]
    rest_mode: none
    thresholds: [0.7, 0.7]
```

The launchers of [`ros2neuro_devel_test`](../packages/devel-test.md) do this with `data/config/layout.yaml`, which the manager, control and the
feedback all load.

| Parameter | Read by | Notes |
|---|---|---|
| `classes`, `rest_mode` | manager, control ([`control_feedback`](../packages/control/feedback.md)), feedback | the layout of the trials and of the drawing; read once |
| `event.start`, `event.fixation`, `event.cfeedback`, `event.hit`, `event.miss`, `event.timeout`, `event.off`, `event.shown` | manager, control ([`control_feedback`](../packages/control/feedback.md)), feedback | the ids of the events; the defaults (1, 786, 781, 897, 898, 899, 32768, 16384) are the same in the three, so they are written only to change them |
| `thresholds` | control ([`control_feedback`](../packages/control/feedback.md)), feedback | control decides with them; the feedback uses them for the first markers. When they change while running (`ros2 param set /control thresholds ...`) control puts the ones in force in the flow and the feedback follows |

The thresholds are the only global value that changes while running, and they reach the feedback **in the flow** (`threshold:<code>` in
`NeuroControl.fields`), not through the parameter service.

## Own parameters (not shared)

| Node | Own parameters |
|---|---|
| manager | `plugin`, `trials`, `duration.begin / start / fixation / cue / boom / iti / end / outcome_wait`, `protocol_ended_topic`, `shutdown_on_end` |
| control ([`control_feedback`](../packages/control/feedback.md)) | `protocol`, `input_fields`, `duration.feedback_min / feedback_max / timeout`, `rest_timeout`, `input_topic`, `reset_service`, `control_topic` |
| feedback | `plugin`, `fps`, `window_title`, `publish_display_events`, `latency_log_period_s` |

## Still written in several places

These are the same value in several yaml sections, with **no** global section yet. A mismatch breaks the pipeline in a way that is hard to see.

### 1. Names of topics and services

| Value (in the test launchers) | Where it is written |
|---|---|
| `/neuroevent` | `event_topic` of the **manager**, of **control**, of the **feedback**, of the **integrator**, and `topic_event` of the **recorder** |
| `/acquisition/neurodata` | the output of the acquisition; `input_topic` of the filters; `topic_data` of the recorder; the topic chosen in the visualizer |
| `/acquisition/neurodata_info` | the output of the acquisition and `topic_info` of the recorder |
| `/processing/filtered` | `output_topic` of the filters and `input_topic` of the spectral and buffer nodes |
| `/processing/psd` (or `/processing/buffered_features`) | `output_topic` of the Welch (or buffer) node and `input_topic` of the decoder |
| `/classification/prediction` | `output_topic` of the decoder and `input_topic` of the integrator |
| `/integrated/raw` | `output_topic` of the integrator and `input_topic` of control |
| `/control_feedback/probabilities` | `control_topic` of control and `control_topic` of the feedback |
| `/reset` | the service of the integrator and `reset_service` of control |

### 2. One number in two places

| Value | Where it is written |
|---|---|
| the reset event (781, the id of CFeedback) | `integrator.reset_event` in the **integrator**, and `event.cfeedback` of the manager, control and the feedback. They are the same event: if you change the id in the three, the integrator does not follow |
| the number of classes K | `classes`, `trials` (manager, one value per class), `thresholds` (one per class with an output), and the classes of the decoder model |
| the class codes | `classes`, `input_fields` of control when the model publishes other codes, and the output fields of the decoder model |

### 3. The signal: it must agree from the acquisition to the decoder

| Value | Where it is written |
|---|---|
| the name of the sensor block (`EEG`) | `acquisition.sensors.eeg.name`, `processing.params.sensor` of the processing plugins (`Welch`, `Buffer`...; matched exactly, case sensitive) |
| the number of channels | the labels of `acquisition.sensors.eeg.labels`, `nchannels` of the spatial filters, and what the decoder model was trained on |
| the sampling rate (512 Hz) | the device (or the GDF file), `processing.params.samplerate` of the spectral plugins (0 reads it from the frame), `processing.params.buffer` of the `Buffer` plugin (its length) |
| the feature: name and frequencies | `processing.params.feature` (`psd`), `processing.params.frequencies` (`4:2:48`) of the `Welch` plugin and the input contract in the `manifest.yaml` of the decoder model |

## What could become global next

Suggested order, from the most useful:

1. **`event_topic`**: five places, always the same value. Put it in the `/**` section too.
2. **The wiring of the chain** (`/integrated/raw`, `/classification/prediction`, `/control_feedback/probabilities`, `/reset`): each name is
   written once as an output and once as an input.
3. **The reset event**: put `event.cfeedback` in the global section and let the integrator read it (instead of its own
   `integrator.reset_event`).
4. **The signal** (sensor name, channels, sampling rate): the acquisition publishes `NeuroFrameInfo` with the names, the channel labels and
   the rate, so the processing and the filters could read them from it instead of from their own yaml. This changes how the nodes work (it
   is not only a yaml change), so decide it separately.

!!! note
    A global parameter (`/**`) is still a copy per node: it moves the place where you write it, it does not remove the copies. That is
    the price of having no node that asks another one.
