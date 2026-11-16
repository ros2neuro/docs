# Decoder converters

!!! info ""
    Package: [`ros2neuro_decoder_converters`](https://github.com/ros2neuro/ros2neuro_decoder_converters) · part of [Decoder](index.md)

Offline tools that convert decoder models trained elsewhere into the ROS2neuro format. Today it converts a Matlab SMR Gaussian decoder (`.mat`) into a `.r2nd` model plus a `manifest.yaml`, through a small graphical tool.

| | |
|---|---|
| **Layer** | Decoder (tools) |
| **Kind** | Offline tool (not a node of the running pipeline) |
| **Reads** | a Matlab `.mat` model |
| **Publishes** | a `.r2nd` model and its `manifest.yaml` |
| **Run** | `ros2 run ros2neuro_decoder_converters r2n_decoder_converter` |

<!-- interfaces -->
## Dependencies

- **ROS 2 packages**: none for the converter; the check in `test/` runs the pipeline ([`ros2neuro_acquisition`](../acquisition/index.md) with the XDF plugin,
  [`ros2neuro_filters`](../filters/index.md) with the Laplacian, [`ros2neuro_processing_spectral`](../processing/spectral.md), [`ros2neuro_decoder`](index.md) with the Gaussian plugin) and needs `rclpy`, `PyYAML` and `mne`
- **External libraries**:
    - `PyQt5`, `numpy`, `scipy`: the graphical tool and the reading of the Matlab file (`python3-pyqt5`, `python3-numpy`, `python3-scipy`)

## Messages and topics

Messages used:

- none: an offline tool, it does not use the ROS graph

<!-- /interfaces -->
The main user entry point is the general converter GUI:

```bash
ros2 run ros2neuro_decoder_converters r2n_decoder_converter
```

Current converters:

- `Gaussian`: Matlab SMR Gaussian decoder `.mat` to `.r2nd` plus `manifest.yaml`

The GUI is implemented with PyQt5 and supports native file drag-and-drop, Browse, and Paste Path input selection.

### Feature unit

The Gaussian classifier works on the natural logarithm of the Welch PSD, which is what the `Welch` plugin of [`ros2neuro_processing_spectral`](../processing/spectral.md) publishes (`ln(power/Hz)`).
The converter writes this unit in the model (field **Feature unit** of the GUI, or `--feature-unit` of the command-line backend `converters/gaussian.py`), and the decoder refuses a feature with another
unit: a model converted with a different one (for example the old `dB/Hz`) has to be converted again.

### What it converts, and what it does not

- It converts **only the Matlab SMR Gaussian classifier** (a `.smr.mat` with a top-level `settings` struct, with `settings.bci.smr.gau.M` and `.C`). There is no
  converter for LDA, QDA or SVM, and none for classifiers of other toolboxes: a classifier from elsewhere works only if its `.mat` has the same `settings`
  structure (see below).
- Centers and diagonal covariances are copied unchanged, with uniform priors.
- `settings.modules.smr.options.classification.norm` (division of the features by `sum(abs(.))`) is **not** carried: a classifier trained with `norm = 1`
  would not give the same output.
- The spatial filter is not part of the model: the Laplacian matrix is only copied as metadata in the `training` section of the manifest, and the filter
  chain, the window, the PSD window and overlap, and the frequencies of the pipeline must be set to the same values the classifier was trained with.

### What we expect from the classifier

The converter copies numbers: it does not train the classifier and it cannot know how it was trained. The result is right when the classifier and the
pipeline that will feed it agree on the points below. The decoder checks what it can: that the model is consistent when it loads it, and the axes of every
feature it receives (point 3), stopping with a clear message if they differ. It cannot check the order of the features (point 2), the processing before it
(point 4) or the classes (point 5), so those are yours to set.

1. **The model.** A Gaussian classifier with diagonal covariances and prototypes: centers `M` and variances `C` of shape `[class, prototype, feature]`,
   all variances positive. The class probabilities are computed in the log domain and the priors are uniform (the priors of the training are not carried).
   A classifier trained with the `norm` option (features divided by `sum(abs(.))`) is not supported: the decoder would give another output.
2. **The features.** The (log) Welch PSD, a tensor `[channels, frequency]`, of which the classifier uses a subset chosen channel by channel (`bands`).
   The third axis of `M` and `C` must follow the order the converter reads `bands`: the EEG channels in the order of `acq.channel_lbl`, and inside a
   channel the frequencies in the order they are listed. If your trainer orders the features differently, reorder `M` and `C` before converting.
3. **The axes.** Every selected frequency must be **exactly** one of `modules.smr.psd.freqs` (the converter compares the numbers, not the nearest one),
   and the PSD that reaches the decoder must have the same channel labels in the same order, and the same frequencies, as the model. The decoder compares them.
4. **The processing before the decoder.** The model carries these only as metadata (`training` section of the manifest), so set the pipeline to the values of the
   training:

   | In the training | Where it is set in ROS2neuro |
   |---|---|
   | sample rate `acq.sf` | the acquisition |
   | analysis window `modules.smr.win.size`, shift `.shift` | `processing.params.buffer` of `Welch` (samples) and the frame size of the acquisition (shift = frame / sample rate) |
   | PSD window and overlap `modules.smr.psd.win`, `.ovl` (fractions of a second and of the window) | `processing.params.wlength`, `.overlap`, `.wtype` of `Welch` |
   | PSD frequencies `modules.smr.psd.freqs` | `processing.params.frequencies` of `Welch` |
   | spatial filter (DC, CAR, Laplacian) | the filter chain ([`ros2neuro_filters`](../filters/index.md)) |

5. **The classes.** The first axis of `M` is in the order of `bci.smr.taskset.classes`. The output fields of the decoder are those codes as text, and the
   `classes` of the manager, control and feedback use the same codes (or `input_fields` of control maps the codes of the model onto them).

The way to know that all of this is right for **your** classifier is to run the check below on it: it replays a recording through the ROS 2 pipeline and compares
the probabilities with the Matlab classifier, window by window. On the example of the package (16 channels, 13 selected features, 2 classes, 3975 windows) the
decision is the same in all of them and the probabilities differ by about 1e-5.

### Checking a converted classifier against Matlab

`test/` holds a check that the converted classifier gives the same output in ROS 2 as in Matlab: `check_decoder.launch.py` replays a GDF through
the pipeline (Laplacian filter, Welch, decoder) and `record_features.py` saves the PSD, the features the classifier uses and its probabilities in a CSV;
`check_decoder.m` repeats the processing in Matlab, compares and plots. In the ROS 2 container, with the workspace sourced:

```bash
ros2 launch ros2neuro_decoder_converters check_decoder.launch.py          # the example of this package
ros2 launch ros2neuro_decoder_converters check_decoder.launch.py manifest:=<manifest.yaml> \
    mat_file:=<classifier.smr.mat> gdf_file:=<recording.gdf> output_csv:=<ros_features.csv>
```

Without arguments it uses the example installed with the package (`share/ros2neuro_decoder_converters/test_data`: a classifier, the model converted
from it and a GDF; `test/data` in the sources). It replays the GDF in real time and ends by itself, writing `ros_features.csv` in the current
folder (`output_csv:=...` to change it). Then in Matlab run `check_decoder(mat_file, gdf_file, 'ros_features.csv')`, or just `check_decoder` from
`test/` with the example. The model must have been converted with the unit of the Welch node (`ln(power/Hz)`, the default).

## Gaussian `.mat` Input

The Gaussian converter expects a Matlab `.mat` file produced by the SMR Gaussian trainer with a top-level `settings` struct. The parser currently reads this structure:

```text
settings
  info
    subject                         # Required unless overridden in the GUI
    basename                        # Optional metadata
    date                            # Optional metadata
    experimenter                    # Optional metadata
    hostname                        # Optional metadata
  acq
    channel_lbl                     # Required, labels for EEG channels
    sf                              # Optional metadata, sample rate
    channels_eeg                    # Optional metadata
    channels_exg                    # Optional metadata
    channels_tri                    # Optional metadata
  modules
    smr
      psd
        freqs                       # Required, PSD frequency axis
        ovl                         # Optional metadata, overlap ratio
        win                         # Optional metadata, window ratio
      gau
        sharedcov                   # Required, covariance mode flag/string
        epochs                      # Optional metadata
        somunits                    # Optional metadata
        micov                       # Optional metadata
        mimean                      # Optional metadata
        terminate                   # Optional metadata
        th                          # Optional metadata
      win
        size                        # Optional metadata, analysis window seconds
        shift                       # Optional metadata, shift seconds
      options
        prep
          dc                        # Optional metadata
          car                       # Optional metadata
          laplacian                 # Optional metadata
      laplacian                     # Optional metadata, Laplacian matrix
  bci
    smr
      bands                         # Required, selected frequencies per channel
      gau
        M                           # Required, Gaussian centers
        C                           # Required, Gaussian diagonal covariances
      taskset
        classes                     # Required, class ids
      trace
        Paths                       # Optional metadata, source dataset paths
```

Required tensor shapes:

- `settings.bci.smr.gau.M`: `[n_classes, n_prototypes, n_features]`
- `settings.bci.smr.gau.C`: same shape as `M`
- `settings.bci.smr.bands`: one entry per EEG channel; each entry lists selected PSD frequencies for that channel
- `settings.modules.smr.psd.freqs`: frequency axis containing every frequency referenced by `bands`
- `settings.bci.smr.taskset.classes`: one class id per class in `M`

Validation rules:

- `M` and `C` must have identical 3D shapes.
- The number of selected features from `bands` must match `M.shape[2]`.
- Every selected frequency in `bands` must exist in `modules.smr.psd.freqs`.
- All covariance values in `C` must be strictly positive.
- The number of task classes must match `M.shape[0]`.

The converter writes:

- `.r2nd` binary model with decoder type [`ros2neuro::decoder::Gaussian`](gaussian.md)
- `manifest.yaml` with the input contract, selected features, output fields, and available training metadata

## Internal Layout

```text
scripts/
  r2n_decoder_converter                 # Main GUI entry point
  r2n_decoder_converters/
    app.py                              # General GUI container
    registry.py                         # Available decoder converter registry
    converters/
      gaussian.py                       # Gaussian conversion backend and CLI parser
    gui/
      gaussian.py                       # Gaussian GUI panel used by the main app
```

Only `r2n_decoder_converter` should be installed as an executable program. Decoder-specific GUI panels live under `r2n_decoder_converters/gui/` and are opened through the main GUI.

## Adding A Converter

1. Add the backend module:

   ```text
   scripts/r2n_decoder_converters/converters/<decoder>.py
   ```

   Keep file parsing, validation, `.r2nd` writing, and manifest writing here. Backend modules can expose helper functions for tests or future CLI support, but they should not be installed as standalone ROS entry points.

2. Add the GUI panel:

   ```text
   scripts/r2n_decoder_converters/gui/<decoder>.py
   ```

   The GUI class is a PyQt5 `QWidget` built without arguments (the main window puts it in a tab):

   ```python
   class MyDecoderConverterGui(QWidget):
       def __init__(self) -> None:
           super().__init__()
           ...
   ```

   Do not install this GUI file as a standalone executable.

3. Register the converter in `scripts/r2n_decoder_converters/registry.py`:

   ```python
   from r2n_decoder_converters.gui.my_decoder import MyDecoderConverterGui

   def _my_decoder_gui() -> MyDecoderConverterGui:
       return MyDecoderConverterGui()

   CONVERTERS = (
       ...,
       DecoderConverter(
           key="my_decoder",
           label="My Decoder",
           description="External model format to ros2neuro .r2nd",
           create_gui=_my_decoder_gui,
       ),
   )
   ```

4. Keep `CMakeLists.txt` focused on the single public entry point:

   ```cmake
   install(PROGRAMS
     scripts/r2n_decoder_converter
     DESTINATION lib/${PROJECT_NAME}
   )
   ```
