function w = r2n_spectral_window(name, n)
%R2N_SPECTRAL_WINDOW  The window of the FFT and spectrogram nodes (WindowFunctions.h): the coefficients of the window filters
%   computed in double (not rounded to float32 as the filters of r2n_window), symmetric (denominator n-1). Column of n values.
%   name : 'rectangular' (or 'boxcar') | 'hann' | 'hamming' | 'blackman' | 'flattop'.
t = 2 * pi * (0:n-1)' / (n - 1);
switch lower(name)
    case {'rectangular', 'boxcar'}, w = ones(n, 1);
    case 'hann',     w = (1 - cos(t)) * 0.5;
    case 'hamming',  w = (54.0 - 46.0 * cos(t)) / 100.0;
    case 'blackman', w = (42.0 - 50.0 * cos(t) + 8.0 * cos(2 * t)) / 100.0;
    case 'flattop',  w = 0.215578950 - 0.416631580 * cos(t) + 0.277263158 * cos(2 * t) - 0.083578947 * cos(3 * t) + 0.006947368 * cos(4 * t);
    otherwise, error('r2n_spectral_window:name', 'unknown window "%s"', name);
end
end
