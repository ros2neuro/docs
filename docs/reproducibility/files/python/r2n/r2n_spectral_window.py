from scipy.signal import windows


def r2n_spectral_window(name, n):
    """The window of the FFT and spectrogram plugins (WindowFunctions.h): scipy window, in double (not rounded to float32 as in
    r2n_window), symmetric (denominator n-1). name : 'rectangular' (or 'boxcar') | 'hann' | 'hamming' | 'blackman' | 'flattop'."""
    make = {'rectangular': windows.boxcar, 'boxcar': windows.boxcar, 'hann': windows.hann, 'hamming': windows.hamming,
            'blackman': windows.blackman, 'flattop': windows.flattop}
    if name.lower() not in make:
        raise ValueError('unknown window "%s"' % name)
    return make[name.lower()](n, sym=True)
