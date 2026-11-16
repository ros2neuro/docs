function [y, b, a] = r2n_butterworth(x, type, order, fc, fs)
%R2N_BUTTERWORTH  ros2neuro_filters_butterworth: causal IIR Butterworth (low-pass or high-pass), run over the whole signal.
%   x : [samples channels]; type : 'low' | 'high'; order, fc (Hz), fs (Hz).
%   NATIVE MATLAB (Signal Processing Toolbox): butter designs the filter and filter runs it causally, in double precision, the state going on across
%   the whole signal: the same as the plugin, which filters frame after frame with the state kept (rtfilter, double) and publishes float32.
%   Returns y (single) and the coefficients b, a.
if ~any(strcmpi(type, {'low', 'high'})), error('r2n_butterworth:type', 'type must be "low" or "high"'); end
[b, a] = butter(order, fc / (fs / 2), lower(type));
y = single(filter(b, a, double(x)));
end
