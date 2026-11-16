function y = r2n_dc(x, block)
%R2N_DC  ros2neuro_filters_dc: removes the mean of every channel, one block (one NeuroFrame) at a time.
%   x : [samples channels]; block : samples per NeuroFrame (default 32). Trailing samples that do not fill a block are dropped.
%   NATIVE MATLAB: x - mean(x) on every block, in single (the plugin adds in float32: a few ULP of difference at most).
if nargin < 2, block = 32; end
nb = floor(size(x, 1) / block); x = single(x(1:nb * block, :));
x3 = reshape(x, block, nb, []);
y = reshape(x3 - mean(x3, 1), nb * block, []);
end
