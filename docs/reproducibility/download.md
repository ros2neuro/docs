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

Every function says in its header which plugin it reproduces, what it expects and what it returns. Each function is explained, with its code, in [MATLAB](matlab.md); the tests that use them are in [Packages](packages/index.md) and [Pipeline](pipeline.md).

### Replay a whole run

The tests of [`ros2neuro_devel_test`](packages/index.md) are the worked examples: each `check_*.m` is one file that reads a recorded run, redoes every step with these functions and compares. The complete pipelines are in the `pipeline/` folder:

| Pipeline | Folder | Check |
|---|---|---|
| raw → Laplacian → band-pass → Welch → QDA → integrator → control | `pipeline/qda/` | `check_pipeline_qda` |
| the same with an LDA | `pipeline/lda/` | `check_pipeline_lda` |
| raw → 9 band-pass chains → FBCSP → LDA → integrator → control | `pipeline/fbcsp/` | `check_pipeline_fbcsp` |

## Python

!!! success "Download"
    - **[ros2neuro_python.zip](ros2neuro_python.zip)**: the `r2n_*.py` functions, one file each (the same as the `python/` folder of [`ros2neuro_devel_test`](https://github.com/ros2neuro/ros2neuro_devel_test/tree/main/python)).
    - **[check_pipeline_dl.py](files/python/check_pipeline_dl.py)**: the whole deep-learning pipeline replayed in Python and compared with the run (also in `pipeline/dl/` of [`ros2neuro_devel_test`](https://github.com/ros2neuro/ros2neuro_devel_test/tree/main/pipeline/dl)).

It needs `numpy` and `scipy`; the models need `scikit-learn` and `skops` (scikit-learn) or `torch` and `braindecode` (deep learning), and `pyyaml` (the Docker image and the `ros2neuro` container have them).

```python
import sys; sys.path.insert(0, 'ros2neuro_python')     # the unzipped folder, or ros2neuro_devel_test/python
import numpy as np
from r2n_butterworth import r2n_butterworth
from r2n_welch import r2n_welch
from r2n_qda_read import r2n_qda_read
from r2n_qda_predict import r2n_qda_predict

x, _, _ = r2n_butterworth(eeg, 'high', 4, 1, 512)               # eeg: [samples, channels]
psd = r2n_welch(x[-512:], 512, 256, 128, 'hamming', np.arange(4, 49, 2))
p, _ = r2n_qda_predict(r2n_qda_read('qda_test_gdf.r2nd'), psd.T.ravel())
```

Loading a scikit-learn or a deep-learning model, and the table of all the functions: [Reproducibility in Python](python.md).
