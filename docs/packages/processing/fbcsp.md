# Processing FBCSP

!!! info ""
    Package: [`ros2neuro_processing_fbcsp`](https://github.com/ros2neuro/ros2neuro_processing_fbcsp) · part of [Packages](../index.md)

Filter-bank CSP (FBCSP) features: a plugin of [`ros2neuro_processing`](index.md) (`ros2neuro::processing::Fbcsp`) that reads one **already band-passed** stream per band, projects every band with the CSP filters of a trained model and publishes the log-variance of the components as a `NeuroFeature` `[bands, components]`. The band-pass is not done here: there is one filter chain (`filter_chain_node`) per band in front of it. It is the processing stage of the FBCSP models trained with `mi_training`; the classifier is the existing [`ros2neuro_decoder_sklearn`](../decoder/sklearn.md).

<!-- at-a-glance -->
| | |
|---|---|
| **Layer** | Processing |
| **Kind** | Plugin of [`ros2neuro_processing`](index.md) (pluginlib class `ros2neuro::processing::Fbcsp`, input kind `FrameSet`) and a C++ library (`FbcspCore`) |
| **Reads** | one `NeuroFrame` topic per band (`input_topics`, in the order of `bands`; the last segment of each is `band_<lo>_<hi>`), through the processing node |
| **Publishes** | `NeuroFeature` (`/features`, parameter `output_topic`; type `TYPE_MATRIX`, shape `[bands, components]`) through the processing node |
| **Run** | in the YAML of the processing node: `processing.plugin: ros2neuro::processing::Fbcsp`, `input_topics`, `processing.params.*` (`ros2 run ros2neuro_processing processing_node --ros-args -r __node:=fbcsp --params-file <file>.yaml`) |
| **Used by** | [`ros2neuro_decoder_sklearn`](../decoder/sklearn.md) (manifest `input.type: NeuroFeature::TYPE_MATRIX`) |
<!-- /at-a-glance -->

<!-- interfaces -->
## Dependencies

- **ROS 2 packages** (build and run): `pluginlib`, `rclcpp`, [`ros2neuro_msgs`](../msgs-data.md#ros2neuro_msgs), [`ros2neuro_processing`](index.md)
- **At run time**, in front of it: [`ros2neuro_filters`](../filters/index.md) (`filter_chain_node`, one per band) with [`ros2neuro_filters_butterworth`](../filters/butterworth.md)
- **External libraries**: none (`yaml-cpp` is used by the tests only)

## Messages and topics

Default node name: `processing` (the node of [`ros2neuro_processing`](index.md); the launch file names it `fbcsp`, and that name is the section of the parameter file).

| | Topic | Type | Changed by |
|---|---|---|---|
| subscribes | the `input_topics`, one per band (for example `/processing/band_8_12`, `/processing/band_12_16`) | `NeuroFrame` | `input_topics` of the node |
| publishes | `/features` | `NeuroFeature` | `output_topic` of the node |

The feature has type `TYPE_MATRIX`, shape `[bands, components]`, data band-major (`index = band * components + component`, float32), the header of the group of frames, unit `ln(variance fraction)` and two axes: `band` (labels, `"lo-hi"` unless `band_labels` is given) and `component` (labels `c1` ... `cN`).
<!-- /interfaces -->

## Topology: one filter chain per band

```
acquisition -> [filter chain: dc, car, laplacian, ...] -+-> band_8_12  (filter_chain_node: hp 8, lp 12)  --+
                                                        +-> band_12_16 (filter_chain_node: hp 12, lp 16) --+-> Fbcsp -> /features
                                                        +-> band_16_20 ...                               --+
```

- The common preprocessing of the model (DC, CAR, Laplacian, ...) is a normal filter chain, as before (`filter_chain.yaml` written next to the model by `mi_training`).
- Every band has its own `filter_chain_node`: a high-pass at `lo` followed by a low-pass at `hi`, both Butterworth. `mi_training` writes the N chains in `band_chains.yaml`, one section per node, named after the topic of the band (`/band_8_12`, ...). The node publishes on `/processing/band_8_12`.
- The processing node of `Fbcsp` subscribes to the N topics. The frames of the N chains that come from the same acquisition frame have the **same stamp** (`filter_chain_node` copies the header of its input): the processing node groups them by stamp and gives the complete group to the plugin (see [`ros2neuro_processing`](index.md)). It needs a device that stamps every frame: every acquisition plugin (ANT, dummy, eegdev, gUSBamp, LSL, XDF) sets `header.stamp` to the clock of the node when it builds each frame (read in the code; only XDF was run with this).

```xml
<node pkg="ros2neuro_filters" exec="filter_chain_node" name="band_8_12" output="screen">
    <param from="$(var config)/band_chains.yaml"/>
    <remap from="/neurodata" to="/processing/filtered"/>        <!-- the output of the common chain -->
    <remap from="~/filtered" to="/processing/band_8_12"/>
</node>
<!-- ... the same for band_12_16, band_16_20, ... -->
<node pkg="ros2neuro_processing" exec="processing_node" name="fbcsp" output="screen">
    <param from="$(var config)/processing.yaml"/>
</node>
```

`filter_chain_node` does not take `-p input_topic` / `-p output_topic` from the command line (they are already declared): use remaps, as above.

### The names of the topics are the bands

The topic of band *k* must end with `band_<lo>_<hi>` of the band *k* of `bands`, and `input_topics` must list the topics **in the order of `bands`**:

| band | last segment of the topic |
|---|---|
| 8-12 Hz | `band_8_12` |
| 8.5-12 Hz | `band_8p5_12` |
| 12-16.25 Hz | `band_12_16p25` |

The decimal point is written `p`, because a topic name cannot hold `-` or `.`, nor a segment that starts with a digit (`8_12` would not be a valid name). The rest of the topic is free (`/processing/`, a namespace, a remap...). The plugin checks this when the node starts: a topic with another name, or two topics swapped, stops the node with exit code 1 and a message that says which topic was expected where.

!!! warning "What the check does not do"
    The check verifies that the topics are the expected ones, in the expected order, and that none is missing. It cannot verify that the chain behind `band_8_12` really filters 8-12 Hz: that is in the YAML of that chain, and nodes do not ask each other. If the name of the topic and the cutoffs are written by hand in two places, they can be wrong together. That is why `mi_training` writes the chains (`band_chains.yaml`) and the `processing.yaml` of the plugin from the same list of bands.

## Algorithm

For every complete group of frames (one per band, `[samples, channels]`, sample-major, float32, sensor `sensor`):

1. **Checks on the group.** All the frames must have the sensor, `nchannels` channels, the same number of samples, the same sample rate and the same channel labels in the same order (the CSP weights are by position). Otherwise the group is dropped with a warning.
2. **Buffer.** The last `buffer` samples of every band are kept.
3. **CSP.** When the buffer is full, `z = x W^T` with the `components` CSP filters `W` of the band.
4. **Feature.** `v_k` is the population variance (mean removed) of `z_k` over the buffer; the feature of component `k` is `log(max(v_k / sum_j v_j, 1e-12))`, the sum running over the components of the band.

A feature is published for every group once the buffer of every band is full. The band-pass is done upstream, in float32, by [`ros2neuro_filters_butterworth`](../filters/butterworth.md); the training (`mi_training`) filters in double precision with `scipy`: on the reference data of the tests the two give features that differ by less than 2e-7.

## Parameters

Given to the processing node as `processing.plugin: ros2neuro::processing::Fbcsp`, `input_topics` and `processing.params.<name>`. The node itself has `output_topic` (default `/features`) and `processing.name`; `input_topic` is not used (`input_topics` is).

Plugin parameters:

- `feature` (string, default `fbcsp`): name of the published feature
- `sensor` (string, default `EEG`): sensor of the frames to read
- `samplerate` (double): Hz; 0 or absent uses the one of the frames
- `buffer` (int, required): samples of the analysis window
- `bands` (double array, required): `[lo0, hi0, lo1, hi1, ...]` in Hz, `0 < lo < hi < samplerate/2`; they give the names the topics must have
- `band_labels` (string array, optional): one label per band, default `"lo-hi"` (`%g`)
- `nchannels` (int, required): channels of the sensor
- `components` (int, required): CSP components per band
- `filters` (double array, required): `[band][component][channel]`, size `bands * components * nchannels`

and, at the level of the node, `input_topics` (string array, required): one topic per band, in the order of `bands`.

The configuration is validated when the node starts: a wrong one (filters of the wrong size, `lo >= hi`, `buffer < 2`, a band above Nyquist, a parameter with the wrong type such as `buffer: 512.0`, a number of topics different from the number of bands, topics that do not match the bands, ...) prints a clear message and the node exits with code 1.

Example (`config/fbcsp.yaml`, placeholder filters for 4 channels):

```yaml
fbcsp:
  ros__parameters:
    processing.plugin: ros2neuro::processing::Fbcsp
    input_topics: [/processing/band_8_12, /processing/band_12_16]
    processing.params.samplerate: 512.0
    processing.params.buffer: 512
    processing.params.nchannels: 4
    processing.params.components: 2
    processing.params.bands: [8.0, 12.0, 12.0, 16.0]
    processing.params.filters: [1.0, 0.0, 0.0, 0.0,  0.0, 1.0, 0.0, 0.0,
                                1.0, 0.0, 0.0, 0.0,  0.0, 1.0, 0.0, 0.0]
```

## With the Sklearn decoder

The model written by `mi_training` (family ML, feature extractor FBCSP) has `model.skops` + `manifest.yaml`, the `processing.yaml` of this plugin (section `/fbcsp`: `processing.plugin`, `input_topics` and `processing.params.*`), `band_chains.yaml` (the N filter chains of the bands) and `filter_chain.yaml` (the common chain). The manifest declares `input.type: NeuroFeature::TYPE_MATRIX`, the axes `band` (labels) and `component` (labels) and `features.mode: all | selection`; the decoder matches the axes by label, so the order of the bands does not matter. The `input_topics` of `processing.yaml` start with `/processing/`: only the last segment is checked, the rest can be remapped.
