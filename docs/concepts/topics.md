# Topics and services

The names below are the **defaults** of each node. Launch files remap them, so the real names depend on the
node name you give: a node called `acquisition` publishes `~/neurodata` as `/acquisition/neurodata`.

The chain they connect is the one of the [architecture figure](architecture.md#the-loop-in-one-figure): every solid arrow there is one of the topics below. The tables use the topic names of the [`ros2neuro_devel_test`](../reproducibility/packages/index.md) launchers. Click a message type to read its description.

## Topics

| Node | Direction | Default topic | Type | Purpose |
|---|---|---|---|---|
| acquisition | publishes | `~/neurodata` | [`NeuroFrame`](messages.md#neuroframe) | raw samples |
| acquisition | publishes | `~/neurodata_info` | [`NeuroFrameInfo`](messages.md#neuroframeinfo) | stream metadata (`transient_local`) |
| filter chain | subscribes | `/neurodata` | [`NeuroFrame`](messages.md#neuroframe) | signal to filter |
| filter chain | publishes | `~/filtered` | [`NeuroFrame`](messages.md#neuroframe) | filtered signal |
| processing node (Welch, FFT, Spectrogram, Buffer plugins) | subscribes | `/neurodata` (`input_topic`) | [`NeuroFrame`](messages.md#neuroframe) | signal to analyse or to buffer: the filtered signal, remapped |
| processing node (Fbcsp plugin) | subscribes | the `input_topics`, one per band (`/processing/band_8_12`, ...) | [`NeuroFrame`](messages.md#neuroframe) | one band-passed stream per band (one filter chain per band); the frames with the same stamp make a group |
| processing node | publishes | `/features` (`output_topic`) | [`NeuroFeature`](messages.md#neurofeature) | PSD, spectrum, spectrogram, window of the signal or FBCSP features, according to the plugin |
| decoder | subscribes | `/features` | [`NeuroFeature`](messages.md#neurofeature) | feature to classify: a PSD (classic decoders) or a window (deep learning) |
| decoder | publishes | `~/prediction` | [`NeuroPrediction`](messages.md#neuroprediction) | class values |
| integrator | subscribes | `/prediction` (`input_topic`) | [`NeuroPrediction`](messages.md#neuroprediction) | decoder output |
| integrator | publishes | `~/control` (`output_topic`) | [`NeuroPrediction`](messages.md#neuroprediction) | integrated values (`type = TYPE_SCORES`, `decoder` = name of the integrator) |
| integrator | subscribes | `/neuroevent` (`event_topic`) | [`NeuroEvent`](messages.md#neuroevent) | optional reset on an event |
| control | subscribes | `/integrated/raw` (`input_topic`) | [`NeuroPrediction`](messages.md#neuroprediction) | integrator output |
| control (Feedback plugin) | publishes | `/control_feedback/probabilities` (`control_topic`) | [`NeuroControl`](messages.md#neurocontrol) | flow for the feedback: the values and the thresholds in force, with the header of the `NeuroPrediction` they come from |
| control (Feedback plugin) | subscribes, publishes | `/neuroevent` (`event_topic`) | [`NeuroEvent`](messages.md#neuroevent) | hears the phases of the trials, writes only the end of CFeedback (CFeedback+Off) and Hit / Miss / Timeout |
| manager | subscribes, publishes | `/neuroevent` (`event_topic`) | [`NeuroEvent`](messages.md#neuroevent) | writes the phases of the trials, hears the outcome |
| manager (Synchronous plugin) | publishes | `/protocol_ended` | `std_msgs/Empty` | end of the protocol (`transient_local`) |
| feedback | subscribes | `/control_feedback/probabilities` (`control_topic`) | [`NeuroControl`](messages.md#neurocontrol) | the values and the thresholds to draw |
| feedback | subscribes | `/neuroevent` (`event_topic`) | [`NeuroEvent`](messages.md#neuroevent) | the phases (manager) and the outcome (control): fixation, cue, boom |
| feedback | publishes | `/neuroevent` | [`NeuroEvent`](messages.md#neuroevent) | display events, only with `publish_display_events` |
| recorder | subscribes | `/neurodata`, `/neurodata_info`, `/neuroevent` | [`NeuroFrame`](messages.md#neuroframe), [`NeuroFrameInfo`](messages.md#neuroframeinfo), [`NeuroEvent`](messages.md#neuroevent) | what to write |
| visualizer | subscribes | `/acquisition/neurodata` (selectable) | [`NeuroFrame`](messages.md#neuroframe) | scope |

!!! note "Which processing plugin runs depends on the decoder"
    The `Welch` plugin feeds the classic decoders and the `Buffer` plugin feeds the deep-learning ones: a pipeline uses one of
    them between the filters and the decoder, not both. See [Processing](../packages/processing/index.md).

!!! note "Defaults vs launch files"
    The integrator defaults (`/prediction`, `~/control`) differ from the topics used in the test launchers
    (`/classification/prediction`, `/integrated/raw`), which set them through parameters. The same happens with the
    features: `/features` is only the **default name** of the input of the decoder (and the default output of every processing plugin, through `processing_node`). The test launchers remap them to one name per kind of feature: `/processing/psd` for the classic
    decoders (Welch) and `/processing/buffered_features` for the deep-learning ones (buffer). Always check
    `ros2 topic list` and `ros2 node info` on a running system.

## Services

| Node | Service | Type | Purpose |
|---|---|---|---|
| acquisition | `~/start`, `~/stop`, `~/quit` | `std_srvs/Empty` | control the device |
| integrator | `reset` (relative name, so `/reset`) | `std_srvs/Empty` | reset the integrated values to 1/K |
| control | client of the integrator reset (`reset_service`, default `/reset`) | `std_srvs/Empty` | ask for a reset (the Feedback plugin, protocol `control`) |

## Useful commands

```bash
ros2 topic list -t                      # topics and their types
ros2 topic hz /acquisition/neurodata    # frame rate
ros2 topic echo /neuroevent             # watch the events
ros2 node info /control                 # publishers, subscribers, services of a node
ros2 param list /filters                # parameters of a node
```

---

**Next:** [Protocols: control, manager and feedback](protocols.md) · [back to the Concepts menu](index.md)
