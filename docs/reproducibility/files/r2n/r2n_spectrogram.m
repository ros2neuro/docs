function [p, freqs, times] = r2n_spectrogram(x, fs, window_length, overlap, window, apply_log)
%R2N_SPECTROGRAM  ros2neuro_processing_spectral spectrogram_node (SpectrogramProcessor.h): power spectral density of every segment.
%   x : [analysis_length channels] (the last analysis_length samples); fs : Hz; window_length, overlap : samples; window : name of
%   r2n_spectral_window (default 'hann'); apply_log : 10*log10(max(p, 1e-12)) (default true).
%   Segments of window_length every window_length-overlap samples; in double |FFT(segment .* w)|^2 / (fs * sum(w.^2)), x2 on every
%   bin but the first and the last; rounded to float32. Returns p [segments bins channels] (the feature has shape [segments bins channels] with
%   the channel varying fastest: its data is reshape(permute(p, [3 2 1]), 1, [])), the frequencies
%   and the time of the centre of every segment.
if nargin < 5, window = 'hann'; end
if nargin < 6, apply_log = true; end
overlap = min(overlap, window_length - 1); step = window_length - overlap;
nseg = 1 + floor((size(x, 1) - window_length) / step); bins = floor(window_length / 2) + 1;
w = r2n_spectral_window(window, window_length); scale = fs * sum(w .^ 2);
p = zeros(nseg, bins, size(x, 2));
for s = 0:nseg-1
    X = fft(double(x(s * step + (1:window_length), :)) .* w, [], 1);
    q = (real(X(1:bins, :)) .^ 2 + imag(X(1:bins, :)) .^ 2) / scale;
    q(2:bins-1, :) = 2 * q(2:bins-1, :);
    p(s + 1, :, :) = reshape(q, 1, bins, []);
end
if apply_log, p = 10 * log10(max(p, 1e-12)); end
p = single(p); freqs = single(fs / window_length * (0:bins-1));
times = single((0:nseg-1) * step / fs + (window_length - 1) / (2 * fs));
end
