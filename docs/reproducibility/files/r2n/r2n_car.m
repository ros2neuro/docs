function y = r2n_car(x)
%R2N_CAR  ros2neuro_filters_car: common average reference. y(s,:) = x(s,:) - mean(x(s,:)).
%   x : [samples channels]. Returns single. NATIVE MATLAB: x - mean(x, 2) (the plugin adds the channels in float32: a few ULP of difference at most).
x = single(x);
y = x - mean(x, 2);
end
