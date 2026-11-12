function y = r2n_laplacian(x, layout)
%R2N_LAPLACIAN  ros2neuro_filters_laplacian: y = x * mask. Column c of the mask has +1 on channel c and -1/n on each of its n neighbours
%   (left, right, up, down in the grid of the layout, where there is an electrode; 0 = no electrode).
%   x : [samples channels]; layout : matrix such as [1 2 3; 4 5 6; 7 8 9] or the text of the yaml parameter "1 2 3; 4 5 6; 7 8 9".
%   Laplacian<float>::apply is input * mask in float32 with Eigen: the products are added one after the other in float32, as here.
x = single(x); nch = size(x, 2);
if ischar(layout) || isstring(layout)
    rows = strsplit(char(layout), ';'); layout = [];
    for r = 1:numel(rows), v = sscanf(rows{r}, '%d')'; if ~isempty(v), layout(end+1, :) = v; end, end %#ok<AGROW>
end
[nr, nc] = size(layout); mask = zeros(nch);
for ch = 1:nch
    [r, c] = find(layout == ch); if isempty(r), continue, end
    nb = [];
    if c > 1  && layout(r, c-1), nb(end+1) = layout(r, c-1); end %#ok<AGROW>
    if c < nc && layout(r, c+1), nb(end+1) = layout(r, c+1); end %#ok<AGROW>
    if r > 1  && layout(r-1, c), nb(end+1) = layout(r-1, c); end %#ok<AGROW>
    if r < nr && layout(r+1, c), nb(end+1) = layout(r+1, c); end %#ok<AGROW>
    mask(ch, ch) = 1;
    for n = nb, mask(n, ch) = -1 / numel(nb); end
end
mask = single(mask);
y = zeros(size(x, 1), nch, 'single');
for j = 1:nch
    acc = zeros(size(x, 1), 1, 'single');
    for k = 1:nch, acc = acc + x(:, k) * mask(k, j); end
    y(:, j) = acc;
end
end
