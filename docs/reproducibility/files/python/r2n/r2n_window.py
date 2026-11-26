import numpy as np
from scipy.signal import windows


def r2n_window(x, name, block=32):
    """ros2neuro_filters_hann / hamming / blackman / flattop: every block (one NeuroFrame) is multiplied by the same window.

    x : [samples, channels]; name : 'hann' | 'hamming' | 'blackman' | 'flattop'; block : samples per NeuroFrame (default 32).
    scipy windows, symmetric (the plugins use the denominator N-1), rounded to float32 like the plugins. Trailing samples that do
    not fill a block are dropped. Returns the windowed signal (float32) and the window.
    """
    make = {'hann': windows.hann, 'hamming': windows.hamming, 'blackman': windows.blackman, 'flattop': windows.flattop}
    if name.lower() not in make:
        raise ValueError('unknown window "%s"' % name)
    w = make[name.lower()](block, sym=True).astype(np.float32)
    nb = x.shape[0] // block
    x3 = np.asarray(x[:nb * block], dtype=np.float32).reshape(nb, block, -1)
    return (x3 * w[None, :, None]).reshape(nb * block, -1), w
