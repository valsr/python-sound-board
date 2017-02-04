'''
Created on Feb 4, 2017

@author: radoslav
'''
from abc import abstractmethod, ABCMeta
from kivy.logger import Logger

class Droppable( object ):
    __metaclass__ = ABCMeta

    def _drag_drop( self, draggable, touch ):
        ret = self.on_drag_drop( draggable, touch )
        if not ret:
            Logger.warning( "Draggable object rejected" )

        return ret

    @abstractmethod
    def on_drag_drop( self, draggable, touch ):
        pass

    def _drag_over( self, draggable, touch ):
        ret = self.on_drag_over( draggable, touch )
        return ret

    @abstractmethod
    def on_drag_over( self, draggable, touch ):
        pass
