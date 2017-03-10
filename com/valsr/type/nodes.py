"""
Created on Mar 9, 2017

@author: valsr <valsr@valsr.com>
"""
from com.valsr.type.tree import GenericTreeNode


class AudioFileNode(GenericTreeNode):
    """Audio file node used for audio files tree"""

    def __init__(self, label, node_id=None, **params):
        """Constructor"""
        super().__init__(**params)
        self.label = label
        self.node_id = node_id if node_id else self.id
