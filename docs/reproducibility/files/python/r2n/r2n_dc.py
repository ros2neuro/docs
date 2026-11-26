import numpy as np


def r2n_dc(x, block=32):
    """ros2neuro_filters_dc: removes the mean of every channel, one block (one NeuroFrame) at a time.

    x : [samples, channels]; block : samples per NeuroFrame (default 32). Trailing samples that do not fill a block are dropped.
    numpy: x - mean(x) on every block, in float32 (the plugin adds in float32: a few ULP of difference at most).
    """
    nb = x.shape[0] // block
    x3 = np.asarray(x[:nb * block], dtype=np.float32).reshape(nb, block, -1)
    return (x3 - x3.mean(axis=1, keepdims=True, dtype=np.float32)).reshape(nb * block, -1)
