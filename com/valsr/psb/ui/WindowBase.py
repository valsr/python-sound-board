'''
Created on Jan 14, 2017

@author: radoslav
'''
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Rectangle, Color 
import uuid
__all__ = ('WindowBase',)

from abc import abstractmethod, ABCMeta
from kivy.logger import Logger
from kivy.properties import *

class WindowBase(GridLayout):
    __metaclass__ = ABCMeta
    '''WindowBase class. See module documentation for more information.

    :Events:
        `on_open`:
            Fired when the WindowBase is opened.
        `on_dismiss`:
            Fired when the WindowBase is closed. If the callback returns True,
            the dismiss will be canceled.
    '''
    background_color = ListProperty([0, 0, 0, .8])
    '''Background color in the format (r, g, b, a).

    :attr:`background_color` is a :class:`~kivy.properties.ListProperty` and
    defaults to [0, 0, 0, .7].
    '''

    border = ListProperty([3, 3, 3, 3])
    '''Border used for :class:`~kivy.graphics.vertex_instructions.BorderImage`
    graphics instruction. Used for the :attr:`background_normal` and the
    :attr:`background_down` properties. Can be used when using custom
    backgrounds.

    It must be a list of four values: (top, right, bottom, left). Read the
    BorderImage instructions for more information about how to use it.

    :attr:`border` is a :class:`~kivy.properties.ListProperty` and defaults to
    (16, 16, 16, 16).
    '''
    title = StringProperty("Window")
    # Internals properties used for graphical representation.
    window_ = ObjectProperty(None, allownone=True)
    __events__ = ('on_open', 'on_dismiss')
    windowed = False
    draggable = OptionProperty("Top", options=["All", "Top", "None"])
    grabOffset_ = (0, 0)
    ui_ = None
    label_ = None
    controller_ = None

    def __init__(self, controller, **kwargs):
        self.controller_ = controller
        self._parent = controller.getUIRoot()
        super().__init__(**kwargs)

    def open(self, *largs):
        '''Show the view window from the :attr:`attach_to` widget. If set, it
        will attach to the nearest window. If the widget is not attached to any
        window, the view will attach to the global
        :class:`~kivy.core.window.Window`.
        '''
        if self.window_ is not None:
            Logger.warning('WindowBase: you can only open once.')
            return self
        # search window
        self.window_ = self.controller_.getUIRoot()  # self._search_window()
        if not self.window_:
            Logger.warning('WindowBase: cannot open view, no window found.')
            return self
        self.create()
        self.window_.add_widget(self)
        self.window_.bind(
            on_resize=self._align_center,
            on_keyboard=self._handle_keyboard)
        self.bindActions(self.controller_)
        self.center = self.window_.center
        self.fbind('size', self._update_center)
        self.dispatch('on_open')
        return self

    def _update_center(self, *args):
        if not self.window_:
            return
        # XXX HACK DONT REMOVE OR FOUND AND FIX THE ISSUE
        # It seems that if we don't access to the center before assigning a new
        # value, no dispatch will be done >_>
        self.center = self.window_.center

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
        if self.window_ is None:
            return self
        if self.dispatch('on_dismiss') is True:
            if kwargs.get('force', False) is not True:
                return self
        self._real_remove_widget()
        return self

    def on_size(self, instance, value):
        self._align_center()
        self.drawBackground()

    def _align_center(self, *l):
        if self.window_:
            self.center = self.window_.center
            # hack to resize dark background on window resize
            window = self.window_
            self.window_ = None
            self.window_ = window

    def on_touch_down(self, touch):
        if self.draggable is not "None":
            if self.collide_point(*touch.pos):
                self.grabOffset_ = self.to_local(*touch.pos, relative=True)
                # check if we should really drag (in case of top)
                if self.draggable is not 'Top' or (self.height - self.grabOffset_[1]) <= 30:
                    touch.grab(self)
                    return True
        
        super(WindowBase, self).on_touch_down(touch)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.pos = touch.x - self.grabOffset_[0], touch.y - self.grabOffset_[1]
            self.drawBackground()
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
        if value == 0 and self.window_ is not None:
            self._real_remove_widget()

    def _real_remove_widget(self):
        if self.window_ is None:
            return
        self.window_.remove_widget(self)
        self.unbindActions(self.controller_)
        self.window_.unbind(
            on_resize=self._align_center,
            on_keyboard=self._handle_keyboard)
        self.window_ = None

    def on_open(self):
        pass

    def on_dismiss(self):
        pass

    def _handle_keyboard(self, window, key, *largs):
        print ('hy')
        if key == 27 and self.auto_dismiss:
            self.dismiss()
            return True
      
    def create(self):
        if self.ui_ == None:
            self.cols = 1
            self.label_ = Label(text=self.title, height=30, size_hint_y=None, id='_windowTop')
            if self.windowed:
                self.label_.text = self.title
                self.padding = (self.border[3], self.border[0],self.border[1],self.border[2])
            self.add_widget(self.label_)
            self.ui_ = self.createRootUI()
            self.ui_.id = str(uuid.uuid1().hex)
            self.add_widget(self.ui_)
                
        return self
    
    def on_title(self, *args):
        if self.label_:
            self.label_.text = args[1]
                
    def destroy(self):
        pass      
    
    def drawBackground(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.background_color, mode='rgba')
            Rectangle(pos=self.pos, size=self.size)
            if self.windowed:
                self.padding = (self.border[3], self.border[0],self.border[1],self.border[2])
                Color(0.294, 0.596, 0.705, 1, mode='rgba')
                Rectangle(pos=(self.x, self.y+self.height), size=(self.width, self.border[0])) # TOP
                Rectangle(pos=(self.x+self.width, self.y), size=(self.border[1], self.height+self.border[0])) #RIGHT
                Rectangle(pos=(self.x, self.y), size=(self.width, self.border[2])) # BOTTOM
                Rectangle(pos=(self.x, self.y), size=(self.border[3], self.height)) # LEFT

    @abstractmethod
    def createRootUI(self):
        pass
    
    def getRootUI(self):
        return self.ui_
    
    def bindActions(self, controller):
        pass
    
    def unbindActions(self, controller):
        pass
    
    def getUI(self, uiID):
        root = self.getRootUI()
        
        if root is not None:
            return root.ids[uiID]
        
        return None