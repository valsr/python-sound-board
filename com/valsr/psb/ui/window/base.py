'''
Created on Jan 14, 2017

@author: radoslav
'''
from abc import abstractmethod, ABCMeta
from enum import Enum
from kivy.graphics import Rectangle, Color
from kivy.logger import Logger
from kivy.properties import *
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
import uuid


__all__ = ( 'WindowBase', )

class WindowCloseState( Enum ):
    CLOSE = 1
    CANCEL = 2
    OK = 3
    YES = 4
    NO = 5
    BUTTON_3 = 6

class WindowBase( GridLayout ):
    __metaclass__ = ABCMeta
    '''WindowBase class. See module documentation for more information.

    :Events:
        `on_open`:
            Fired when the WindowBase is opened.
        `on_dismiss`:
            Fired when the WindowBase is closed. If the callback returns True,
            the dismiss will be canceled.
    '''
    __events__ = ( 'on_open', 'on_dismiss' )
    background_color = ListProperty( [0, 0, 0, .8] )
    '''Background color in the format (r, g, b, a).
    
    :attr:`background_color` is a :class:`~kivy.properties.ListProperty` and
    defaults to [0, 0, 0, .7].
    '''
    border = ListProperty( [3, 3, 3, 3] )
    '''Border used for :class:`~kivy.graphics.vertex_instructions.BorderImage`
    graphics instruction. Used for the :attr:`background_normal` and the
    :attr:`background_down` properties. Can be used when using custom
    backgrounds.
    
    It must be a list of four values: (top, right, bottom, left). Read the
    BorderImage instructions for more information about how to use it.
    
    :attr:`border` is a :class:`~kivy.properties.ListProperty` and defaults to
    (16, 16, 16, 16).
    '''
    title = StringProperty( "Window" )
    # Internals properties used for graphical representation.
    _parent = ObjectProperty( None, allownone = True )
    draggable = OptionProperty( "Top", options = ["All", "Top", "None"] )

    def __init__( self, controller, **kwargs ):
        self.windowed = False
        self.grabOffset_ = ( 0, 0 )
        self.ui_ = None
        self.label_ = None
        self.controller_ = controller
        self._parent = controller.getUIRoot()
        self.id_ = uuid.uuid1()
        self._closeState_ = WindowCloseState.CLOSE
        self.opened_ = False
        super().__init__( **kwargs )

    def open( self, *largs ):
        if self.opened_:
            Logger.warning( 'WindowBase: you can only open once.' )
            return self

        if not self._parent:
            Logger.warning( 'WindowBase: cannot open view, no window found.' )
            return self

        self.create()
        self._parent.add_widget( self )
        self._parent.bind( 
            on_resize = self._align_center )
        self.center = self._parent.center
        self.fbind( 'size', self._update_center )
        self.controller_.onWindowOpen( self )
        self.dispatch( 'on_open' )
        return self

    def _update_center( self, *args ):
        if not self._parent:
            return
        # XXX HACK DONT REMOVE OR FOUND AND FIX THE ISSUE
        # It seems that if we don't access to the center before assigning a new
        # value, no dispatch will be done >_>
        self.center = self._parent.center

    def dismiss( self, *largs, **kwargs ):
        if self._parent is None:
            return self

        if self.dispatch( 'on_dismiss' ) is True:
            if kwargs.get( 'force', False ) is not True:
                return self

        self.controller_.onWindowClose( self )
        self._real_remove_widget()
        return self

    def on_size( self, instance, value ):
        self._align_center()
        self.drawBackground()

    def _align_center( self, *l ):
        if self._parent:
            self.center = self._parent.center
            # hack to resize dark background on window resize
            window = self._parent
            self._parent = None
            self._parent = window

    def on_touch_down( self, touch ):
        if self.draggable is not "None":
            if self.collide_point( *touch.pos ):
                self.grabOffset_ = self.to_local( *touch.pos, relative = True )
                # check if we should really drag (in case of top)
                if self.draggable is not 'Top' or ( self.height - self.grabOffset_[1] ) <= 30:
                    touch.grab( self )
                    return True

        super( WindowBase, self ).on_touch_down( touch )
        return True

    def on_touch_move( self, touch ):
        if touch.grab_current is self:
            self.pos = touch.x - self.grabOffset_[0], touch.y - self.grabOffset_[1]
            self.drawBackground()
        else:
            super( WindowBase, self ).on_touch_move( touch )
            return True

    def on_touch_up( self, touch ):
        if touch.grab_current is self:
            touch.ungrab( self )
            return True

        super( WindowBase, self ).on_touch_up( touch )
        return True

    def on__anim_alpha( self, instance, value ):
        if value == 0 and self._parent is not None:
            self._real_remove_widget()

    def _real_remove_widget( self ):
        if self._parent is None:
            return
        self._parent.remove_widget( self )
        self._parent.unbind( 
            on_resize = self._align_center )
        self._parent = None

    def on_open( self ):
        pass

    def on_dismiss( self ):
        pass

    def create( self ):
        if self.ui_ == None:
            self.cols = 1
            self.label_ = Label( text = self.title, height = 30, size_hint_y = None, id = '_windowTop' )
            if self.windowed:
                self.label_.text = self.title
                self.padding = ( self.border[3], self.border[0], self.border[1], self.border[2] )
            self.add_widget( self.label_ )
            self.ui_ = self.createRootUI()
            self.ui_.id = str( uuid.uuid1().hex )
            self.add_widget( self.ui_ )
            self.onPostCreate()
        return self

    def on_title( self, *args ):
        if self.label_:
            self.label_.text = args[1]

    def destroy( self ):
        pass

    def drawBackground( self ):
        self.canvas.before.clear()
        with self.canvas.before:
            Color( *self.background_color, mode = 'rgba' )
            Rectangle( pos = self.pos, size = self.size )
            if self.windowed:
                self.padding = ( self.border[3], self.border[0], self.border[1], self.border[2] )
                Color( 0.294, 0.596, 0.705, 1, mode = 'rgba' )
                Rectangle( pos = ( self.x, self.y + self.height ), size = ( self.width, self.border[0] ) ) # TOP
                Rectangle( pos = ( self.x + self.width, self.y ), size = ( self.border[1], self.height + self.border[0] ) ) # RIGHT
                Rectangle( pos = ( self.x, self.y ), size = ( self.width, self.border[2] ) ) # BOTTOM
                Rectangle( pos = ( self.x, self.y ), size = ( self.border[3], self.height ) ) # LEFT

    @abstractmethod
    def createRootUI( self ):
        pass

    def onPostCreate( self ):
        pass

    def getRootUI( self ):
        return self.ui_

    def getUI( self, uiID ):
        root = self.getRootUI()

        if root is not None:
            return root.ids[uiID]

        return None

    @property
    def closeState_( self ):
        return self._closeState_

    @closeState_.setter
    def closeState_( self, state ):
        self._closeState_ = state
