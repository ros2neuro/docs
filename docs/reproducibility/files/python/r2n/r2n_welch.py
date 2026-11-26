import numpy as np
from scipy.signal import welch

from r2n_spectral_window import r2n_spectral_window


def r2n_welch(x, fs, length, overlap, window, freqs):
    """ros2neuro_processing_spectral (Welch): ln of the power spectral density of one buffer, at the frequencies of the feature.

    x : [samples, channels] (the buffer, double); fs (Hz), length (segment, samples), overlap (samples), window ('hann' | 'hamming'),
    freqs (Hz, the bins to keep). scipy.signal.welch gives the one-sided PSD of every channel with the symmetric window of the plugin,
    segments of `length` every length-overlap, nfft = length and NO detrend (MATLAB's pwelch does not detrend; scipy would by default);
    the plugin publishes ln(max(PSD, 1e-12)) at the bins of `freqs`. Returns [len(freqs), channels].
    """
    win = r2n_spectral_window(window, length)
    _, p = welch(np.asarray(x, dtype=np.float64), fs=fs, window=win, nperseg=length, noverlap=overlap, nfft=length, detrend=False,
                 scaling='density', axis=0)
    bins = np.round(np.asarray(freqs) / (fs / length)).astype(int)
    return np.log(np.maximum(p[bins, :], 1e-12))
