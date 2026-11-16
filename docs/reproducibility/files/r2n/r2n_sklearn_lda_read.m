function m = r2n_sklearn_lda_read(file)
%R2N_SKLEARN_LDA_READ  The numbers of a scikit-learn Pipeline [StandardScaler] + LinearDiscriminantAnalysis, as written next to the model by
%   data/models/export_lda_weights.py (lda_weights.yaml, one key per line, lists on one line): scaler_mean, scaler_scale, coef [rows columns, row-major],
%   intercept, classes_sklearn (the order of scikit-learn's classes_), classes (the order of the output fields of the decoder) and, when the manifest
%   selects features, selection (0-based indices into the feature of the plugin; read here as 1-based, [] = all the features).
m.mean = r2n_yaml_value(file, 'scaler_mean'); m.scale = r2n_yaml_value(file, 'scaler_scale');
shape = r2n_yaml_value(file, 'coef_shape'); m.coef = reshape(r2n_yaml_value(file, 'coef'), shape(2), shape(1))';   % row-major [rows columns]
m.intercept = r2n_yaml_value(file, 'intercept'); m.classes_sklearn = r2n_yaml_value(file, 'classes_sklearn'); m.classes = r2n_yaml_value(file, 'classes');
m.selection = [];                                   % the features the LDA reads (1-based indices into the feature), empty = all of them
try, m.selection = r2n_yaml_value(file, 'selection') + 1; catch, end %#ok<NOCOM>
end
