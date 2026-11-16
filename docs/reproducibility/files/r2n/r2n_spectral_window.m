function w = r2n_spectral_window(name, n)
%R2N_SPECTRAL_WINDOW  The window of the FFT and spectrogram nodes (WindowFunctions.h): the native MATLAB window (hann, hamming, blackman,
%   flattopwin, rectwin: Signal Processing Toolbox), in double (not rounded to float32 as in r2n_window), symmetric (denominator n-1). Column of n values.
%   name : 'rectangular' (or 'boxcar') | 'hann' | 'hamming' | 'blackman' | 'flattop'.
switch lower(name)                                  % NATIVE MATLAB (Signal Processing Toolbox), symmetric, in double
    case {'rectangular', 'boxcar'}, w = rectwin(n);
    case 'hann',     w = hann(n, 'symmetric');
    case 'hamming',  w = hamming(n, 'symmetric');
    case 'blackman', w = blackman(n, 'symmetric');
    case 'flattop',  w = flattopwin(n, 'symmetric');
    otherwise, error('r2n_spectral_window:name', 'unknown window "%s"', name);
end
end
