function psd = r2n_welch(x, w)
%R2N_WELCH  ros2neuro_processing_spectral (Welch): ln of the power spectral density of one buffer, at the frequencies of the feature.
%   x : [samples channels] (the buffer, double); w : struct with
%       w.fs (Hz), w.length (segment, samples), w.overlap (samples), w.window ('hann' | 'hamming'), w.freqs (Hz, the bins to keep).
%   Segments of w.length every length-overlap, symmetric window (the Hamming of the ROS code is divided by 100), |X|^2 / (fs * sum(win^2) *
%   segments), x2 on the interior bins, summed over the segments, ln(max(., 1e-12)). Returns [numel(w.freqs) channels].
step = w.length - w.overlap; nseg = 1 + floor((size(x, 1) - w.length) / step);
win = r2n_spectral_window(w.window, w.length);                 % native MATLAB window, symmetric
scale = w.fs * sum(win .^ 2) * nseg; bins = w.length / 2 + 1; power = zeros(bins, size(x, 2));
for s = 0:nseg-1
    X = fft(x(s * step + (1:w.length), :) .* win, [], 1); X = X(1:bins, :);
    p = (real(X) .^ 2 + imag(X) .^ 2) / scale; p(2:end-1, :) = 2 * p(2:end-1, :); power = power + p;
end
power = log(max(power, 1e-12));
psd = power(round(w.freqs / (w.fs / w.length)) + 1, :);
end
