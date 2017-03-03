"""
Created on Mar 3, 2017

@author: valsr <valsr@valsr.com>
"""
from com.valsr.psb.ui.widget.draggabletreeview import DraggableTreeViewNode
from com.valsr.psb.sound.info import MediaInfo


class AudioTreeViewNode(DraggableTreeViewNode):
    """Node in the DraggableTreeView used for audio files/categories"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_drag(self, draggable, touch):
        if isinstance(self.data, MediaInfo):
            # get the waveform and switch
            pass
