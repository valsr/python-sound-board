"""
Created on Mar 3, 2017

@author: valsr <valsr@valsr.com>
"""
from kivy.logger import Logger
import json
from com.valsr.psb.sound.info import MediaInfo
import os
from com.valsr.type.nodes import AudioFileNode


class SaveFile(object):
    """Project Data object"""

    def __init__(self):
        """Constructor"""
        self.audio_tree = AudioFileNode(label='files')
        self.lanes = AudioFileNode(label='lanes')
        self.file = None


def load_project(path):
    """Load project file from given path

    Args:
        path: File to open
    """
    Logger.info('Opening project at %s', path)

    savefile = SaveFile()

    with open(path, 'r') as f:
        json_data = json.load(f)
        savefile.file = path

    # synchronize the file nodes
    if 'files' in json_data:
        for n in json_data['files']:
            _deserialize_node_structure(n, savefile.audio_tree)

    return savefile


def _deserialize_node_structure(data, parent):
    node = AudioFileNode(node_id=data['id'], label=data['label'])

    if data['data']:  # a music file
        node.data = MediaInfo.deserialize(data['data'])

    parent.add_node(node)
    if 'children' in data:
        for child in data['children']:
            _deserialize_node_structure(child, node)


def save_project(savefile):
    Logger.info('Saving project to %s', savefile.file)

    json_dict = {}
    files = []
    lanes = []

    for child in savefile.audio_tree.children():
        files.append(_serialize_node_structure(child, savefile=savefile))
    json_dict['files'] = files

    json_dict['lanes'] = lanes

    with open(savefile.file, 'w') as f:
        json.dump(json_dict, f, indent=2)

    Logger.info('Project successfully saved to file %s', savefile.file)


def _serialize_node_structure(node, savefile):
    """Serialize node structure to a string

    Args:
        node: Node to serialize
        savefile: PSBProject object

    Returns:
        String: serialized object
    """
    from com.valsr.psb.ui.widget.audiotree import AudioTreeViewNode

    if not isinstance(node, AudioTreeViewNode):
        raise RuntimeError("Can only serialize AudioTreeViewNode")

    d = {}
    d['id'] = node.node_id
    d['label'] = node.label

    if isinstance(node.data, MediaInfo):
        d['data'] = node.data.serialize(relative_file=True, relative_root=os.path.dirname(savefile.file))
    else:
        d['data'] = None

    # serialize children
    d['children'] = []
    for child in node.children():
        d['children'].append(_serialize_node_structure(child, savefile=savefile))

    return d

    # adding dictionary items
    # def get
