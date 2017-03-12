"""
Created on Feb 4, 2017

@author: valsr <valsr@valsr.com>
"""
from kivy.logger import Logger


class Droppable(object):
    """Droppable class interface"""

    __events_ = ('on_drop', 'on_hover')

    def _drop(self, draggable, touch):
        ret = self.on_drop(draggable, touch)
        if not ret:
            Logger.warning("Draggable object rejected")

        return ret

    def on_drop(self, draggable, touch):
        """Handles drag drop event

        Args:
            draggable: Object being dropped
            touch: Touch event
        """
        pass

    def on_hover(self, draggable, touch):
        """Handles when a draggable object is hovered (but not dropped) over.

        Args:
            draggable: Object being dropped
            touch: Touch event
        """
        pass

    def on_hover_out(self, draggable, touch):
        """Handles when a draggable object is hovered out (but not dropped) over.

        Args:
            draggable: Object being dropped
            touch: Touch event
        """
        pass
