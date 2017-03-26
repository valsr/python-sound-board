"""
Created on Feb 4, 2017

@author: valsr <valsr@valsr.com>
"""
from kivy.core.window.window_sdl2 import WindowSDL
from kivy.logger import Logger
from kivy.properties import ObjectProperty, BooleanProperty, NumericProperty
from kivy.uix.widget import Widget
from com.valsr.psb.ui.widget.droppable import Droppable
import copy
from kivy.clock import Clock
from kivy.uix.label import Label


class Draggable(Widget):
    """Draggable class interface.

    The lifecycle (and important steps) of dragging follows the following:
    1. Touch down: Mouse event
        stores touch event in drag_touch
        stores touch offset in drag_offset
        register selection timer (drag_select_timeout)

    2. Selection: Timer event
        unschedule drag selection timer
        dispatches on_drag_select event

    3. Start dragging: Dragging starts immediately after drag selecting or after min_drag_offset
        calls drag select (if not yet selected, see above)
        calls init_drag method (if false then resets drag status and resumes normal operations)
        detaches from parent (drag_detach)
            this will set the drag_parent and call drag_detach method. drag_detach must return the UI to use for moving
            around (could be self). This will be stored in drag_ui
        dispatches on_drag

    4. Dragging:
        moves drag_ui to new mouse position
        calls on_hover for each widget that is under the mouse position
        calls on_hover_out for each widget that was but no longer is under the mouse position (see Droppable for more
        information)

    5. Touch up: Mouse event, and only after a touch down has been issued
        dispatches on_drag_release
        drop the widget at the current position (will backwards iterate - children first then their parents - over
        widgets of the Droppable interface and the first one to accept will trigger on_drop
        if no widgets accept the drop, then it will drop at the original parent widget (if possible) or issue an error
    """

    __events__ = ('on_drag_select', 'on_drag_release', 'on_drag', 'on_drop')

    draggable = BooleanProperty(True)
    """Whether _dragging is enabled"""

    min_drag_offset = NumericProperty(30)
    """Minimum drag distance before drag stars"""

    draggable_bound_window = ObjectProperty(defaultvalue=None, allownone=True)
    """Bound _dragging to this window"""

    draggable_bound_window_class = ObjectProperty(defaultvalue=WindowSDL, allownone=False)
    """Bound _dragging to this window class"""

    drag_data = ObjectProperty(defaultvalue=None, allownone=True)
    """Drag bounded data"""

    drag_select_timeout = NumericProperty(0.4)
    """Timeout from selecting widget to starting drag. In seconds"""

    drag_ui = ObjectProperty(defaultvalue=Label(text="Drag Me"), allownone=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._reset_drag()

    def _reset_drag(self):
        self._drag_touch = None
        self._drag_offset = ()
        self._drag_select_timer = None
        self._dragging = False
        self._drag_detached = False
        self.drag_ui = Label(text="Drag Me")
        self._drag_parent = None
        self._drag_selected = False
        self.drag_data = None
        self._hover_list = ()

    @property
    def drag_touch(self):
        return self._drag_touch

    @property
    def drag_offset(self):
        return self._drag_offset

    @property
    def dragging(self):
        return self._dragging

    @property
    def drag_detached(self):
        return self._drag_detached

    @property
    def drag_parent(self):
        return self._drag_parent

    @property
    def drag_selected(self):
        return self._drag_selected

    def on_touch_down(self, touch):
        if not touch.grab_current and self.draggable:
            self._drag_touch = copy.deepcopy(touch)
            touch.grab(self)
            self._drag_offset = self.to_local(touch.pos[0], touch.pos[1], True)
            self._drag_select_timer = Clock.schedule_once(self._drag_select, self.drag_select_timeout)
            return True

    def _drag_select(self, *args):
        if self._drag_select_timer:
            Clock.unschedule(self._drag_select_timer)

        if not self.drag_selected:
            Logger.debug("Select drag element")
            self._drag_selected = True
            self.dispatch('on_drag_select', self, self._drag_touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            grab_pos = self._drag_touch.pos
            distance = abs(touch.pos[0] - grab_pos[0]) + abs(touch.pos[1] - grab_pos[1])
            if not self.dragging:
                if distance > self.min_drag_offset:  # begin _dragging
                    if not self.drag_selected:
                        self._drag_select()
                    self._start_drag(touch)
            else:
                mouse_pos = self.to_window(touch.pos[0], touch.pos[1])
                self.drag_ui.pos = (mouse_pos[0] - self._drag_offset[0], mouse_pos[1] - self._drag_offset[1])
                print("pos:", mouse_pos, self.drag_ui.pos)
                print("size:", self.size, self.drag_ui.size)
                self._issue_hover_over(touch, self.parent)
                self._issue_hover_out(touch)

    def _start_drag(self, touch):
        if not self.init_drag():
            Logger.debug("Drag prevented by init_drag")
            touch.ungrab(self)
            self._reset_drag()
        else:
            self._detach(touch)
            self.dispatch('on_drag', self, touch)
            self._dragging = True

    def _detach(self, touch):
        Logger.debug("Detaching widget")

        root_widget = self._find_root_wiget()
        self._drag_parent = self.parent

        self.drag_ui = self.drag_detach()

        # cast position to window position
        window_pos = self.to_window(touch.pos[0], touch.pos[1])
        if self.drag_ui:  # keep as drag_ui since we drag_ui can return self as ui
            Logger.debug("Detached from parent")
            root_widget.add_widget(self.drag_ui)
            self._drag_detached = True

            # figure out the position
            self.drag_ui.pos = window_pos
        else:
            Logger.debug("Prevented form detaching from parent")

    def set_drag_ui(self, ui):
        parent = self.drag_ui.parent
        parent.remove_widget(self.drag_ui)
        self.drag_ui = ui
        parent.add_widget(self.drag_ui)

    def drag_detach(self):
        """Detach from parent widget

        Returns:
            widget: Widget to use for _dragging (UI)
            None: Detach was unsuccessful or prevent from detaching

        Notes:
            Remember to detach from the parent widget if detaching
        """
        self.drag_parent.remove_widget(self)
        self.drag_parent._trigger_layout()
        return self

    def on_touch_up(self, touch):
        if touch.grab_current is self and touch.button == 'left':
            Logger.debug("Drag touch up event")
            self.dispatch("on_drag_release", self, touch)
            touch.ungrab(self)

            if self.dragging:
                dropped = False
                parent = self.parent
                self.parent.remove_widget(self)

                # note even though we get the collide list in proper order (child first, parent second), at this point
                # we are not checking for z-values so it is possible that the drop goes to the wrong widget
                collide_list = self._get_collide_list(touch.pos[0], touch.pos[1], parent)
                collide_list.reverse()
                for widget in collide_list:
                    if widget._drop(self, touch):
                        self.dispatch('on_drop', self, widget, touch)
                        dropped = True
                        break
                    elif not widget.drop_propagate:
                        break

                # if not, drop back to original parent
                if not dropped:
                    Logger.debug('No drop recipients, returning to original parent')
                    if isinstance(self.drag_parent, Droppable) and not self.drag_parent._drop(self, touch):
                        raise RuntimeError('Previous parent rejected us!!!')
                    self.dispatch('on_drop', self, self.drag_parent, touch)
            self._reset_drag()

    def _find_root_wiget(self):
        if self.draggable_bound_window:
            parent = self.parent
            while not isinstance(parent.parent, WindowSDL) and parent is not self.draggable_bound_window:
                parent = parent.parent
            return parent
        else:
            parent = self.parent
            while not isinstance(parent.parent, self.draggable_bound_window_class):
                parent = parent.parent
            return parent

        return None

    #
    # Events
    #
    def on_drag_select(self, draggable, touch):
        pass

    def on_drop(self, draggable, droppable, touch):
        pass

    def on_drag(self, draggable, touch):
        pass

    def on_drag_release(self, draggable, touch):
        pass

    def init_drag(self):
        """Initialize _dragging (before the drag begins). Usually perform any UI related swaps

        Returns:
            False: Prevent/stop _dragging
            True: Initialization is ready and drag may begin
        """
        return self.draggable

    def drag_release(self, touch):
        """Fired when a touch up event has been received while _dragging

        Args:
            touch: Touch event
        """
        pass

    def _issue_hover_over(self, touch, root):
        collide_list = self._get_collide_list(touch.pos[0], touch.pos[1], root)
        collide_list.reverse()

        # now call each widget
        first = True
        hover_list = []
        exposed_only_hover_out = []
        for widget in collide_list:
            if isinstance(widget, Droppable):
                if first or not widget.drop_exposed_only:
                    widget.on_hover(self, touch)
                    hover_list.append(widget)
                elif widget.drop_exposed_only:
                    exposed_only_hover_out.append(widget)
                first = False

                if not widget.drop_propagate:
                    break

        # find out which widgets are hovered out
        for widget in self._hover_list:
            if widget not in hover_list:
                if widget in exposed_only_hover_out:
                    # deal with the case that drop_child_out
                    if widget.drop_child_out:
                        widget.on_hover_out(self, touch)
                    else:
                        hover_list.append(widget)
                else:
                    widget.on_hover_out(self, touch)

        self._hover_list = hover_list

    def _get_collide_list(self, x, y, widget):
        collide = []
        if isinstance(widget, Droppable) and widget is not self:
            if widget.collide_point(x, y):
                collide.append(widget)

        x, y = widget.to_local(x, y)
        for child in widget.children:
            collide.extend(self._get_collide_list(x, y, child))

        return collide

    def _issue_hover_out(self, touch):
        pass
