'''
Created on Feb 4, 2017

@author: radoslav
'''
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.window.window_sdl2 import WindowSDL
from kivy.logger import Logger
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty, NumericProperty
from kivy.uix.treeview import TreeView, TreeViewLabel, TreeViewException
from kivy.uix.widget import Widget
import math
import uuid

from com.valsr.psb.ui.widget.draggable import Draggable
from com.valsr.psb.ui.widget.droppable import Droppable


class DraggableTreeView( TreeView, Droppable ):
    '''
    classdocs
    '''
    draggable = BooleanProperty( True )
    draggable_offset = NumericProperty( 30 )
    def __init__( self, **kwargs ):
        '''
        Constructor
        '''
        super().__init__( **kwargs )

    def add_node( self, node, parent = None ):
        if self._root != None: # allow adding different nodes during tree initalization
            if not isinstance( node, DraggableTreeViewNode ):
                raise TreeViewException( 
                    'The node must be a subclass of DraggableTreeViewNode' )
        else: # convert root nod to DraggabreTreeViewNode
            rootNode = DraggableTreeViewNode( text = 'root', is_open = True, level = 0 )
            for key, value in self.root_options.items():
                setattr( rootNode, key, value )
            node = rootNode
            node.draggable = False

        # check if the parent has the node already
        if parent and parent.has_node_id( node.id ):
            Logger.warning( 'Node %s already has node by id %s', parent.id, node.id )
            return parent.get_node( node.id )

        node = super().add_node( node, parent )

        for n in self.iterate_all_nodes( node ):
            n._tree = self

        return node

    def remove_node( self, node ):
        for n in self.iterate_all_nodes( node ):
            n._tree = None

        super().remove_node( node )

    def find_node( self, cb ):
        return self.root.find_node( cb, True )

    def on_drag_drop( self, draggable, touch ):
        if isinstance( draggable, DraggableTreeViewNode ):
            node = self.get_node_at_pos( touch.pos )
            if not node:
                node = self.root

            self.select_node( node )
            self.add_node( draggable, self.root )
            return True

        return False

    def on_drag_over( self, draggable, touch ):
        node = self.get_node_at_pos( self.to_widget( *touch.pos ) )
        if not node:
            node = self.root

        self.select_node( node )

class DraggableTreeViewNode( TreeViewLabel, Draggable ):
    id = StringProperty( allownone = False )
    data = ObjectProperty( defaultvalue = None )
    _tree = ObjectProperty( defaultvalue = None, allownone = True )

    def __init__( self, id = None, data = None, **kwargs ):
        if id == None:
            id = str( uuid.uuid1().hex )

        self.id = id
        self.data = data
        super().__init__( **kwargs )

    def add_node( self, node ):
        return self._tree.add_node( node, self )

    def remove_node_id( self, id ):
        node = self.get_node( id )
        if node:
            self._tree.remove_node( node )

    def get_node( self, id ):
        return self.find_node( lambda x: x.id == id, False )

    def has_node_id( self, id ):
        return self.get_node( id ) is not None

    def find_node( self, cb, decend = False ):
        for node in self.nodes:
            if cb( node ):
                return node
            elif decend:
                node.find_node( cb, decend )

        return None

    def open( self, openParents = False ):
        if not self.is_leaf:
            if not self.is_open:
                self._tree.toggle_node( self )
            else:
                Logger.trace( 'Node %s: Already opened', self.id )
        else:
            Logger.trace( 'Node %s: is a leaf node', self.id )

        if openParents and self.parent_node:
            Logger.debug( 'opening parents' )
            self.parent_node.open( openParents = True )

    def close( self ):
        if not self.is_leaf:
            if self.is_open:
                self._tree.toggle_node( self )
            else:
                Logger.trace( 'Node %s: Already closed', self.id )
        else:
            Logger.trace( 'Node %s: is a leaf node', self.id )

    def toggle( self ):
        self._tree.toggle_node( self )
