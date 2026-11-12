function [y, b, a] = r2n_butterworth(x, type, order, fc, fs)
%R2N_BUTTERWORTH  ros2neuro_filters_butterworth: causal IIR Butterworth (low-pass or high-pass), run over the whole signal.
%   x : [samples channels]; type : 'low' | 'high'; order, fc (Hz), fs (Hz). No toolbox needed (same design as butter()).
%   ROS runs the filter in double precision (rtfilter) and converts the output to float32: the same here. The state goes on across the
%   frames, so the result is that of one filter() over the whole signal. Returns y (single) and the coefficients b, a.
Wn = fc / (fs / 2); Wo = 2 * tan(pi * Wn / 2);                  % pre-warped cut-off, sampling frequency 2
k = 1:order; p = exp(1i * pi * (2 * k + order - 1) / (2 * order));  % analog prototype, left half plane
switch lower(type)
    case 'low',  s = Wo * p;     zz = -ones(1, order);
    case 'high', s = Wo ./ p;    zz =  ones(1, order);
    otherwise, error('r2n_butterworth:type', 'type must be "low" or "high"');
end
zp = (1 + s / 2) ./ (1 - s / 2);                                 % bilinear transform
a = real(poly(zp)); b = real(poly(zz));
if strcmpi(type, 'low'), g = sum(a) / sum(b); else, sg = (-1) .^ (0:order); g = sum(a .* sg) / sum(b .* sg); end
b = b * g;
y = single(filter(b, a, double(x)));
end
