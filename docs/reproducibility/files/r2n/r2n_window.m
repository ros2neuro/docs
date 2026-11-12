function [y, w] = r2n_window(x, name, block)
%R2N_WINDOW  ros2neuro_filters_hann / hamming / blackman / flattop: every block (one NeuroFrame) is multiplied by the same window.
%   x : [samples channels]; name : 'hann' | 'hamming' | 'blackman' | 'flattop'; block : samples per NeuroFrame (default 32).
%   The window is symmetric (denominator N-1), computed in double and rounded to float32 like static_cast<float>(...) in the plugins.
%   Trailing samples that do not fill a block are dropped. Returns the windowed signal (single) and the window.
if nargin < 3, block = 32; end
n = (0:block-1)'; t = 2 * pi * n / (block - 1);
switch lower(name)
    case 'hann',     w = 0.5 * (1 - cos(t));
    case 'hamming',  w = (54.0 - 46.0 * cos(t)) / 100.0;
    case 'blackman', w = (42.0 - 50.0 * cos(t) + 8.0 * cos(2 * t)) / 100.0;
    case 'flattop',  w = 0.215578950 - 0.416631580 * cos(t) + 0.277263158 * cos(2 * t) - 0.083578947 * cos(3 * t) + 0.006947368 * cos(4 * t);
    otherwise, error('r2n_window:name', 'unknown window "%s"', name);
end
w = single(w); x = single(x); nb = floor(size(x, 1) / block); y = zeros(nb * block, size(x, 2), 'single');
for b = 0:nb-1, y(b*block + (1:block), :) = x(b*block + (1:block), :) .* w; end
end
