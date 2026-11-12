function value = r2n_yaml_value(file, key)
%R2N_YAML_VALUE  "key: value" of a yaml parameter file of ros2neuro (flat keys such as welch.wlength): number, [a, b, c], true/false or text.
lines = regexp(fileread(file), '\r?\n', 'split');
for i = 1:numel(lines)
    if startsWith(strtrim(lines{i}), '#'), continue, end
    tok = regexp(lines{i}, ['^\s*' regexptranslate('escape', key) '\s*:\s*(.*)$'], 'tokens', 'once');
    if ~isempty(tok), raw = strtrim(regexprep(tok{1}, '\s+#.*$', '')); break, end
end
if ~exist('raw', 'var'), error('r2n_yaml_value:key', 'Key "%s" not found in %s', key, file); end
if startsWith(raw, '[')
    value = sscanf(strrep(strrep(strrep(raw, '[', ' '), ']', ' '), ',', ' '), '%f')';
elseif strcmp(raw, 'true'), value = true;
elseif strcmp(raw, 'false'), value = false;
elseif ~isempty(regexp(raw, '^-?\d+(\.\d+)?([eE][-+]?\d+)?$', 'once')), value = str2double(raw);
else
    value = raw;
    if numel(value) >= 2 && any(value(1) == '"''') && value(end) == value(1), value = value(2:end-1); end
end
end
