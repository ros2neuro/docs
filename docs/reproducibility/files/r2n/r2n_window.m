function [y, w] = r2n_window(x, name, block)
%R2N_WINDOW  ros2neuro_filters_hann / hamming / blackman / flattop: every block (one NeuroFrame) is multiplied by the same window.
%   x : [samples channels]; name : 'hann' | 'hamming' | 'blackman' | 'flattop'; block : samples per NeuroFrame (default 32).
%   NATIVE MATLAB (Signal Processing Toolbox): hann, hamming, blackman and flattopwin, symmetric (the plugins use the denominator N-1), rounded to
%   float32 like the plugins. Trailing samples that do not fill a block are dropped. Returns the windowed signal (single) and the window.
if nargin < 3, block = 32; end
switch lower(name)
    case 'hann',     w = hann(block, 'symmetric');
    case 'hamming',  w = hamming(block, 'symmetric');
    case 'blackman', w = blackman(block, 'symmetric');
    case 'flattop',  w = flattopwin(block, 'symmetric');
    otherwise, error('r2n_window:name', 'unknown window "%s"', name);
end
w = single(w); nb = floor(size(x, 1) / block); x = single(x(1:nb * block, :));
y = reshape(reshape(x, block, nb, []) .* w, nb * block, []);
end
