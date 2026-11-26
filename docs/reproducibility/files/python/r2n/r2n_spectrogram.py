import numpy as np

from r2n_spectral_window import r2n_spectral_window


def r2n_spectrogram(x, fs, window_length, overlap, window='hann', apply_log=True):
    """ros2neuro_processing_spectral Spectrogram (SpectrogramCore.h): power spectral density of every segment.

    x : [analysis_length, channels] (the last analysis_length samples); fs : Hz; window_length, overlap : samples; window : name of
    r2n_spectral_window; apply_log : 10*log10(max(p, 1e-12)). Segments of window_length every window_length-overlap samples; in
    double |FFT(segment * w)|^2 / (fs * sum(w^2)), x2 on every bin but the first and the last; rounded to float32.
    Returns p [segments, bins, channels] (the feature has the same shape, the channel varying fastest: its data is p.ravel()),
    the frequencies and the time of the centre of every segment.
    """
    overlap = min(overlap, window_length - 1)
    step = window_length - overlap
    nseg = 1 + (x.shape[0] - window_length) // step
    bins = window_length // 2 + 1
    w = r2n_spectral_window(window, window_length)
    scale = fs * np.sum(w ** 2)
    p = np.zeros((nseg, bins, x.shape[1]))
    for s in range(nseg):
        X = np.fft.fft(np.asarray(x[s * step:s * step + window_length], dtype=np.float64) * w[:, None], axis=0)[:bins]
        q = (X.real ** 2 + X.imag ** 2) / scale
        q[1:bins - 1] *= 2
        p[s] = q
    if apply_log:
        p = 10 * np.log10(np.maximum(p, 1e-12))
    return p.astype(np.float32), (fs / window_length * np.arange(bins)).astype(np.float32), \
        ((np.arange(nseg) * step / fs) + (window_length - 1) / (2 * fs)).astype(np.float32)
