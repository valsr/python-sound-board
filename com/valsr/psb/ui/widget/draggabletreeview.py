'''
Created on Feb 4, 2017

@author: radoslav
'''
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.window.window_sdl2 import WindowSDL
from kivy.graphics import Color, Rectangle, Line
from kivy.input.motionevent import MotionEvent
from kivy.logger import Logger
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty, NumericProperty
from kivy.uix import label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.treeview import TreeView, TreeViewLabel, TreeViewException, TreeViewNode
from kivy.uix.widget import Widget
import math
from matplotlib.backend_bases import MouseEvent
import uuid

from com.valsr.psb.ui.menu import Menu, SimpleMenuItem
from com.valsr.psb.ui.widget.draggable import Draggable
from com.valsr.psb.ui.widget.droppable import Droppable
from com.valsr.psb.ui.window.base import WindowBase


class DraggableTreeView( TreeView, Droppable ):
    '''
    classdocs
    '''
    draggable = BooleanProperty( True )
    draggable_offset = NumericProperty( 30 )
    drop_acceptable_cb = ObjectProperty( None )
    def __init__( self, **kwargs ):
        '''
        Constructor
        '''
        super().__init__( **kwargs )
        self.drop_acceptable_cb = self._drop_acceptable

    def add_node( self, node, parent = None ):
        if self._root != None: # allow adding different nodes during tree initalization
            if not isinstance( node, DraggableTreeViewNode ):
                raise TreeViewException( 
                    'The node must be a subclass of DraggableTreeViewNode' )
        else: # convert root nod to DraggabreTreeViewNode
            rootNode = DraggableTreeViewNode( label = 'root', is_open = True, level = 0 )
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

    def remove_all_nodes( self ):
        for n in self.root.nodes:
            self.remove_node( n )

    def find_node( self, cb ):
        return self.root.find_node( cb, True )

    def on_drag_drop( self, draggable, touch ):
        if isinstance( draggable, DraggableTreeViewNode ):
            node = self.get_node_at_pos( self.to_widget( *touch.pos ) )
            if not node:
                node = self.root

            Logger.debug( 'Selected node %s', node._label.text )
            afterNode = node
            while not self.drop_acceptable_cb( node ):
                node = node.parent_node

            Logger.debug( 'Adding %s to %s', draggable._label.text, node._label.text )
            # add before
            self.select_node( self.add_node( draggable, node ) )
            return True

        return False

    def on_drag_over( self, draggable, touch ):
        node = self.get_node_at_pos( self.to_widget( *touch.pos ) )

        if not node:
            node = self.root

        # figure if we can drop here
        afterNode = node
        while not self.drop_acceptable_cb( node ):
            node = node.parent_node

        self.select_node( node )
        return True

    def _drop_acceptable( self, node ):
        return node.data is None

class DraggableTreeViewNode( TreeViewNode, BoxLayout, Draggable ):
    id = StringProperty( allownone = False )
    data = ObjectProperty( defaultvalue = None )
    _tree = ObjectProperty( defaultvalue = None, allownone = True )
    ui = ObjectProperty( defaultvalue = None, allownone = True )

    def __init__( self, id = None, data = None, label = None, **kwargs ):
        super().__init__( **kwargs )
        if id == None:
            id = str( uuid.uuid1().hex )

        self.id = id
        self.data = data

        # create a label for us
        self._label = Label( text = label )
        self._label.width = self.width
        self._label.shorten = True
        self._label.max_lines = 1
        self._label.shorten_from = 'right'
        self._label.texture_update()

        # add label to ui component
        self.ui = self._label
        self.add_widget( self.ui )

        # fix component height
        self.height = self._label.texture_size[1] + 16
        self._label.text_size = ( self._label.texture_size[0], self._label.texture_size[1] )

    def do_layout( self, *largs ):
        # fix the alignment due to size not being calculated in the init method
        if self.ui is self._label:
            self._label.text_size[0] = self.width
        return BoxLayout.do_layout( self, *largs )

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