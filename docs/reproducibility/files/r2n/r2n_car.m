function y = r2n_car(x)
%R2N_CAR  ros2neuro_filters_car: common average reference. y(s,:) = x(s,:) - mean(x(s,:)).
%   x : [samples channels]. Returns single.
%   Car<float>::apply computes in float32 with Eigen: input.rowwise().mean() adds the channels one after the other in float32.
%   MATLAB's mean() on single adds in double, so the mean is summed here by hand to give the same rounding.
x = single(x);
acc = zeros(size(x, 1), 1, 'single');
for j = 1:size(x, 2), acc = acc + x(:, j); end
y = x - acc / single(size(x, 2));
end
