import numpy as np

from r2n_spectral_window import r2n_spectral_window


def r2n_fft(x, fs, window='hann', apply_log=False):
    """ros2neuro_processing_spectral FFT (FFTCore.h): one-sided amplitude spectrum of one buffer.

    x : [window_length, channels] (the last window_length samples); fs : Hz; window : name of r2n_spectral_window; apply_log :
    20*log10(max(a, 1e-12)). In double: |FFT(x * w)| / N, x2 on every bin but the first and the last; rounded to float32 like the
    published feature. Returns a [bins, channels] and the frequency axis. The feature has shape [channels, bins], channel-major.
    """
    n = x.shape[0]
    bins = n // 2 + 1
    X = np.fft.fft(np.asarray(x, dtype=np.float64) * r2n_spectral_window(window, n)[:, None], axis=0)
    a = np.abs(X[:bins]) / n
    a[1:bins - 1] *= 2
    if apply_log:
        a = 20 * np.log10(np.maximum(a, 1e-12))
    return a.astype(np.float32), (fs / n * np.arange(bins)).astype(np.float32)
