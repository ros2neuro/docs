function [a, freqs] = r2n_fft(x, fs, window, apply_log)
%R2N_FFT  ros2neuro_processing_spectral fft_node (FFTProcessor.h): one-sided amplitude spectrum of one buffer.
%   x : [window_length channels] (the last window_length samples, float32 as they arrive); fs : Hz; window : name of
%   r2n_spectral_window (default 'hann'); apply_log : 20*log10(max(a, 1e-12)) (default false).
%   In double: |FFT(x .* w)| / N, x2 on every bin but the first and the last; rounded to float32 like the published feature.
%   Returns a [bins channels] and the frequency axis. The feature has shape [channels bins], channel-major: its data is a(:)'.
if nargin < 3, window = 'hann'; end
if nargin < 4, apply_log = false; end
N = size(x, 1); bins = floor(N / 2) + 1;
X = fft(double(x) .* r2n_spectral_window(window, N), [], 1);
a = abs(X(1:bins, :)) / N; a(2:bins-1, :) = 2 * a(2:bins-1, :);
if apply_log, a = 20 * log10(max(a, 1e-12)); end
a = single(a); freqs = single(fs / N * (0:bins-1));
end
