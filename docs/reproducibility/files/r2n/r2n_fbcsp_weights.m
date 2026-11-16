function W = r2n_fbcsp_weights(filters, bands, components, channels)
%R2N_FBCSP_WEIGHTS  The CSP filters of the parameter `filters` of the Fbcsp plugin (a flat list, [band][component][channel], channel varying fastest)
%   as the [bands components channels] array r2n_fbcsp takes.
W = permute(reshape(double(filters(:)), channels, components, bands), [3 2 1]);
end
