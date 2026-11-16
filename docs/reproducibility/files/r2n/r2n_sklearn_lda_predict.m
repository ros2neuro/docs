function p = r2n_sklearn_lda_predict(m, x)
%R2N_SKLEARN_LDA_PREDICT  predict_proba of the scikit-learn LDA of r2n_sklearn_lda_read for one feature row x, in double (scikit-learn is), as float32
%   like the published prediction. x = x(m.selection) when the model selects features; z = (x - mean) ./ scale; d = coef * z + intercept; two classes: p(classes_sklearn(2)) = 1 / (1 + exp(-d)), the other
%   1 minus it; more classes: softmax(d). Returned in the order of m.classes (the output fields of the decoder).
x = double(x(:))'; if ~isempty(m.selection), x = x(m.selection); end        % the features the LDA reads, in its order
z = (x - m.mean) ./ m.scale; d = z * m.coef' + m.intercept;
if size(m.coef, 1) == 1
    p2 = 1 / (1 + exp(-d)); q = zeros(1, 2); q(1) = 1 - p2; q(2) = p2;           % in the order of classes_sklearn
else
    q = exp(d - max(d)); q = q / sum(q);
end
[~, where] = ismember(m.classes, m.classes_sklearn); p = single(q(where));
end
