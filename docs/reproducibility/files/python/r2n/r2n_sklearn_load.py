import os

import yaml


def _locate(axis, item):
    """Index of `item` on one axis of the manifest: by text when the axis has labels, by number when it has values."""
    if axis['labels']:
        return axis['labels'].index(str(item))
    return [i for i, v in enumerate(axis['values']) if abs(v - float(item)) < 1e-6][0]


def r2n_sklearn_load(model):
    """Loads a scikit-learn model of ros2neuro_decoder_sklearn (a folder with manifest.yaml and model.skops, or the manifest itself),
    the way the plugin does (sklearn_model.py), without ROS.

    Returns a dict: model (the estimator or Pipeline, it has predict_proba), classes (the output fields, the order of the published
    probabilities), class_index (their position in model.classes_), axes (the two axes of the feature: name, labels, values),
    mode ('all' | 'selection') and selection (the (axis 0, axis 1) index pairs, in the order the model reads them).
    Needs scikit-learn, skops, pyyaml. skops refuses the types it does not know unless they are trusted: the model is the one you
    chose, so the types it holds are trusted.
    """
    from skops import io as skops_io
    manifest_file = os.path.join(model, 'manifest.yaml') if os.path.isdir(model) else model
    folder = os.path.dirname(os.path.abspath(manifest_file))
    with open(manifest_file) as f:
        manifest = yaml.safe_load(f)
    model_file = os.path.join(folder, manifest['decoder']['path'])
    est = skops_io.load(model_file, trusted=skops_io.get_untrusted_types(file=model_file))
    classes = [str(c) for c in manifest['output']['fields']]
    model_classes = [str(c) for c in est.classes_]
    axes = [{'name': a.get('name', ''), 'labels': [str(v) for v in a.get('labels') or []], 'values': [float(v) for v in a.get('values') or []]}
            for a in manifest['input']['axes']]
    features = manifest.get('features', {'mode': 'all'})
    m = {'model': est, 'classes': classes, 'class_index': [model_classes.index(c) for c in classes], 'axes': axes,
         'mode': features.get('mode', 'all'), 'selection': []}
    if m['mode'] == 'selection':
        sel = features['selection']
        names = [a['name'] for a in axes]
        if all(n in sel for n in names):                    # keys named like the axes (band / component of FBCSP)
            columns = [sel[n] for n in names]
        else:                                               # the original keys of a PSD feature
            columns = [None, None]
            columns[names.index('channels')], columns[names.index('frequency')] = sel['channels'], sel['frequencies']
        m['selection'] = [(_locate(axes[0], x), _locate(axes[1], y)) for x, y in zip(*columns)]
    return m
