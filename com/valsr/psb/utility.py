"""
Created on Feb 2, 2017

@author: valsr <valsr@valsr.com>
"""
import json
from kivy.logger import Logger

from com.valsr.psb.sound.info import MediaInfo
from enum import Enum


def save_project(file, tree_file_structure=None, stream_list=None):
    """Save project

    Args:
        file: File path
        tree_file_structure: Tree files
        stream_list: List of stream objects
    """
    Logger.info('Saving project to %s', file)

    json_dict = {}
    files = []
    if tree_file_structure:
        for child in tree_file_structure.root.nodes:
            files.append(serialize_node_structure(child))
        json_dict['files'] = files

    if stream_list:
        json_dict['streams'] = stream_list.seralize()

    with open(file, 'w') as f:
        json.dump(json_dict, f, indent=2)

    Logger.info('Project successfully saved to file %s', file)


def serialize_node_structure(node):
    """Serialize node structure to a string

    Args:
        node: Starting root (node)

    Returns:
        String: serialized object
    """
    from com.valsr.psb.ui.widget.audiotree import AudioTreeViewNode

    if not isinstance(node, AudioTreeViewNode):
        raise RuntimeError("Can only serialize AudioTreeViewNode")

    d = {}
    d['id'] = node.id
    d['label'] = node.label

    if isinstance(node.data, MediaInfo):
        d['data'] = node.data.serialize()
    else:
        d['data'] = None

    # serialize children
    d['children'] = []
    for child in node.nodes:
        d['children'].append(serialize_node_structure(child))

    return d


def deserialize_node_structure(d, parent):
    """Deserialize node structure

    Args:
        d: Dictionary to deserialize
        parent: Parent root node
    """
    from com.valsr.psb.ui.widget.audiotree import AudioTreeViewNode

    data = MediaInfo.deserialize(d['data']) if d['data'] else None
    node = AudioTreeViewNode(id=d['id'], data=data, label=d['label'])
    node.is_open = True
    parent.add_node(node)
    if 'children' in d:
        for child in d['children']:
            deserialize_node_structure(child, node)


def load_project(file, tree):
    """Load project file

    Args:
        file: File path to load
        tree: Tree node
    """
    Logger.info('Opening project %s', file)
    with open(file, 'r') as f:
        json_dict = json.load(f)

    # clear up the files tree
    tree.remove_all_nodes()

    nodes = None
    stream = None
    if 'files' in json_dict:
        for n in json_dict['files']:
            deserialize_node_structure(n, tree.root)

    Logger.info('Project file %s loaded successfully', file)

    return (nodes, stream)


def allowed_audio_formats():
    """Return the list of acceptable file formats

    Returns:
        List
    """
    return ['.mp3', '.wav', '.flac', '.ogg', '.mp4']


class MainTreeMenuActions(Enum):
    """Main tree menu actions"""
    RENAME = 1
    DELETE = 2
