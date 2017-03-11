"""
Created on Mar 9, 2017

@author: valsr <valsr@valsr.com>
"""
from com.valsr.type.tree import DataTreeNode, GenericTreeNodeSearcher
from com.valsr.psb.sound.info import MediaInfo
import copy


class AudioFileNode(DataTreeNode):
    """Audio file node used for audio files tree"""

    def __init__(self, label, node_id=None, **params):
        """Constructor"""
        super().__init__(**params)
        self.label = label
        self.node_id = node_id if node_id else self.id

    def is_category(self):
        return not self.is_file()

    def is_file(self):
        return self.has_data('data') and isinstance(self.data, MediaInfo)

    def clone(self, deep=False):
        node = AudioFileNode(label=self.label, node_id=self.node_id)

        data = self.get_data()
        node.set_data(copy.copy(data) if not deep else copy.deepcopy(data))

        for child in self.nodes():
            child_node = child.clone()
            node.add_node(child_node)

        return node
        return super().clone()


def find_by_fingerprint(fingerprint):
    def _find(node, fingerprint):
        if node.has_data('data') and isinstance(node.data, MediaInfo):
            return node.data.fingerprint == fingerprint
        return False

    return GenericTreeNodeSearcher(_find, fingerprint)


def find_by_fingerprint(fingerprint):
    def _find(node, fingerprint):
        if node.has_data('data') and isinstance(node.data, MediaInfo):
            return node.data.fingerprint == fingerprint
        return False

    return GenericTreeNodeSearcher(_find, fingerprint)
