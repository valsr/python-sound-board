'''
Created on Jan 13, 2017

@author: radoslav
'''
import gi
from kivy.app import App
from kivy.config import Config
from kivy.logger import Logger
from kivy.uix.floatlayout import FloatLayout

from com.valsr.psb import sound
from com.valsr.psb.ui.window import MainWindow


gi.require_version( 'Gst', '1.0' )


class PSB( App ):
    '''
    Main application
    '''

    def __init__( self, **kwargs ):
        App.__init__( self, **kwargs )
        self.theme = 'white'
        self.ui = None
        self.active_window = []
        self.window_order = []
        self._keyboard = None
        self.rebind_keyboard()

    def allowed_audio_files( self ):
        return ['.mp3', '.wav', '.flac', '.ogg', '.mp4']

    def _keyboard_closed( self ):
        self._keyboard.unbind( on_key_down = self._on_keyboard_down )
        self._keyboard = None
        Logger.debug( 'Keyboard closed' )

    def _on_keyboard_down( self, keyboard, keycode, text, modifiers ):
        print( keycode )
        return True

    def rebind_keyboard( self ):
        if not self._keyboard:
            # self._keyboard = Window.request_keyboard( self._keyboard_closed, self )
            # self._keyboard.bind( on_key_down = self._on_keyboard_down )
            Logger.debug( 'Keyboard bound' )

    def open_window( self, windowClass, **kwargs ):
        window = windowClass( controller = self )

        if 'size_hint' in kwargs:
            window.size_hint = kwargs['size_hint']

        if 'draggable' in kwargs:
            window.draggable = kwargs['draggable']

        if 'title' in kwargs:
            window.title = kwargs['title']

        if 'windowed' in kwargs:
            window.windowed = kwargs['windowed']

        # add to order
        self.window_order.append( window.id_ )
        window.open()

        self.rebind_keyboard()

        return window
    def on_window_open( self, window ):
        self.window_order.append( window.id_ )

    def on_window_close( self, window ):
        self.window_order.remove( window.id_ )
        self.rebind_keyboard()

    def theme_image_filename( self, name, size ):
        return "ui/fontawesome/%s/png/%d/%s.png" % ( self.theme, size, name )

    def build( self ):
        self.ui = FloatLayout()
        window = MainWindow( controller = self )
        window.draggable = 'None'
        window.title = 'PSB'
        window.open()
        return self.ui

    def get_uiroot( self ):
        return self.ui

    def to_window( self, x, y, initial, relative ):
        return ( x, y )

if __name__ == '__main__':
    from gi.repository import Gst
    sound.initAudio()
    version = Gst.version()
    Config.set( 'input', 'mouse', 'mouse,multitouch_on_demand' )
    Logger.info( "GStreamer version %d.%d.%d.%d" % version )
    PSB().run()
