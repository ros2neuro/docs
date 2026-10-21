# Architecture

![ROS2neuro architecture](../assets/architecture.svg)

ROS2neuro is a chain of ROS 2 nodes. Each node subscribes to the output of the previous one, does one job and
publishes its result. A few nodes (recorder, visualizer) sit beside the chain and only listen.

## The layers

| Layer | Package(s) | Job | Output |
|---|---|---|---|
| Acquisition | [`ros2neuro_acquisition`](../packages/acquisition/index.md) + one backend plugin | read samples from a device or a file | `NeuroFrame`, `NeuroFrameInfo` |
| Filters | [`ros2neuro_filters`](../packages/filters/index.md) + filter plugins | clean the signal with a configurable chain | `NeuroFrame` |
| Processing | [`ros2neuro_processing_spectral`](../packages/processing/spectral.md) (Welch) **or** [`ros2neuro_processing_buffer`](../packages/processing/buffer.md): the decoder decides | turn the filtered frames into the feature the decoder reads (a PSD, or a window of the signal) | `NeuroFeature` |
| Decoder | [`ros2neuro_decoder`](../packages/decoder/index.md) + one model plugin | classify a feature | `NeuroPrediction` |
| Integrator | [`ros2neuro_integrator`](../packages/integrator/index.md) + one plugin | smooth the predictions over time | `NeuroControl` |
| Manager | [`ros2neuro_manager`](../packages/manager/index.md) + one protocol plugin | run calibration, evaluation or control; emit events | `NeuroControl` (flow), `NeuroEvent` |
| Feedback | [`ros2neuro_feedback`](../packages/feedback/index.md) + one drawing plugin | show the state to the subject | a window |
| Recorder | [`ros2neuro_recorder`](../packages/recorder/index.md) + one format plugin | write data and events to a file | GDF / BDF |
| Visualizer | [`ros2neuro_visualizer`](../packages/visualizer.md) | scope of the signals | a window |

[`ros2neuro_msgs`](../packages/msgs-data.md#ros2neuro_msgs) defines the messages exchanged between all of them, [`ros2neuro_data`](../packages/msgs-data.md#ros2neuro_data) holds the in-memory C++
types used inside plugins before converting to messages.

### The processing stage depends on the decoder

Most layers have one job and, when there are several implementations, a plugin selects one. **Processing** is different: it
is the stage that prepares the data *for the decoder*, so what runs depends on the decoder. There are two chains in the stack:

```mermaid
flowchart LR
    FIL["filters"] --> WEL["welch_node<br/>PSD"] --> CLA["decoder<br/>LDA, QDA, SVM, Gaussian"]
    FIL --> BUF["buffer_node<br/>window of the signal"] --> DL["decoder_py<br/>deep learning"]
```

- the **classic decoders** read a power spectrum: the processing is the Welch PSD ([`ros2neuro_processing_spectral`](../packages/processing/spectral.md));
- the **deep-learning decoders** read a window of the filtered signal: the processing is the buffer
  ([`ros2neuro_processing_buffer`](../packages/processing/buffer.md)).

The spectral code is also used by the visualizer, which computes its spectrum itself. There is **no base class for
processing**: each one is an ordinary node that reads a `NeuroFrame` and publishes a `NeuroFeature`, so new ones (a Hilbert
envelope, Riemannian features...) can be added by anyone. See [Processing](../packages/processing/index.md).

## Three ideas that explain the design

**1. Everything is a node, everything is replaceable.**
Nodes are connected only by topics, so any stage can be swapped, started on another machine, replayed from a
file or observed with `ros2 topic echo`.

**2. Behaviour comes from plugins.**
A generic node (for example the acquisition node) knows how to talk ROS but not how to talk to a specific
amplifier. The amplifier driver is a plugin selected by a parameter. See [Plugins](plugins.md).

**3. The protocol is separate from the signal chain.**
The signal chain ends at the integrator, which knows nothing about trials or cues. The **manager** adds the
experimental protocol on top and the **feedback** is passive: it only draws what the manager says. See
[Protocols](protocols.md).

## Closing the loop

The loop of a BCI task is:

1. the subject produces brain activity, the amplifier samples it;
2. the chain acquisition → filters → processing → decoder → integrator turns it into class probabilities;
3. the manager normalises them, decides the outcome of the trial and forwards the values to the feedback;
4. the feedback shows them, and the subject adapts.

Two side channels complete the picture: the manager publishes **events** (`/neuroevent`) that the recorder
stores next to the signal, and it can ask the integrator to **reset** through a ROS service.

## Running without hardware

Replacing the amplifier with a GDF file ([`ros2neuro::acquisition::XDFDevice`](../packages/acquisition/xdf.md)) or the dummy generator
([`ros2neuro::acquisition::DummyDevice`](../packages/acquisition/dummy.md)) leaves the rest of the chain untouched. The
[`ros2neuro_devel_test`](../packages/devel-test.md) launchers use this to start a full pipeline, from the
file to the wheel or the bars, on a laptop. The first tutorial,
[Hardware-free pipeline](../tutorials/hardware-free-pipeline/index.md), walks through it.
