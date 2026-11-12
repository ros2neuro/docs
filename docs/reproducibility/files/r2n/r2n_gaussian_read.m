function m = r2n_gaussian_read(file)
%R2N_GAUSSIAN_READ  Reads the .r2nd file of the Gaussian decoder (GaussianModel.cpp, version 2, little endian).
%   Returns a struct: priors, frequencies, selection_channel / selection_frequency (0-based), prototypes, centers, covariances, n_classes.
fid = fopen(file, 'r', 'ieee-le'); cleanup = onCleanup(@() fclose(fid)); %#ok<NASGU>
magic = fread(fid, 8, 'uint8=>char')'; assert(strcmp(magic(1:7), 'R2NDEC1'), 'not an .r2nd file');
assert(fread(fid, 1, 'uint32') == 2, 'unsupported .r2nd version');
str = @() fread(fid, fread(fid, 1, 'uint32'), 'uint8=>char')';
str(); str(); str(); str();                                   % name, subject, type, parameterization
m.priors = fread(fid, fread(fid, 1, 'uint32'), 'single')';
str(); if fread(fid, 1, 'uint8') ~= 0, fread(fid, 1, 'single'); end   % regularization method, lambda
str(); str(); str(); str();                                   % solver, source, feature name, unit
fread(fid, 2, 'uint8');                                       % feature type, output type
n_ch = fread(fid, 1, 'uint32'); n_fr = fread(fid, 1, 'uint32'); n_sel = fread(fid, 1, 'uint32'); n_cl = fread(fid, 1, 'uint32');
m.prototypes = fread(fid, 1, 'uint32');
for i = 1:n_ch, str(); end
m.frequencies = fread(fid, n_fr, 'single')';
sel = fread(fid, [2 n_sel], 'uint32')'; m.selection_channel = sel(:, 1); m.selection_frequency = sel(:, 2);   % 0-based
for i = 1:n_cl, str(); end
n = n_cl * m.prototypes * n_sel;
m.centers = reshape(fread(fid, n, 'single'), n_sel, m.prototypes, n_cl);
m.covariances = reshape(fread(fid, n, 'single'), n_sel, m.prototypes, n_cl);
m.n_classes = n_cl;
end
