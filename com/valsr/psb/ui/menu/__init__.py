from abc import abstractmethod
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
from postgresql.project import abstract
import time
import uuid

from com.valsr.psb.ui.window.base import WindowBase


class MenuItem( Widget ):
    select_cb = ObjectProperty( None )
    hover_cb = ObjectProperty( None )
    menu = ObjectProperty( None )

    def __init__( self, select_cb = None, hover_cb = None, **kwargs ):
        if self.__class__ is MenuItem:
            raise RuntimeError( 'You cannot use MenuItem directly.' )
        self.parent_menu = None # parent menu
        self.id = str( uuid.uuid1().hex )
        self.select_cb = select_cb
        self.hover_cb = hover_cb
        super().__init__( **kwargs )

    def on_hover( self, pos ):
        if self.menu:
            self.menu.show( self.pos[0] + self.width - 10, self.pos[1] + self.height - 10, self )

        if self.hover_cb:
            return self.hover_cb( pos )

        return True

    def on_hover_out( self, pos ):
        if self.menu:
            self.menu.hide()

    def on_select( self, touch ):
        if self.select_cb:
            return self.select_cb( touch )

        return False

    @abstractmethod
    def _calculate_minimum_size( self ):
        pass

    def _is_active( self ):
        if self.parent_menu:
            activeItem = self.parent_menu.active_menu_item
            return activeItem and activeItem.id == self.id

        return False

    def set_menu( self, menu ):
        if menu and not isinstance( menu, Menu ):
            raise RuntimeError( 'Menu must be an instance of Menu' )

        if self.menu:
            self.menu.parent_menu_item = None

        self.menu = menu

        if self.menu:
            self.menu.parent_menu_item = self


class SimpleMenuItem( Label, MenuItem ):
    def __init__( self, **kwargs ):
        super().__init__( **kwargs )

    def _calculate_minimum_size( self ):
        self.texture_update()
        return ( self.texture_size[0], self.texture_size[1] + 12 )

class Menu( BoxLayout ):
    minimum_width = NumericProperty( 0 )
    minimum_height = NumericProperty( 0 )
    minimum_size = ReferenceListProperty( minimum_width, minimum_height )
    menu_color = ListProperty( [0.3, 0.3, 0.3, 0.75] )
    selected_menu_color = ListProperty( [0.6, 0.6, 0.6, 0.85] )
    border_color = ListProperty( [0.75, 0.75, 0.75, 1] )
    padding = VariableListProperty( [1] )
    spacing = NumericProperty( 1 )

    menu_items = ListProperty( [] )
    active_menu_item = ObjectProperty( defaultvalue = None, allownone = True )
    parent_menu_item = ObjectProperty( defaultvalue = None, allownone = True )

    def __init__( self, **kwargs ):
        super().__init__( orientation = 'vertical', size_hint = ( None, None ), ** kwargs )
        self._trigger_layout = Clock.create_trigger( self._do_layout, -1 )
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

        Logger.debug( 'Adding menu item %s', menu.id )

        self.menu_items.append( menu )
        menu.parent_menu = self
        menu.size_hint = ( None, None )
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
        if self.x <= pos[0] <= self.right:
            return self.get_menu_at_y_pos( pos[1] )

    def get_menu_at_y_pos( self, y ):
        for item in self.menu_items:
            if item.y <= y <= item.top:
                return item
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
                child.size = child._calculate_minimum_size()
                min_width = max( min_width, child.width )
                min_height += child.height + self.spacing

            # fix bottom height (no spacing)
            min_height -= self.spacing

            self.width = max( min_width, self.width )
            self.height = max( min_height, self.height )

            # fix child widths
            childWidth = self.width - self.padding[0] - self.padding[1]
            for child in self.menu_items:
                child.width = childWidth

            for child in self.menu_items:
                self.add_widget( child )


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
            sepHeight = self.height - self.padding[1]
            for child in self.menu_items:
                sepHeight -= child.height

                # selected child
                if self.active_menu_item and child.id == self.active_menu_item.id:
                    Color ( *self.selected_menu_color )
                    Rectangle( pos = ( self.pos[0] + padding[0], self.pos[1] + sepHeight ),
                               size = ( self.size[0] - padding[0] - padding[2], child.height ) )
                    Color ( *self.border_color )

                sepHeight -= self.spacing
                Rectangle( pos = ( self.pos[0] + self.padding[0], self.pos[1] + sepHeight ),
                           size = ( self.size[0], self.spacing ) )

    def on_touch_down( self, touch ):
        if self.visible:
            self.hide()
            node = self.get_menu_at_pos( touch.pos )
            if node:
                return node.on_select( touch )

            return True

    def deactivate_active_menu_item( self ):
        if self.active_menu_item:
            self.active_menu_item = None
            self._trigger_layout()

    def activate_menu_item( self, item ):
        if item in self.menu_items:
            self.deactivate_active_menu_item()
            self.active_menu_item = item

    def on_mouse_move( self, window, pos ):
        if self.visible:
            # check if the active menu should be closed
            active = self.active_menu_item
            if active and active.menu and active.menu.visible:
                r = active.menu.on_mouse_move( window, pos )
                if active.menu.visible: # menu remained visible so return r (hover return action)
                    return r

            item = self.get_menu_at_pos( pos )

            if item:
                if not active or self.active_menu_item.id != item.id:
                    Logger.debug( "Hover menu item %s", item.id )
                    if self.active_menu_item:
                        self.active_menu_item.on_hover_out( pos )
                        self.deactivate_active_menu_item()
                    self.activate_menu_item( item )
                    self._trigger_layout()
                    return item.on_hover( pos )
            else:
                print( 'No menu at position ', pos, self )
                self.hide()
                return True
        else:
            Window.unbind( mouse_pos = self.on_mouse_move )

    def show( self, x, y, widget ):
        if not self.visible:
            if len( self.menu_items ) > 0:
                self.visible = True
                if not self.root_widget:
                    self.root_widget = self._findRootWiget( widget )
                self.root_widget.add_widget( self )
                self._do_layout()
                self.pos = ( x - 10, y - self.height + 10 )
            else:
                Logger.debug( 'No menu items in menu! Will not open' )
        else:
            Logger.debug( 'Menu already visible' )


    def hide( self ):
        if self.visible:
            deactivate = True

            # check if the parent is inactive
            if self.parent_menu_item:
                deactivate = not self.parent_menu_item._is_active()

            if deactivate:
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
