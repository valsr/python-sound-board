"""
Created on Feb 4, 2017

@author: valsr <valsr@valsr.com>
"""
from kivy.logger import Logger
from kivy.properties import BooleanProperty


class Droppable(object):
    """Droppable class interface. This handles adds three additional behaviors to the class.
    Drop - when a draggable object is dropped onto this object (return false to signify that the object was rejected).
    Hover - when an draggable object is moved over this object. Hover out - when an object hovers out of this object.
    In all cases, the event handling is first delegated to the lowest level widget and propagated up to the parent
    widgets until the drop_propagate property is set to False (or the root most parent is reached). During propagation
    non-droppable widgets will be skipped. If the drop_exposed is set, then it will only fire events when the mouse
    is directly over the droppable widget (and not within any child elements). Furthermore, if drop_child_out is set,
    then moving from this widget to a child will generate a hover_out event."""

    __events_ = ('on_drop', 'on_hover', 'on_hover_out')

    drop_propagate = BooleanProperty(True)
    """Whether to propagate drop events (drop or hover) or not"""

    drop_exposed_only = BooleanProperty(False)
    """Whether to only issue events for only the exposed UI bits (non-child overlapped)"""

    drop_child_out = BooleanProperty(False)
    """Whether to treat hovering over child element as a hover out action or not (only when drop_exposed_only is set 
    to true)"""

    def _drop(self, draggable, touch):
        ret = self.on_drop(draggable, touch)
        if not ret:
            Logger.warning("Draggable object rejected")

        return ret

    def on_drop(self, draggable, touch):
        """Handles drag drop event

        Args:
            draggable: Object being dropped
            touch: Touch event (window coordinate)

        Returns:
            Boolean: To accept as target or not
        """
        return False

    def on_hover(self, draggable, touch):
        """Handles when a draggable object is hovered (but not dropped) over.

        Args:
            draggable: Object being dropped
            touch: Touch event (window coordinate)
        """
        pass

    def on_hover_out(self, draggable, touch):
        """Handles when a draggable object is hovered out (but not dropped) over.

        Args:
            draggable: Object being dropped
            touch: Touch event (window coordinate)
        """
        pass
