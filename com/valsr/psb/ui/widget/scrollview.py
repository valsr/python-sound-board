"""
Created on Mar 14, 2017

@author: valsr <valsr@valsr.com>
"""
from kivy.uix.scrollview import ScrollView
from com.valsr.psb.ui.widget.droppable import Droppable


class ScrollViewEx(ScrollView, Droppable):
    """Custom scroll view that provides extra functions such as scroll when something is dragged over this widget"""

    def __init__(self, *args, **kwargs):
        """Constructor"""
        super().__init__(*args, **kwargs)

    def on_drop(self, draggable, touch):
        return False

    def on_hover(self, draggable, touch):
        pass