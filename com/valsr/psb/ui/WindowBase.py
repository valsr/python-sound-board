'''
Created on Jan 14, 2017

@author: radoslav
'''
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
__all__ = ('WindowBase',)

from kivy.lang import Builder
from abc import abstractmethod, ABC, ABCMeta
from kivy.logger import Logger
from kivy.animation import Animation
from kivy.properties import *

class WindowBase(FloatLayout):
    __metaclass__ = ABCMeta
    '''WindowBase class. See module documentation for more information.

    :Events:
        `on_open`:
            Fired when the WindowBase is opened.
        `on_dismiss`:
            Fired when the WindowBase is closed. If the callback returns True,
            the dismiss will be canceled.
    '''
    attach_to = ObjectProperty(None)
    '''If a widget is set on attach_to, the view will attach to the nearest
    parent window of the widget. If none is found, it will attach to the
    main/global Window.

    :attr:`attach_to` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    background_color = ListProperty([1, 0, 0, .7])
    '''Background color in the format (r, g, b, a).

    :attr:`background_color` is a :class:`~kivy.properties.ListProperty` and
    defaults to [0, 0, 0, .7].
    '''

    background = StringProperty(
        'atlas://data/images/defaulttheme/modalview-background')
    '''Background image of the view used for the view background.

    :attr:`background` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/modalview-background'.
    '''

    border = ListProperty([16, 16, 16, 16])
    '''Border used for :class:`~kivy.graphics.vertex_instructions.BorderImage`
    graphics instruction. Used for the :attr:`background_normal` and the
    :attr:`background_down` properties. Can be used when using custom
    backgrounds.

    It must be a list of four values: (top, right, bottom, left). Read the
    BorderImage instructions for more information about how to use it.

    :attr:`border` is a :class:`~kivy.properties.ListProperty` and defaults to
    (16, 16, 16, 16).
    '''

    # Internals properties used for graphical representation.

    _anim_alpha = NumericProperty(0)

    _anim_duration = NumericProperty(.1)

    _window = ObjectProperty(None, allownone=True)

    __events__ = ('on_open', 'on_dismiss')
    
    windowed_ = True
    draggable_ = OptionProperty("Top", options=["All", "Top", "None"])
    grabOffset_ = (0, 0)

    def __init__(self, parent, **kwargs):
        self._parent = parent
        super().__init__(**kwargs)

    def _search_window(self):
        # get window to attach to
        window = None
        if self.attach_to is not None:
            window = self.attach_to.get_parent_window()
            if not window:
                window = self.attach_to.get_root_window()
        if not window:
            from kivy.core.window import Window
            window = Window
        return window

    def open(self, window = None, *largs):
        '''Show the view window from the :attr:`attach_to` widget. If set, it
        will attach to the nearest window. If the widget is not attached to any
        window, the view will attach to the global
        :class:`~kivy.core.window.Window`.
        '''
        if self._window is not None:
            Logger.warning('WindowBase: you can only open once.')
            return self
        # search window
        self._window = self._search_window()
        if not self._window:
            Logger.warning('WindowBase: cannot open view, no window found.')
            return self
        self._window.add_widget(self)
        self._window.bind(
            on_resize=self._align_center,
            on_keyboard=self._handle_keyboard)
        self.center = self._window.center
        self.fbind('size', self._update_center)
        self.create()
        a = Animation(_anim_alpha=1., d=self._anim_duration)
        a.bind(on_complete=lambda *x: self.dispatch('on_open'))
        a.start(self)
        return self

    def _update_center(self, *args):
        if not self._window:
            return
        # XXX HACK DONT REMOVE OR FOUND AND FIX THE ISSUE
        # It seems that if we don't access to the center before assigning a new
        # value, no dispatch will be done >_>
        self.center = self._window.center

    def dismiss(self, *largs, **kwargs):
        '''Close the view if it is open. If you really want to close the
        view, whatever the on_dismiss event returns, you can use the *force*
        argument:
        ::

            view = WindowBase(...)
            view.dismiss(force=True)

        When the view is dismissed, it will be faded out before being
        removed from the parent. If you don't want animation, use::

            view.dismiss(animation=False)

        '''
        if self._window is None:
            return self
        if self.dispatch('on_dismiss') is True:
            if kwargs.get('force', False) is not True:
                return self
        if kwargs.get('animation', True):
            Animation(_anim_alpha=0., d=self._anim_duration).start(self)
        else:
            self._anim_alpha = 0
            self._real_remove_widget()
        return self

    def on_size(self, instance, value):
        self._align_center()

    def _align_center(self, *l):
        if self._window:
            self.center = self._window.center
            # hack to resize dark background on window resize
            _window = self._window
            self._window = None
            self._window = _window

    def on_touch_down(self, touch):
        if self.draggable_ is not "None":
            self.grabOffset_ = self.ui_.to_local(*touch.pos, relative=True)
            
            if self.ui_.collide_point(*self.grabOffset_):
                # check if we should really drag (in case of top)
                if self.draggable_ is not 'Top' or (self.ui_.height - self.grabOffset_[1]) <= 30:
                    print(self.grabOffset_)
                    touch.grab(self)
                    return True
        
        super(WindowBase, self).on_touch_down(touch)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.ui_.pos = touch.x - self.grabOffset_[0], touch.y - self.grabOffset_[1]
        else:
            super(WindowBase, self).on_touch_move(touch)
            return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            return True
        
        super(WindowBase, self).on_touch_up(touch)
        return True

    def on__anim_alpha(self, instance, value):
        if value == 0 and self._window is not None:
            self._real_remove_widget()

    def _real_remove_widget(self):
        if self._window is None:
            return
        self._window.remove_widget(self)
        self._window.unbind(
            on_resize=self._align_center,
            on_keyboard=self._handle_keyboard)
        self._window = None

    def on_open(self):
        pass

    def on_dismiss(self):
        pass

    def _handle_keyboard(self, window, key, *largs):
        if key == 27 and self.auto_dismiss:
            self.dismiss()
            return True
   
    controller_ = None
    ui_ = None
    
    
    def build(self):
        pass
    
    def show(self):
        pass
    
    @abstractmethod
    def getRootUI(self):
        pass
    
    def create(self):
        if self.ui_ == None:
            # build the display
            self.ui_ = GridLayout(cols = 1)
            self.ui_.rows_minimum = {0:30}
            self.ui_.add_widget(Label(text='Window', height = 30, size_hint_y = None, id = '_windowTop'))
            r = self.getRootUI()
            self.ui_.add_widget(r)
#             self.ui_ = r
            self.ui_.size_hint = self.size_hint
        
        return self.ui_
    
    def destroy(self):
        pass      
