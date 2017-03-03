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
    """Minimum drag distance before drag statrs"""

    draggableBoundWindow = ObjectProperty(defaultvalue=None, allownone=True)
    """Bound dragging to this window"""

    draggableBoundWindowClass = ObjectProperty(defaultvalue=WindowSDL, allownone=False)
    """Bound dragging to this window class"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._grab_pos = ()
        self._grab_offset = ()
        self._detached = False
        self._original_parent = None

    def on_touch_down(self, touch):
        if not touch.grab_current and self.draggable:
            Logger.debug('grab started')
            touch.grab(self)
            self._grab_pos = touch.pos
            self._grab_offset = self.to_local(touch.pos[0], touch.pos[1], True)
            self.dispatch('on_drag', self, touch)
            return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            distance = abs(touch.pos[0] - self._grab_pos[0]) + abs(touch.pos[1] - self._grab_pos[1])
            if not self._detached:
                if distance > self.draggable_offset:
                    Logger.debug('detaching')
                    root_widget = self._find_root_wiget()
                    size = self.size
                    self._original_parent = self.parent

                    # do detach or copy
                    self._tree.remove_node(self)
                    self._original_parent._do_layout()

                    # re-attach
                    root_widget.add_widget(self)
                    self._detached = True
                    self.size_hint = (None, None)
                    self.size = size
            else:
                self.pos = (touch.pos[0] - self._grab_offset[0], touch.pos[1] - self._grab_offset[1])
                for widget in self.parent.walk():
                    if widget is not self:
                        if isinstance(widget, Droppable):
                            x, y = widget.to_widget(*touch.pos)
                            if widget.collide_point(x, y):
                                if widget._drag_over(self, touch):
                                    break

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            Logger.debug('grab ended')
            touch.ungrab(self)

            if self._detached:
                # find what is under
                dropped = False
                parent = self.parent
                self.parent.remove_widget(self)
                for widget in parent.walk():
                    if isinstance(widget, Droppable):
                        x, y = widget.to_widget(*touch.pos)
                        if widget.collide_point(x, y):
                            if widget._drop(self, touch):
                                self.dispatch('on_drop', self, widget, touch)
                                dropped = True
                                break

                # if not, drop back to original parent
                if not dropped:
                    Logger.debug('No drop recipients, returning to original parent')
                    if not self._original_parent._drop(self, touch):
                        raise RuntimeError('Previous parent rejected us!!!')
                    self.dispatch('on_drop', self, self._original_parent, touch)

                self._detached = False

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
