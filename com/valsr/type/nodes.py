"""
Created on Mar 9, 2017

@author: valsr <valsr@valsr.com>
"""
from com.valsr.type.tree import DataTreeNode
from com.valsr.psb.sound.info import MediaInfo


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
