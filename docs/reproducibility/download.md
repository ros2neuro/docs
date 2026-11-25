# Download and use the functions

## MATLAB

!!! success "Download"
    **[ros2neuro_matlab.zip](ros2neuro_matlab.zip)**: the `r2n_*` functions, one file each (the same as the `matlab/` folder of [`ros2neuro_devel_test`](https://github.com/ros2neuro/ros2neuro_devel_test/tree/main/matlab)).

Or take them from the repository, together with the tests that check them:

```bash
git clone https://github.com/ros2neuro/ros2neuro_devel_test.git
```

You need **MATLAB R2019b or newer with the Signal Processing Toolbox** (`butter`, `filter`, `pwelch`, `hann`, ...). Reading a GDF needs [BIOSIG](https://biosig.sourceforge.net) (`sload`).

```matlab
addpath('ros2neuro_matlab');                   % the unzipped folder, or ros2neuro_devel_test/matlab

x   = single(eeg);                             % samples x channels
y   = r2n_butterworth(x, 'high', 4, 1, 512);   % high-pass 1 Hz, as the Butterworth filter plugin does
y   = r2n_laplacian(y, '0 0 1 0 0; 2 3 4 5 6; 7 8 9 10 11; 12 13 14 15 16');
psd = r2n_welch(double(y(end-511:end, :)), struct('fs', 512, 'length', 256, 'overlap', 128, 'window', 'hamming', 'freqs', 4:2:48));
m   = r2n_qda_read('qda_test_gdf.r2nd');       % the model the decoder node loads
p   = r2n_qda_predict(m, psd(:)');             % its probabilities
```

Every function says in its header which plugin it reproduces, what it expects and what it returns. The replication of each plugin, with its code, is in the **MATLAB replication** section of its page ([filters](../packages/filters/index.md), [processing](../packages/processing/index.md), [decoders](../packages/decoder/index.md), [integrators](../packages/integrator/index.md)); all of them are in [Reproducibility in MATLAB](matlab.md).

### Replay a whole run

The tests of [`ros2neuro_devel_test`](../packages/devel-test.md) are the worked examples: each `check_*.m` is one file that reads a recorded run, redoes every step with these functions and compares. The complete pipelines are in the `pipeline/` folder:

| Pipeline | Folder | Check |
|---|---|---|
| raw → Laplacian → band-pass → Welch → QDA → integrator → control | `pipeline/qda/` | `check_pipeline_qda` |
| the same with an LDA | `pipeline/lda/` | `check_pipeline_lda` |
| raw → 9 band-pass chains → FBCSP → LDA → integrator → control | `pipeline/fbcsp/` | `check_pipeline_fbcsp` |

## Python

!!! success "Download"
    **[check_pipeline_dl.py](files/python/check_pipeline_dl.py)**: the whole deep-learning pipeline replayed in Python and compared with the run (also in `pipeline/dl/` of [`ros2neuro_devel_test`](https://github.com/ros2neuro/ros2neuro_devel_test/tree/main/pipeline/dl)).

It needs `numpy`, `scipy`, `matplotlib`, `torch`, `braindecode` and `pyyaml` (the Docker image and the `ros2neuro` container have them). See [Reproducibility in Python](python.md).
