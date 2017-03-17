"""
Created on Feb 4, 2017

@author: valsr <valsr@valsr.com>
"""
from kivy.core.window.window_sdl2 import WindowSDL
from kivy.logger import Logger
from kivy.properties import ObjectProperty, BooleanProperty, NumericProperty
from kivy.uix.widget import Widget
from com.valsr.psb.ui.widget.droppable import Droppable


class Draggable(Widget):
    """Draggable class interface"""

    __events__ = ('on_drag', 'on_drop')

    draggable = BooleanProperty(True)
    """Whether dragging is enabled"""

    draggable_offset = NumericProperty(30)
    """Minimum drag distance before drag stars"""

    draggableBoundWindow = ObjectProperty(defaultvalue=None, allownone=True)
    """Bound dragging to this window"""

    draggableBoundWindowClass = ObjectProperty(defaultvalue=WindowSDL, allownone=False)
    """Bound dragging to this window class"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._grab_pos = ()
        self._grab_offset = ()
        self._detached = False
        self._drag = False
        self._original_parent = None
        self.drag_data = None
        self._hover_list = ()

    def on_touch_down(self, touch):
        if not touch.grab_current and self.draggable:
            Logger.debug("Grab started")
            touch.grab(self)
            self._grab_pos = touch.pos
            self._grab_offset = self.to_local(touch.pos[0], touch.pos[1], True)
            return True

    def _detach(self, touch):
        Logger.debug("Initating drag")
        if not self.init_drag():
            Logger.debug("Drag prevented by init_drag")
            touch.ungrab(self)
            return True

        root_widget = self._find_root_wiget()
        size = self.size
        self._original_parent = self.parent

        # do detach or copy
        if self.drag_detach_parent():
            Logger.debug("Detached from parent")
            root_widget.add_widget(self)
            self._detached = True
            self.size_hint = (None, None)
            self.size = size
        else:
            Logger.debug("Prevented form detaching from parent")

        self.dispatch('on_drag', self, touch)
        self._drag = True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            distance = abs(touch.pos[0] - self._grab_pos[0]) + abs(touch.pos[1] - self._grab_pos[1])
            if not self._drag:
                if distance > self.draggable_offset:
                    self._detach(touch)
            else:
                self.pos = (touch.pos[0] - self._grab_offset[0], touch.pos[1] - self._grab_offset[1])
                self._issue_hover_over(touch, self.parent)
                self._issue_hover_out(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self and touch.button == 'left':
            Logger.debug('grab ended')
            touch.ungrab(self)

            if self._drag:
                # find what is under
                dropped = False
                parent = self.parent
                self.parent.remove_widget(self)
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
                    if not self._original_parent._drop(self, touch):
                        raise RuntimeError('Previous parent rejected us!!!')
                    self.dispatch('on_drop', self, self._original_parent, touch)

                self._detached = False
                self._drag = False

    def _find_root_wiget(self):
        if self.draggableBoundWindow:
            parent = self.parent
            while not isinstance(parent.parent, WindowSDL) and parent is not self.draggableBoundWindow:
                parent = parent.parent
            return parent
        else:
            parent = self.parent
            while not isinstance(parent.parent, self.draggableBoundWindowClass):
                parent = parent.parent
            return parent

        return None

    def on_drop(self, draggable, droppable, touch):
        pass

    def on_drag(self, draggable, touch):
        pass

    def init_drag(self):
        return self.draggable

    def drag_detach_parent(self):
        self._original_parent.remove_widget(self)
        self._original_parent._do_layout()
        return True

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
