from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.window.window_sdl2 import WindowSDL
from kivy.graphics import Color, Rectangle
from kivy.logger import Logger
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty, \
    AliasProperty, NumericProperty, ReferenceListProperty, VariableListProperty, BoundedNumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from com.valsr.psb.ui.window.base import WindowBase


class MenuItem( Widget ):
    def __init__( self, **kwargs ):
        if self.__class__ is MenuItem:
            raise RuntimeError( 'You cannot use MenuItem directly.' )
        self.menu = None # sub menu
        self.parent = None # parent menu
        self.menu_items = []
        self.level = 0
        super().__init__( **kwargs )

class SimpleMenuItem( Label, MenuItem ):
    pass

class Menu( BoxLayout ):
    minimum_width = NumericProperty( 0 )
    minimum_height = NumericProperty( 0 )
    minimum_size = ReferenceListProperty( minimum_width, minimum_height )
    menu_color = ListProperty( [0.3, 0.3, 0.3, 0.75] )
    border_color = ListProperty( [0.75, 0.75, 0.75, 1] )
    menu_items = ListProperty( [] )
    padding = VariableListProperty( [1] )
    spacing = NumericProperty( 1 )

    def __init__( self, **kwargs ):
        super().__init__( orientation = 'vertical', size_hint = ( None, None ), ** kwargs )
        self._trigger_layout = Clock.create_trigger( self._do_layout, -1 )
        self.level = 0
        self.visible = False
        self.root_widget = None
        trigger = self._trigger_layout
        self.fbind( 'pos', trigger )
        self.fbind( 'size', trigger )
        Window.bind( mouse_pos = self.on_mouse_move )
        trigger()

    def add_menu_item( self, menu ):
        if not isinstance( menu, MenuItem ):
            raise RuntimeError( 
                'The menu must be a subclass of MenuItem' )

        self.menu_items.append( menu )
        menu.size_hint = ( None, None )
        menu.level = self.level + 1
        if not menu.height or menu.height == 100:
            menu.height = 50

        menu.fbind( 'size', self._trigger_layout )
        if self.visible:
            self._trigger_layout()
        return menu

    def remove_menu_item( self, menu ):
        if not isinstance( menu, MenuItem ):
            raise RuntimeError( 
                'The menu must be a subclass of MenuItem' )

        if menu in self.menu_items:
            self.menu_items.pop( menu )
            menu.funbind( 'size', self._trigger_layout )
            self._trigger_layout()

    def get_menu_at_pos( self, pos ):
        x, y = pos
        for node in self.menu_items:
            if self.x <= x <= self.right and \
               node.y <= y <= node.top:
                return node

    #
    # Private
    #
    def _do_layout( self, *largs ):
        if self.visible:
            self.clear_widgets()
            self._draw_background()

            min_width = self.padding[0] + self.padding[2]
            min_height = self.padding[1] + self.padding[3]
            for child in self.menu_items:
                self.add_widget( child )
                min_height += child.height + self.spacing
                min_width = max( min_width, child.width )

            self.width = max( min_width, self.width )
            self.height = max( min_height, self.height )

    def _draw_background( self ):
        self.canvas.clear()

        with self.canvas:
            Color ( *self.border_color )
            Rectangle( pos = self.pos, size = self.size )

            Color( *self.menu_color )
            padding = self.padding
            Rectangle( pos = ( self.pos[0] + padding[0], self.pos[1] + padding[2] ),
                       size = ( self.size[0] - padding[0] - padding[2], self.size[1] - padding[1] - padding[3] ) )

            Color ( *self.border_color )
            sepHeight = self.height - self.padding[1] - self.spacing
            for child in self.menu_items:
                sepHeight -= child.height + self.spacing
                Rectangle( pos = ( self.pos[0], self.pos[1] + sepHeight ), size = ( self.size[0], self.spacing ) )

    def on_touch_down( self, touch ):
        if self.visible:
            self.hide()
            node = self.get_menu_at_pos( touch.pos )
            if node:
                # do node event
                return

            return True

    def on_touch_move( self, touch ):
        if self.visible:
            item = self.get_menu_at_pos( *touch.pos )
            if not item:
                self.hide()
                return True

            # set active
    def on_mouse_move( self, window, pos ):
        if self.visible:
            item = self.get_menu_at_pos( pos )
            if not item:
                self.hide()
                return True
        else:
            Window.unbind( mouse_pos = self.on_mouse_move )

    def show( self, x, y, widget ):
        if not self.visible:
            self.visible = True
            if not self.root_widget:
                self.root_widget = self._findRootWiget( widget )
            self.root_widget.add_widget( self )
            self._do_layout()
            self.pos = ( x - 10, y - self.height + 10 )

    def hide( self ):
        if self.visible:
            self.visible = False
            Window.unbind( mouse_pos = self.on_mouse_move )
            self.root_widget.remove_widget( self )

    def _findRootWiget( self, start_widget = None ):
        if self.root_widget is None:
            widget = start_widget
            while not isinstance( widget , WindowSDL ) and not isinstance( widget, WindowBase ) :
                widget = widget.parent

            return widget

        return self.root_widget
