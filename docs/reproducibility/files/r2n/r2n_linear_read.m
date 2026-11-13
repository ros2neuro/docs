function m = r2n_linear_read(file)
%R2N_LINEAR_READ  Reads the .r2nd of the LDA or the SVM decoder (LDAModel.cpp / SVMModel.cpp: the same layout, version 1 or 2,
%   little endian). Returns a struct: type, parameterization, classes, channels, frequencies, selection_channel /
%   selection_frequency (0-based), weights [K S] (one row per class), bias [1 K], n_classes.
fid = fopen(file, 'r', 'ieee-le'); cleanup = onCleanup(@() fclose(fid)); %#ok<NASGU>
magic = fread(fid, 8, 'uint8=>char')'; assert(strcmp(magic(1:7), 'R2NDEC1'), 'not an .r2nd file');
version = fread(fid, 1, 'uint32'); assert(version == 1 || version == 2, 'unsupported .r2nd version');
str = @() fread(fid, fread(fid, 1, 'uint32'), 'uint8=>char')';
str(); str(); m.type = str(); m.parameterization = str();       % name, subject, type, parameterization
if version >= 2
    fread(fid, fread(fid, 1, 'uint32'), 'single');                 % priors (not used by the prediction)
    str(); if fread(fid, 1, 'uint8') ~= 0, fread(fid, 1, 'single'); end   % regularization method, lambda
    str(); str();                                                  % solver, source
end
str(); str(); fread(fid, 2, 'uint8');                              % feature name, unit, feature type, output type
n_ch = fread(fid, 1, 'uint32'); n_fr = fread(fid, 1, 'uint32'); n_sel = fread(fid, 1, 'uint32'); n_cl = fread(fid, 1, 'uint32');
m.channels = cell(1, n_ch); for i = 1:n_ch, m.channels{i} = str(); end
m.frequencies = fread(fid, n_fr, 'single')';
sel = fread(fid, [2 n_sel], 'uint32')'; m.selection_channel = sel(:, 1); m.selection_frequency = sel(:, 2);   % 0-based
m.classes = cell(1, n_cl); for i = 1:n_cl, m.classes{i} = str(); end
m.weights = reshape(fread(fid, n_cl * n_sel, 'single=>single'), n_sel, n_cl)';   % stored one class after the other
m.bias = fread(fid, n_cl, 'single=>single')';
m.n_classes = n_cl;
end
