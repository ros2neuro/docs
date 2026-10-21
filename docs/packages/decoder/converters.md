# Decoder converters

!!! info ""
    Package: [`ros2neuro_decoder_converters`](https://github.com/ros2neuro/ros2neuro_decoder_converters) · part of [Decoder](index.md)

Offline converters for `ros2neuro` decoder models.

The main user entry point is the general converter GUI:

```bash
ros2 run ros2neuro_decoder_converters r2n_decoder_converter
```

Current converters:

- `Gaussian`: Matlab SMR Gaussian decoder `.mat` to `.r2nd` plus `manifest.yaml`

The GUI is implemented with PyQt5 and supports native file drag-and-drop, Browse, and Paste Path input selection.

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

   The GUI class should accept a parent widget:

   ```python
   class MyDecoderConverterGui:
       def __init__(self, root: tk.Misc) -> None:
           ...
   ```

   Do not install this GUI file as a standalone executable.

3. Register the converter in `scripts/r2n_decoder_converters/registry.py`:

   ```python
   from r2n_decoder_converters.gui.my_decoder import MyDecoderConverterGui

   def _my_decoder_gui(parent: tk.Misc) -> MyDecoderConverterGui:
       return MyDecoderConverterGui(parent)

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
