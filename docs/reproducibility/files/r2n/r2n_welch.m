function psd = r2n_welch(x, w)
%R2N_WELCH  ros2neuro_processing_spectral (Welch): ln of the power spectral density of one buffer, at the frequencies of the feature.
%   x : [samples channels] (the buffer, double); w : struct with
%       w.fs (Hz), w.length (segment, samples), w.overlap (samples), w.window ('hann' | 'hamming'), w.freqs (Hz, the bins to keep).
%   NATIVE MATLAB (Signal Processing Toolbox): pwelch gives the one-sided PSD of every channel with the symmetric window of the plugin, segments of w.length
%   every length-overlap, nfft = w.length; the plugin publishes ln(max(PSD, 1e-12)) at the bins of w.freqs. Returns [numel(w.freqs) channels].
win = r2n_spectral_window(w.window, w.length);                 % native MATLAB window, symmetric
p = pwelch(x, win, w.overlap, w.length, w.fs);                 % native MATLAB: one-sided PSD, [length/2+1 channels]
psd = log(max(p(round(w.freqs / (w.fs / w.length)) + 1, :), 1e-12));
end
