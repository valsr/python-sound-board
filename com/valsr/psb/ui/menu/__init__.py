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
        print( 'On hover for ', self.id )
        if self.menu:
            print( 'Open submenu', self.menu )
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
            activeItem = self.parent_menu.active_item
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
    color = ListProperty( [0.3, 0.3, 0.3, 0.75] )
    active_color = ListProperty( [0.6, 0.6, 0.6, 0.85] )
    border_color = ListProperty( [0.75, 0.75, 0.75, 1] )
    selected_color = ListProperty( [0.75, 0.75, 0.75, 1] )
    padding = VariableListProperty( [1] )
    spacing = NumericProperty( 1 )

    items = ListProperty( [] )
    active_item = ObjectProperty( defaultvalue = None, allownone = True )
    parent_menu_item = ObjectProperty( defaultvalue = None, allownone = True )

    def __init__( self, **kwargs ):
        super().__init__( orientation = 'vertical', size_hint = ( None, None ), ** kwargs )
        self._trigger_layout = Clock.create_trigger( self._do_layout, -1 )
        self.visible = False
        self.root_widget = None
        trigger = self._trigger_layout
        self.fbind( 'pos', trigger )
        self.fbind( 'size', trigger )
        trigger()

    def add_menu_item( self, menu ):
        if not isinstance( menu, MenuItem ):
            raise RuntimeError( 
                'The menu must be a subclass of MenuItem' )

        Logger.debug( 'Adding menu item %s', menu.id )

        self.items.append( menu )
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

        if menu in self.items:
            self.items.pop( menu )
            menu.funbind( 'size', self._trigger_layout )
            self._trigger_layout()

    def item_at_pos( self, pos ):
        if self.x <= pos[0] <= self.right:
            return self.item_at_y_pos( pos[1] )

    def item_at_y_pos( self, y ):
        for item in self.items:
            if item.y <= y <= item.top:
                return item

    def _do_layout( self, *largs ):
        if self.visible:
            self.clear_widgets()
            self._draw_background()

            min_width = self.padding[0] + self.padding[2]
            min_height = self.padding[1] + self.padding[3]
            for child in self.items:
                child.size = child._calculate_minimum_size()
                min_width = max( min_width, child.width )
                min_height += child.height + self.spacing

            # fix bottom height (no spacing)
            min_height -= self.spacing

            self.width = max( min_width, self.width )
            self.height = max( min_height, self.height )

            # fix child widths
            childWidth = self.width - self.padding[0] - self.padding[1]
            for child in self.items:
                child.width = childWidth

            for child in self.items:
                self.add_widget( child )

            print( self, self.size, self.pos )

    def _draw_background( self ):
        self.canvas.clear()

        with self.canvas:
            Color ( *self.border_color )
            Rectangle( pos = self.pos, size = self.size )

            Color( *self.color )
            padding = self.padding
            Rectangle( pos = ( self.pos[0] + padding[0], self.pos[1] + padding[2] ),
                       size = ( self.size[0] - padding[0] - padding[2], self.size[1] - padding[1] - padding[3] ) )

            Color ( *self.border_color )
            sepHeight = self.height - self.padding[1]
            for child in self.items:
                sepHeight -= child.height

                # selected child
                if self.active_item and child.id == self.active_item.id:
                    Color ( *self.active_color )
                    Rectangle( pos = ( self.pos[0] + padding[0], self.pos[1] + sepHeight ),
                               size = ( self.size[0] - padding[0] - padding[2], child.height ) )
                    Color ( *self.border_color )

                sepHeight -= self.spacing
                Rectangle( pos = ( self.pos[0] + self.padding[0], self.pos[1] + sepHeight ),
                           size = ( self.size[0], self.spacing ) )

    def on_touch_down( self, touch ):
        if self.visible:
            self.hide()
            node = self.item_at_pos( touch.pos )
            if node:
                return node.on_select( touch )

            return True

    def pos_in_submenu( self, pos, item ):
        print( 'Checking if ', pos, ' is in item', item )
        if item and item.menu and item.menu.visible:
            if item.menu.collide_point( pos ):
                print( 'Position is in submenu' )
                return True
            else:
                print( 'Checking if submenu item at y pos has the pos' )
                return item.menu.pos_in_submenu( pos, item.menu.item_at_y_pos( pos[1] ) )

        print( 'Item has no menu' )
        return False

    def collide_point( self, pos, selfOnly = True ):
        if self.x <= pos[0] <= self.right and self.y <= pos[1] <= self.top:
            return True
        else:
            # loop through all children and through their children's children
            for i in self.items:
                if i.menu and i.menu.visible:
                    if i.menu.collide_item( pos, selfOnly = False ):
                        return True

        return False

    def collide_item( self, pos, selfOnly = True ): # returns menu_item or menu
        item = None # the item corresponding at that position (either menu item or menu)

        # does any sub child element overshadow the current position
        for i in self.items:
            if i.menu and i.menu.visible:
                child = i.menu.collide_item( pos, selfOnly = False )
                if child:
                    item = child

        if not item: # check self for item at position
            if self.x <= pos[0] <= self.right and self.y <= pos[1] <= self.top:
                item = self.item_at_y_pos( pos[1] )
                if not item: # still no item but within self
                    item = self

        return item

    def on_mouse_move( self, window, pos ):
        if self.visible:
            hide = False
            inBound = self.collide_point( pos )

            if inBound or self.collide_point( pos, False ): # within visible menus bounds
                item = self.collide_item( pos, False )
                selfOnly = False
                if isinstance( item, Menu ): # either self or child menu
                    selfOnly = item is self
                else:
                    selfOnly = item in self.items

                if selfOnly:
                    if isinstance( item, Menu ):
                        if self.active_item:
                            oActive = self.active_item
                            self.active_item = None
                            oActive.on_hover_out( pos )
                    else:
                        if self.active_item and self.active_item.id is not item.id:
                            oActive = self.active_item
                            self.active_item = None
                            oActive.on_hover_out( pos )
                            print( 'De-activated menu item:', oActive.id )
                            self._trigger_layout()

                        if not self.active_item:
                            self.active_item = item
                            item.on_hover( pos )
                            self._trigger_layout()
                            print( 'Activated menu item:', item.id )
                else:
                    return False
#                 leafItem = item
#                 while item not in self.items:
#                     item = item.menu.parent_menu_item
#
#                 # child menu item and leaf item are the same
#                 if leafItem.id is item.id:
#                     pass
#
#                 if item.menu:
#                     item.menu.on_mouse_move( window, pos )
#                 if self.active_item: # check if we are in a child overlap
#                     if self.collide_point( pos ):
#                         return self.active_item.menu.on_mouse_move( window, pos )
#
#                 nActive = self.item_at_pos( pos )
#                 if nActive: # could be in a boundary
#
#                     if not self.active_item or self.active_item.id is not nActive.id:
#                         if self.active_item:
#                             oActive = self.active_item
#                             Logger.debug( "Deactivate item %s", oActive.id )
#                             self.active_item = None
#                             oActive.on_hover_out( pos )
#                         Logger.debug( "Activate item %s", nActive.id )
#                         self.active_item = nActive
#                         r = self.active_item.on_hover( pos )
#                         self._do_layout()
#                         return r
            else:
                if not self.parent_menu_item or not self.parent_menu_item._is_active():
                    Logger.debug( 'Parent menu item is not active or mouse is outside us' )
                    print( self )
                    hide = True

            if hide:
                Logger.debug( 'Hide the menu' )
                print( self )
                self.hide()
                return True
        else:
            print( "Unbind us... now" )
            print( self )
            Window.unbind( mouse_pos = self.on_mouse_move )

    def show( self, x, y, widget ):
        if not self.visible:
            if len( self.items ) > 0:
                self.visible = True
                if not self.root_widget:
                    self.root_widget = self._findRootWiget( widget )
                print( 'root widget', self.root_widget )
                self.root_widget.add_widget( self )
                self._do_layout()
                self.pos = ( x - 10, y - self.height + 10 )
                Logger.debug( 'Opening menu at position' )
                Window.bind( mouse_pos = self.on_mouse_move )
            else:
                Logger.debug( 'No menu items in menu! Will not open' )
        else:
            Logger.debug( 'Menu already visible' )

    def hide( self ):
        if self.visible:
            self.visible = False
            Window.unbind( mouse_pos = self.on_mouse_move )
            self.root_widget.remove_widget( self )
            # hide child submenus
            for item in self.items:
                if item.menu:
                    item.menu.hide()

    def _findRootWiget( self, start_widget = None ):
        if self.root_widget is None:
            widget = start_widget
            while not isinstance( widget , WindowSDL ) and not isinstance( widget, WindowBase ) :
                widget = widget.parent

            return widget

        return self.root_widget
