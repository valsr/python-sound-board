"""
Created on Feb 19, 2017

@author: valsr <valsr@valsr.com>
"""
from abc import abstractmethod
import time
import uuid

from com.valsr.psb.ui.window.base import WindowBase
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.window.window_sdl2 import WindowSDL
from kivy.graphics import Color, Rectangle
from kivy.logger import Logger
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty, \
    AliasProperty, NumericProperty, ReferenceListProperty, VariableListProperty, BoundedNumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget


class MenuItem(Widget):
    """Menu item class"""

    __events__ = ("on_hover_over", "on_hover_out", "on_select")
    """Events:
        on_hover_over: When (continuously fired) the mouse is hovering over the menu item
        on_hover_out: When the mouse moves outside a menu item
        on_select: When a menu item has been selected
    """

    select_cb = ObjectProperty(None)
    """Selection callback. Called when the user selects a menu item"""

    hover_cb = ObjectProperty(None)
    """Hover callback. Called when the mouse hovers over the menu item"""

    menu = ObjectProperty(None)
    """Sub-menu associated with the menu item"""

    id = StringProperty(str(uuid.uuid1()))
    """Menu item id"""

    def __init__(self, **kwargs):
        """Constructor

        Args:
            kwargs: Named parameters
        """
        if self.__class__ is MenuItem:
            raise RuntimeError('You cannot use MenuItem directly.')
        self.parent_menu = None  # parent menu
        super().__init__(**kwargs)

    def on_hover_over(self, item, pos):
        """On hover event"""
        pass

    def on_hover_out(self, item, pos):
        """On hover out event"""
        pass

    def on_select(self, item, pos):
        """On select event"""
        pass

    def _on_hover_over(self, pos):
        """Handles menu item hover action

        Args:
            pos: Mouse current position
        """
        if self.menu:
            self.menu.show(self.pos[0] + self.width - 10, self.pos[1] + self.height - 10, self)

        return self.dispatch("on_hover_over", self, pos)

    def _on_hover_out(self, pos):
        """Handles on hover out action (hide the menu)

        Args:
            pos: Mouse current position
        """
        if self.menu:
            self.menu.hide()

        return self.dispatch("on_hover_out", self, pos)

    def _on_select(self, touch):
        """Handles selecting the menu

        Args:
            touch: Touch event that triggered the selection
        """
        return self.dispatch("on_select", self, touch)

    @abstractmethod
    def _calculate_minimum_size(self):
        """Calculate the minimum size of the widget/menu item to display

        Returns:
            (width, height)
        """
        pass

    def _is_active(self):
        if self.parent_menu:
            active_item = self.parent_menu.active_item
            return active_item and active_item.id == self.id

        return False

    def set_menu(self, menu):
        """Set the associated sub-menu with this menu item

        Args:
            menu: Menu to associated with
        """
        if menu and not isinstance(menu, Menu):
            raise RuntimeError('Menu must be an instance of Menu')

        if self.menu:
            self.menu.parent_menu_item = None

        self.menu = menu

        if self.menu:
            self.menu.parent_menu_item = self


class SimpleMenuItem(Label, MenuItem):
    """Simple label menu item based on kivy Label class"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _calculate_minimum_size(self):
        self.texture_update()
        return (self.texture_size[0], self.texture_size[1] + 12)


class Menu(BoxLayout):
    """UI Menu. This menu works only with WindowBase class as it attaches it self to that window (or top root window)"""

    __events__ = ("on_hover_over", "on_hover_out", "on_select", "on_open", "on_close")
    """Events:
        on_hover_over: When (continuously fired) the mouse is hovering over the menu item (will not fire if the menu
            item handled the event)
        on_hover_out: When the mouse moves outside a menu item (will not fire if the menu item handled the event)
        on_select: When a menu item has been selected (will not fire if the menu item handled the event)
        on_open: After the menu has been opened
        on_close: After the menu has been closed but before closing child menus
    """

    color = ListProperty([0.3, 0.3, 0.3, 0.75])
    """Background colour"""

    active_color = ListProperty([0.6, 0.6, 0.6, 0.85])
    """Menu item active colour"""

    border_color = ListProperty([0.75, 0.75, 0.75, 1])
    """Border colour"""

    selected_color = ListProperty([0.75, 0.75, 0.75, 1])
    """Selected menu colour"""

    padding = VariableListProperty([1])
    """Menu item padding"""

    spacing = NumericProperty(1)
    """Menu item spacing between items (in pixels)"""

    items = ListProperty([])
    """Menu items"""

    active_item = ObjectProperty(defaultvalue=None, allownone=True)
    """Current active menu item"""

    selected_item = ObjectProperty(defaultvalue=None, allownone=True)
    """Selected menu item"""

    parent_menu_item = ObjectProperty(defaultvalue=None, allownone=True)
    """Parent menu item if the this menu is a sub-menu"""

    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', size_hint=(None, None), ** kwargs)
        self._trigger_layout = Clock.create_trigger(self._do_layout, -1)
        self.visible = False
        self.root_widget = None
        trigger = self._trigger_layout
        self.fbind('pos', trigger)
        self.fbind('size', trigger)
        trigger()

    def add_menu_item(self, menu):
        """Add menu item

        Args:
            menu: Menu item to add

        Returns:
            Added menu item
        """
        if not isinstance(menu, MenuItem):
            raise RuntimeError('The menu must be a subclass of MenuItem')

        Logger.debug('Adding menu item %s', menu.id)

        self.items.append(menu)
        menu.parent_menu = self
        menu.size_hint = (None, None)

        if not menu.height or menu.height == 100:
            menu.height = 50

        menu.fbind('size', self._trigger_layout)
        if self.visible:
            self._trigger_layout()
        return menu

    def remove_menu_item(self, menu):
        """Remove menu item from the menu

        Args:
            menu: Menu item to remove
        """
        if not isinstance(menu, MenuItem):
            raise RuntimeError(
                'The menu must be a subclass of MenuItem')

        if menu in self.items:
            self.items.pop(menu)
            menu.funbind('size', self._trigger_layout)
            self._trigger_layout()

    def show(self, x, y, widget):
        """Show the menu item at given position

        Args:
            x: X coordinate
            y: y coordinate
            widget: Starting widget to search for appropriate window
        """
        if not self.visible:
            if len(self.items) > 0:
                Logger.debug('%s: Open menu at %d %d', self, x, y)
                if not self.root_widget:
                    self.root_widget = self._find_root_wiget(widget)
                self.root_widget.add_widget(self)
                self.visible = True
                self._do_layout()
                self.pos = (x - 10, y - self.height + 10)
                Logger.debug("%s: Bind windows event", self)
                Window.bind(mouse_pos=self.on_mouse_move)
                self.dispatch("on_open", self, x, y)
            else:
                Logger.debug('%s: No menu items in menu! Will not open', self)
        else:
            Logger.debug('%s: Menu already visible', self)

    def hide(self):
        """Hide menu"""
        if self.visible:
            self.visible = False
            Window.unbind(mouse_pos=self.on_mouse_move)
            self.root_widget.remove_widget(self)
            # hide child sub-menus
            for item in self.items:
                if item.menu:
                    item.menu.hide()
            self.dispatch("on_close", self)

    def item_at_pos(self, pos):
        """Return item at given position

        Args:
            pos: (x,y) position

        Returns:
            MenuItem or None

        Note:
            This function will not take occlusion into consideration - use collide_item instead.
        """
        if self.x <= pos[0] <= self.right:
            return self.item_at_y_pos(pos[1])

        return None

    def item_at_y_pos(self, y):
        """Return item at given y-coordinate

        Args:
            y: y coordinate

        Returns:
            MenuItem or None

        Note:
            This function will not take occlusion into consideration - use collide_item instead.
        """
        for item in self.items:
            if item.y <= y <= item.top:
                return item

    def collide_point(self, pos, self_only=True):
        """Check if given position is within the visible menu.

        Args:
            pos: Position tuple (x,y)
            self_only: Restrict checking to only self (see note)

        Returns:
            Boolean: if position is within the menu (see note)

        Note:
            If self_only is false then the function will check if the position is within itself and all visible
        children menu's (recursing of course). If self_only is true, then the check will only return true if the
        position is within it self but not within any children visible menus (i.e. the mouse pointer is uncovered and
        within the menu boundaries)
        """
        collide = False

        # loop through all children and through their children's children
        for i in self.items:
            if i.menu and i.menu.visible:
                if i.menu.collide_item(pos, self_only=False):
                    collide = True
                    break

        if not collide:
            if self.x <= pos[0] <= self.right and self.y <= pos[1] <= self.top:
                collide = True
        elif self_only:
            collide = False

        return collide

    def collide_item(self, pos, self_only=True):
        """Obtain the item that collides at the given position.

        Args:
            pos: Position tuple (x,y)
            self_only: Restrict checking to only self (see note).

        Returns:
            MeunItem or Menu: the item at the given position (Menu is returned when the position is within a
            separator)

        Note:
            If self_only is false then the function will check if the position is within itself and all visible
        children menu's (recursing of course). If self_only is true, then the check will only return true if the
        position is within it self but not within any children visible menus (i.e. the mouse pointer is uncovered and
        within the menu boundaries)
        """
        item = None  # the item corresponding at that position (either menu item or menu)

        # does any sub child element overshadow the current position
        for i in self.items:
            if i.menu and i.menu.visible:
                child = i.menu.collide_item(pos, self_only=False)
                if child:
                    item = child

        if not item:  # check self for item at position
            if self.x <= pos[0] <= self.right and self.y <= pos[1] <= self.top:
                item = self.item_at_y_pos(pos[1])
                if not item:  # still no item but within self
                    item = self
        elif self_only:  # child covering us, so position does not collide
            item = None

        return item

    def on_mouse_move(self, window, pos):
        """Handles mouse move events (used for responding to hover events):

        Args:
            window: Not used
            pos: Mouse position

        Returns:
            Boolean: Whether the event has been consumed/handled
        """
        if self.visible:
            hide = False

            item = self.collide_item(pos, False)
            if item:  # within visible menus bounds
                if self.collide_point(pos, True):
                    if isinstance(item, Menu):
                        if self.active_item:
                            previous_active = self.active_item
                            self.active_item = None
                            if not previous_active._on_hover_out(pos):
                                self.root_menu().dispatch("on_hover_out", previous_active, pos)
                    else:
                        if self.active_item and self.active_item.id is not item.id:
                            previous_active = self.active_item
                            self.active_item = None
                            if not previous_active._on_hover_out(pos):
                                self.root_menu().dispatch("on_hover_out", previous_active, pos)
                            Logger.debug('%s: De-activated menu item: %s', self, previous_active.id)
                            self._trigger_layout()

                        if not self.active_item:
                            self.active_item = item
                            if not item._on_hover_over(pos):
                                self.root_menu().dispatch("on_hover_over", self.active_item, pos)
                            self._trigger_layout()
                            Logger.debug('%s: Activated menu item: %s', self, item.id)
                else:
                    return False
            else:
                hide = True
                if self.parent_menu_item and self.parent_menu_item._is_active():
                    Logger.trace('%s: Parent menu item is active - prevent hiding', self)
                    hide = False

            if hide:
                Logger.debug('%s: Hide the menu', self)
                self.hide()
                return True
        else:
            Logger.debug("%s: Unbind windows event", self)
            Window.unbind(mouse_pos=self.on_mouse_move)

    def on_touch_down(self, touch):
        if self.visible:

            item = self.collide_item(touch.pos, True)
            if item:
                Logger.debug('%s: Item selected %s', self, item.id)

                if not item._on_select(touch):
                    # find the top-most menu parent
                    menu = self.root_menu()
                    menu.selected_item = item
                    menu.dispatch("on_select", menu, item)
                    menu.hide()

            return True

    def root_menu(self):
        """Obtain the root/top most menu

        Returns:
            Menu
        """
        top_most = self
        while top_most.parent_menu_item:
            top_most = top_most.parent_menu_item.parent_menu

        return top_most

    def _do_layout(self, *largs):
        if self.visible:
            self.clear_widgets()
            self._draw_background()

            height_padding = self.padding[1] + self.padding[3]
            width_padding = self.padding[0] + self.padding[2]
            min_width = 0
            min_height = 0
            for child in self.items:
                child.size = child._calculate_minimum_size()
                min_width = max(min_width, child.width)
                min_height += child.height + self.spacing

            # fix bottom height (no spacing)
            min_height -= self.spacing

            self.width = min_width + width_padding
            self.height = min_height + height_padding

            print(self.size)
            # fix child widths
            child_width = self.width - width_padding
            for child in self.items:
                child.width = child_width

            for child in self.items:
                self.add_widget(child)

    def _draw_background(self):
        self.canvas.clear()

        with self.canvas:
            Color(*self.border_color)
            Rectangle(pos=self.pos, size=self.size)

            Color(*self.color)
            padding = self.padding
            Rectangle(pos=(self.pos[0] + padding[0], self.pos[1] + padding[2]),
                      size=(self.size[0] - padding[0] - padding[2], self.size[1] - padding[1] - padding[3]))

            Color(*self.border_color)
            separator_height = self.height - self.padding[1]
            for child in self.items:
                separator_height -= child.height

                # selected child
                if self.active_item and child.id == self.active_item.id:
                    Color(*self.active_color)
                    Rectangle(pos=(self.pos[0] + padding[0], self.pos[1] + separator_height),
                              size=(self.size[0] - padding[0] - padding[2], child.height))
                    Color(*self.border_color)

                separator_height -= self.spacing
                Rectangle(pos=(self.pos[0] + self.padding[0], self.pos[1] + separator_height),
                          size=(self.size[0], self.spacing))

    def _find_root_wiget(self, start_widget=None):
        if self.root_widget is None:
            widget = start_widget
            while not isinstance(widget, WindowSDL) and not isinstance(widget, WindowBase):
                widget = widget.parent

            return widget

        return self.root_widget

    def on_hover_over(self, item, pos):
        """On hover event"""
        pass

    def on_hover_out(self, item, pos):
        """On hover out event"""
        pass

    def on_select(self, item, pos):
        """On select event"""
        pass

    def on_open(self, menu, x, y):
        """On open event"""
        pass

    def on_close(self, menu):
        """On close event"""
        pass
