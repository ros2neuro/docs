function p = r2n_softmax(score)
%R2N_SOFTMAX  The probabilities of the LDA, QDA and SVM decoders: exp(score - max) in single, divided by their sum (added in order).
%   If the sum is not above eps(single(1)) the values are returned as they are (the C++ does the same).
raw = exp(single(score) - max(single(score))); s = single(0);
for k = 1:numel(raw), s = s + raw(k); end
if s <= eps('single'), p = raw; else, p = raw / s; end
end
