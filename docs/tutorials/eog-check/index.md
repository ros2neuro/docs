# Detect eye blinks (EOG)

Eye blinks and eye movements produce large electrical deflections, the electro-oculogram (EOG), that the
frontal EEG electrodes (**Fp1** and **Fp2**, just above the eyes) pick up much more strongly than anything the
brain does. In a BCI they matter twice: they contaminate the signal, and a trial in which the subject blinked
is often better discarded.

**Goal.** Write a node that **detects blinks on Fp1 and Fp2** and publishes them as events (`Blink` and its end) on `/neuroevent`. You also get a small simulator,
so you can run everything **without hardware** and without frontal electrodes, and see one event pair for every blink.

**You will learn**

- why a blink is easy to recognise on Fp1/Fp2 and how to detect it sample by sample;
- how to separate the signal from slow drifts with a baseline, and avoid false events with hysteresis;
- how to time-stamp an event with the exact sample that caused it;
- how this ties in with the stack: the blink is a `NeuroEvent` on `/neuroevent` (id `1024`, and `1024 + 32768` for its end), so the
  [recorder](../../packages/recorder/index.md) saves it next to the signal with no change.

**You need** the [power threshold tutorial](../power-threshold-event/index.md): this one builds on the same ideas. About 30 minutes.

The complete package is in the repository, under `docs/tutorials/eog-check/tutorial_eog_check/`. The page includes its files, so the code below is the code that builds.

## 1. What a blink looks like

A blink is a deflection of 100 to 300 µV that lasts about 200 to 400 ms. It has three properties that make it
detectable:

- it is **large** compared with the EEG (tens of µV);
- it is strongest on **Fp1 and Fp2**, with the **same polarity** on both (the eyelid moves both eyes together);
- it is much smaller on the central channels, where the motor rhythms are recorded.

So the mean of Fp1 and Fp2 is a good blink signal: it keeps the common-mode blink and averages out the
independent noise of the two electrodes.

!!! note "Eye movements"
    A horizontal eye movement has *opposite* polarity on the two sides, so it shows up in the difference of two
    lateral channels (F7 and F8, or the dedicated EOG channels) rather than in Fp1 and Fp2. This tutorial detects
    blinks. See the exercises for the next step.

## 2. The plan

```mermaid
flowchart LR
    ACQ["acquisition<br/>NeuroFrame (EEG with Fp1, Fp2)"] --> N["eog_blink node"]
    N -->|"Blink 1024<br/>Blink Off 33792"| EV["/neuroevent"]
    EV --> YOU["a node of yours<br/>(optional)"]
    EV --> REC[recorder]
```

For every sample the node:

1. takes the mean of the frontal channels;
2. subtracts a slow **baseline** that follows the signal (so offsets and drifts do not matter);
3. starts a blink when the difference reaches a threshold, and ends it when it stays low for a short time;
4. publishes the event, stamped with the time of that sample.

As in the previous tutorial, the algorithm is in a header with no ROS code, so it can be tested on its own.

## 3. Package layout

```text
tutorial_eog_check/
├── CMakeLists.txt
├── package.xml
├── include/tutorial_eog_check/BlinkDetector.h   # the algorithm, no ROS
├── src/eog_blink_node.cpp                       # the detector node
├── src/fake_eog_node.cpp                        # a blink simulator for the demo
├── test/test_blink_detector.cpp
├── config/eog_blink.yaml
└── launch/eog_demo.launch.xml
```

## 4. The detector, step by step

We write `BlinkDetector`: a class that receives **one number per sample** (the mean of Fp1 and Fp2) and says when a blink starts and ends. It has no ROS in it.

**The state.** The constructor turns times into samples. `baseline_tau_s` sets how slowly the baseline follows the signal, `release_s` how long the signal must stay quiet
before the blink is over:

```cpp title="include/tutorial_eog_check/BlinkDetector.h"
--8<-- "eog-check/tutorial_eog_check/include/tutorial_eog_check/BlinkDetector.h:constructor"
```

**One sample in, one decision out.** Three details make it robust:

- **Baseline.** A one-pole low-pass (`baseline_tau_s`, 2 s) follows the signal. The detector looks at the *deviation* from it, so a constant offset (the test uses 5000 µV) or a slow
  drift is not a blink. The baseline starts at the first sample to avoid a transient at startup.
- **Frozen baseline during a blink.** While a blink is open the baseline stops moving. Otherwise it would follow the blink and the deviation would shrink before the blink is over.
- **Hysteresis and release time.** The blink starts at `threshold`, but it ends only when the deviation stays under `threshold * hysteresis` for `release_s`. The waveform of a blink
  crosses zero and has ripples, and without this rule one blink would produce several events.

The detector uses the absolute value, because depending on the reference a blink can be positive or negative.

```cpp
--8<-- "eog-check/tutorial_eog_check/include/tutorial_eog_check/BlinkDetector.h:process"
```

??? example "The complete header"
    ```cpp
    --8<-- "eog-check/tutorial_eog_check/include/tutorial_eog_check/BlinkDetector.h"
    ```

## 5. The node, step by step

The node is the thin ROS layer: it turns frames into the stream of numbers the detector wants, and the detector's answers into events.

**Parameters and topics.** Everything has a default, so the node works without a YAML file. The threshold is in the unit of the signal (µV):

```cpp title="src/eog_blink_node.cpp"
--8<-- "eog-check/tutorial_eog_check/src/eog_blink_node.cpp:parameters"
```

```cpp
--8<-- "eog-check/tutorial_eog_check/src/eog_blink_node.cpp:topics"
```

**Find the block and the frontal channels.** `channels: ["Fp1", "Fp2"]` is resolved once from `sensor.labels`. If a label is missing the node says so and does nothing, instead of silently
reading the wrong channel. The detector is created at the first frame, because only then do we know the sampling rate, so the node works at any rate:

```cpp
--8<-- "eog-check/tutorial_eog_check/src/eog_blink_node.cpp:find"
```

```cpp
--8<-- "eog-check/tutorial_eog_check/src/eog_blink_node.cpp:resolve"
```

**One value per sample.** The value of channel `c` at sample `s` is `sensor.data[s * channels + c]` (sample-major). The node averages the frontal channels for every sample:

```cpp
--8<-- "eog-check/tutorial_eog_check/src/eog_blink_node.cpp:average"
```

**Ask the detector, and stamp the event with the sample that caused it.** Unlike the previous tutorial, the event is stamped with `frame.header.stamp + s / samplerate`, the time of the
sample that triggered it. A blink then lines up with the signal in the recorded file.

```cpp
--8<-- "eog-check/tutorial_eog_check/src/eog_blink_node.cpp:detect"
```

```cpp
--8<-- "eog-check/tutorial_eog_check/src/eog_blink_node.cpp:publish"
```

**Event ids.** `1024` is the id this tutorial chooses for *Blink*: it is not an id of the stack, and its end follows the *Off* convention, `1024 + 32768`
([event codes](../../concepts/protocols.md#event-codes)). No node of the stack reacts to it: the recorder saves it, and a node of yours can listen to it (for example to discard a trial
with a blink).

```cpp
--8<-- "eog-check/tutorial_eog_check/src/eog_blink_node.cpp:count"
```

??? example "The complete node"
    ```cpp
    --8<-- "eog-check/tutorial_eog_check/src/eog_blink_node.cpp"
    ```

## 6. The simulator

We need something to detect. Real recordings are not always at hand, and the test GDF of the workspace has no frontal electrodes. The package
includes a small simulator:

```cpp title="src/fake_eog_node.cpp"
--8<-- "eog-check/tutorial_eog_check/src/fake_eog_node.cpp"
```

It publishes five EEG channels (Fp1, Fp2, C3, Cz, C4) with a 10 Hz rhythm and noise, and a Gaussian blink every
four seconds, large and in phase on Fp1/Fp2 and ten times smaller elsewhere. It is a useful pattern in its own
right: **a tiny publisher with known content lets you test a node without any hardware**.

## 7. The test

Before running anything, check the detector on signals whose answer we know.

```cpp title="test/test_blink_detector.cpp"
--8<-- "eog-check/tutorial_eog_check/test/test_blink_detector.cpp"
```

The tests cover one blink giving exactly one start and one end, a deflection that is too small, a negative blink,
a large constant offset, and two blinks in a row.

## 8. Build files

```xml title="package.xml"
--8<-- "eog-check/tutorial_eog_check/package.xml"
```

```cmake title="CMakeLists.txt"
--8<-- "eog-check/tutorial_eog_check/CMakeLists.txt"
```

## 9. Build and test

```bash
colcon build --packages-select tutorial_eog_check
colcon test  --packages-select tutorial_eog_check
colcon test-result --verbose
source install/setup.bash
```

If the package lives outside `src/`, add its path: `colcon build --paths path/to/tutorial_eog_check`.

## 10. Run it

```yaml title="config/eog_blink.yaml"
--8<-- "eog-check/tutorial_eog_check/config/eog_blink.yaml"
```

```xml title="launch/eog_demo.launch.xml"
--8<-- "eog-check/tutorial_eog_check/launch/eog_demo.launch.xml"
```

Start the demo:

```bash
ros2 launch tutorial_eog_check eog_demo.launch.xml
```

The detector reports one blink every four seconds:

```text
[eog_blink]: Using 2 frontal channel(s)
[eog_blink]: blink 1
[eog_blink]: blink 2
[eog_blink]: blink 3
```

In a second terminal look at the events:

```bash
ros2 topic echo /neuroevent --field event_id
```

```text
1024        blink starts
33792       blink ends (1024 + 32768)
1024
33792
```

Each blink lasts a bit more than a third of a second between its two events, which is the width of the waveform
the detector is following.

## 11. Use it on real data

- **Real electrodes.** Remap the input to your acquisition or filter output:
  `ros2 run tutorial_eog_check eog_blink_node --ros-args --params-file config/eog_blink.yaml -r /neurodata:=/acquisition/neurodata`.
  Make sure `channels` use the labels of your cap (`ros2 topic echo --once /acquisition/neurodata_info`).
- **Choose the threshold.** Ask the subject to blink a few times and look at the size of the deflection in the
  [visualizer](../../packages/visualizer.md). Set the threshold to about half of the blink amplitude, well above
  the amplitude of the EEG.
- **Filtering first.** Do not high-pass the signal above about 1 Hz before this node: it would distort the slow
  blink waveform. Detect blinks on the raw or lightly filtered signal, and filter afterwards for the BCI chain.
- **Record and reject.** Run the [recorder](../../packages/recorder/index.md) on `/neuroevent` and the blinks are in the
  GDF file. In an offline analysis they tell you which trials to discard.
- **Check the electrodes.** If no blink is ever detected, the frontal electrodes may have a bad contact. Asking
  the subject to blink is a quick way to check that Fp1 and Fp2 are recording.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `Channel 'Fp1' is not in sensor 'EEG'` | the labels of the stream differ (`Fp1` vs `FP1`), or the cap has no frontal channels |
| no blink is detected | the threshold is above the blink amplitude: print the deviation or lower it |
| false blinks | the threshold is too low, or the signal has fast artifacts: raise it and the `release_s` |
| several events for one blink | `release_s` is too short or `hysteresis` too close to 1 |
| a blink is missed right after another | the previous one is still open: lower `release_s` |

## Exercises

1. Detect **horizontal eye movements**: use two lateral channels and look at their difference, which changes sign
   with the direction of the gaze.
2. Count the blinks per minute and log the rate every 10 seconds. A high rate is a sign of fatigue.
3. Add a service `reset` that clears the blink count, as the integrator does.
4. Combine this node with the [power threshold](../power-threshold-event/index.md) node: publish an event only
   when a blink *and* a rise of the frontal power occur together.

## What you learned

- a blink is a large deflection with the same polarity on Fp1 and Fp2, so their mean is a good blink signal;
- a baseline and a hysteresis turn a noisy signal into clean start and end events;
- an event can be stamped with the exact sample that caused it, so it lines up with the recording;
- a tiny publisher with known content lets you test a node without any hardware.

Next: [Feedback in virtual reality (WebXR and Unity)](../vr-feedback/index.md).
