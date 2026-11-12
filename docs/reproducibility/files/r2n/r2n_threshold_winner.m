function w = r2n_threshold_winner(thresholds, values)
%R2N_THRESHOLD_WINNER  ros2neuro_control_feedback: the class over its own threshold (value + 1e-6 >= threshold, in single).
%   The highest value wins when several are over; 0 = none. Used to recompute Hit / Miss / Timeout.
w = 0; th = single(thresholds);
for i = 1:numel(th)
    if values(i) + single(1e-6) < th(i), continue, end
    if w == 0 || values(i) > values(w), w = i; end
end
end
