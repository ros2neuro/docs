import importlib
import os

import yaml


def r2n_braindecode_load(model):
    """Loads a deep-learning model of ros2neuro_decoder_braindecode (a folder with manifest.yaml and params.pt, or the manifest itself),
    the way the plugin does, without ROS: the class of `decoder.target` is built from `decoder.config` and gets the weights of the
    parameters file, in eval mode on the CPU.

    Returns a dict: net (the torch module), labels (the channels the network reads, in its order), fields (the output classes) and
    the manifest. Needs torch, braindecode, pyyaml.
    """
    import torch
    manifest_file = os.path.join(model, 'manifest.yaml') if os.path.isdir(model) else model
    folder = os.path.dirname(os.path.abspath(manifest_file))
    with open(manifest_file) as f:
        manifest = yaml.safe_load(f)
    dec = manifest['decoder']
    module_name, class_name = dec['target'].rsplit('.', 1)
    cls = getattr(importlib.import_module(module_name), class_name)
    net = cls.from_config(dec['config']) if hasattr(cls, 'from_config') else cls(**dec['config'])
    net.load_state_dict(torch.load(os.path.join(folder, dec.get('parameters_file', 'params.pt')), map_location='cpu', weights_only=True))
    net.eval()
    return {'net': net, 'labels': [str(c) for c in manifest['input']['axes'][1]['labels']],
            'fields': [str(c) for c in manifest['output']['fields']], 'manifest': manifest}
