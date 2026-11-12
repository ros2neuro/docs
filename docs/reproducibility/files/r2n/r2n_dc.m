function y = r2n_dc(x, block)
%R2N_DC  ros2neuro_filters_dc: removes the mean of every channel, one block (one NeuroFrame) at a time.
%   x : [samples channels]; block : samples per NeuroFrame (default 32). Trailing samples that do not fill a block are dropped.
%   Dc<float> works in float32 with Eigen: input.colwise().mean() adds the samples one after the other in float32 (see r2n_car).
if nargin < 2, block = 32; end
x = single(x); n = floor(size(x, 1) / block) * block; y = zeros(n, size(x, 2), 'single');
for b = 1:block:n
    xb = x(b:b + block - 1, :); acc = zeros(1, size(x, 2), 'single');
    for i = 1:block, acc = acc + xb(i, :); end
    y(b:b + block - 1, :) = xb - acc / single(block);
end
end
