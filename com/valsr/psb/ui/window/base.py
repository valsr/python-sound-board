"""
Created on Jan 14, 2017

@author: valsr <valsr@valsr.com>
"""
from abc import abstractmethod, ABCMeta
from enum import Enum
from kivy.graphics import Rectangle, Color
from kivy.properties import ListProperty, StringProperty, BooleanProperty, ObjectProperty, OptionProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
import uuid


__all__ = ('WindowBase', )


class WindowCloseState(Enum):
    """Window Close State"""
    CLOSE = 1
    CANCEL = 2
    OK = 3
    YES = 4
    NO = 5
    BUTTON_3 = 6


class WindowBase(FloatLayout):
    """Base class for all windows (other than the main window). Note that the base class inherits
    from the FloatLayout.

    Events
        on_open: Fired when the window is opened
        on_dismiss: Fired when the window is closed. If the callback returns True, the dismiss will be cancelled.
    """
    __metaclass__ = ABCMeta
    __events__ = ('on_open', 'on_dismiss')

    background_color = ListProperty([0, 0, 0, .8])
    """Background color in the format (r, g, b, a)"""

    border = ListProperty([3, 3, 3, 3])
    """Border width used for the window. It must be a list of four values: (top, right, bottom, left)."""

    padding = ListProperty([3, 3, 3, 3])
    """Border padding used for the window. It must be a list of four values: (top, right, bottom, left)."""

    title = StringProperty("Window")
    """Title for this window"""

    windowed = BooleanProperty(False)
    """Whether the window is windowed or full screened"""

    # Internals properties used for graphical representation.
    _parent = ObjectProperty(None, allownone=True)
    draggable = OptionProperty("Top", options=["All", "Top", "None"])
    """Whether the window is draggable. Can be one of the 'All', 'Top', 'None' option. Top will make the window
    draggable by the top label, 'All' will make the entire window draggable, 'None' will disable ability to drag the
    window"""

    def __init__(self, **kwargs):
        """Constructor

        Args:
            **kwargs: Class parameters
        """
        self.grab_offset = (0, 0)
        self.ui = None
        self.label = None
        self._close_state = WindowCloseState.CLOSE
        self.id = str(id(self))
        self.__dismiss_dispatched = False
        super().__init__(**kwargs)

    def on_pre_create(self):
        """Called before window creation"""
        pass

    def on_create(self):
        """Called after creation (during creation process)"""
        pass

    def create(self):
        """Create the main ui components of the class. This will call create_root_ui as needed

        Returns:
            self
        """
        if not self.ui:
            self.label = Label(text=self.title, height=30, size_hint_y=None, id='_windowTop')
            if self.windowed:
                self.label.text = self.title
            self.add_widget(self.label)
            self.ui = self.create_root_ui()
            self.ui.id = str(uuid.uuid1().hex)
            self.add_widget(self.ui)
        return self

    def on_destroy(self):
        """Called just before destroying the window object"""
        pass

    def open(self):
        """Call to open the window. This method is shorthand for calling WindowManager.open_window"""
        from com.valsr.psb.ui.window.manager import WindowManager
        WindowManager.open_window(self.id)

    def _open(self):
        """Perform opening functions - bindings, event dispatching

        Returns:
            self
        """
        if self._parent:
            self._parent.bind(on_resize=self._align_center)
            self.center = self._parent.center

        self.fbind('size', self._update_center)
        self.dispatch('on_open')
        self.__dismiss_dispatched = False
        return self

    def on_open(self):
        """Called once the window has been opened"""
        pass

    def _update_center(self, *args):
        """HACK DON'T REMOVE OR FOUND AND FIX THE ISSUE
        It seems that if we don't access to the centre before assigning a new value, no dispatch will be done >_>
        """
        if not self._parent:
            return
        self.center = self._parent.center

    def dismiss(self):
        """Call to dismiss/close the window. This method is shorthand for calling WindowManager.close_window"""
        from com.valsr.psb.ui.window.manager import WindowManager
        WindowManager.close_window(self.id)

    def _dismiss(self):
        """Executes the dismissal of the current window - it dispatches the on_dismiss event

        Returns:
            True if the window should not be dismissed (see WindowManager)
        """
        if not self.__dismiss_dispatched:
            self.__dismiss_dispatched = True
            from com.valsr.psb.ui.window.manager import WindowManager
            if not WindowManager.is_visible(self.id):
                return False

            return self.dispatch('on_dismiss')

    def on_dismiss(self):
        """Called when dismissing/closing the window.

        Returns:
            True if the close event has been handled and the window should not be closed
        """
        return False

    def on_size(self, *args):
        """Handles re-sizing of its self

        Args:
            *args: Positional arguments (not used)
        """
        self._align_center()
        self.draw_background()

    def _align_center(self, *args):
        """Aligns the window to be at the parent's centre"""
        if self._parent:
            self.center = self._parent.center
            self.ui.pos = self.pos
            # hack to re-size dark background on window re-size
            window = self._parent
            self._parent = None
            self._parent = window

    def on_touch_down(self, touch):
        """Handles touch down event. This method is needed for dragging the main window.

        Args:
            touch: Touch event

        Returns:
            True if the event has been handled, False otherwise
        """
        if self.draggable is not "None":
            if self.collide_point(*touch.pos):
                self.grab_offset = self.to_local(*touch.pos, relative=True)
                # check if we should really drag (in case of top)
                if self.draggable is not 'Top' or (self.height - self.grab_offset[1]) <= 30:
                    touch.grab(self)
                    return True

        super(WindowBase, self).on_touch_down(touch)
        return True

    def on_touch_move(self, touch):
        """Handles touch move event. This method is needed for dragging the main window.

        Args:
            touch: Touch event

        Returns:
            True if the event has been handled, False otherwise
        """
        if touch.grab_current is self:
            self.pos = touch.x - \
                self.grab_offset[0], touch.y - self.grab_offset[1]
            self.draw_background()
        else:
            super(WindowBase, self).on_touch_move(touch)
            return True

    def on_touch_up(self, touch):
        """Handles touch up event. This method is needed for dragging the main window.

        Args:
            touch: Touch event

        Returns:
            True if the event has been handled, False otherwise
        """
        if touch.grab_current is self:
            touch.ungrab(self)
            return True

        super(WindowBase, self).on_touch_up(touch)
        return True

    def on_title(self, _, value):
        """Title changes

        Args:
            *args: Positional arguments (not used)
        """
        if self.label:
            self.label.text = value

    def draw_background(self):
        """Draws the background of the window"""
        self.ui.pos = self.pos
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.background_color, mode='rgba')
            Rectangle(pos=self.pos, size=self.size)
            if self.windowed:
                Color(0.294, 0.596, 0.705, 1, mode='rgba')
                Rectangle(pos=(self.x, self.y + self.height),
                          size=(self.width, self.border[0]))  # TOP
                Rectangle(pos=(self.x + self.width, self.y),
                          size=(self.border[1], self.height + self.border[0]))  # RIGHT
                # BOTTOM
                Rectangle(
                    pos=(self.x, self.y), size=(self.width, self.border[2]))
                # LEFT
                Rectangle(
                    pos=(self.x, self.y), size=(self.border[3], self.height))

    @abstractmethod
    def create_root_ui(self):
        """Creates the root ui - implement this method and return a UI element

        Returns:
            Widget element
        """
        pass

    def root_ui(self):
        """Get the root ui for this window

        Returns:
            Widget (may return None in some cases)
        """
        return self.ui

    def get_ui(self, name):
        """Get window UI element by name

        Args:
            name: Identification of the UI element

        Returns:
            Widget or None
        """
        root = self.root_ui()

        if root is not None:
            return root.ids[name]

        return None

    @property
    def close_state(self):
        """Close state property getter

        Returns:
            WindowCloseState enum value
        """
        return self._close_state

    @close_state.setter
    def close_state(self, state):
        """Close state property setter

        Args:
            state: WindowCloseState enum value
        """
        self._close_state = state

    def parent_window(self):
        """Obtain the parent window/widget

        Returns:
            Widget or None
        """
        return self._parent
