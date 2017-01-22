'''
Created on Jan 13, 2017

@author: radoslav
'''
import gi
from kivy.app import App
from kivy.logger import Logger
from kivy.uix.floatlayout import FloatLayout

from com.valsr.psb.sound import util
from com.valsr.psb.ui.window import MainWindow

gi.require_version( 'Gst', '1.0' )


class PSB( App ):

    def __init__( self, **kwargs ):
        App.__init__( self, **kwargs )
        self.theme_ = 'white'
        self.ui_ = None
        self.activeWindow_ = []

    def getAllowedAudioFiles( self ):
        return ['.mp3', '.wav', '.flac', '.ogg', '.mp4']

    def on_keyoard( self, window, key, *largs ):
        return True

    def openWindow( self, windowClass, **kwargs ):
        window = windowClass( controller = self )

        if 'size_hint' in kwargs:
            window.size_hint = kwargs['size_hint']

        if 'draggable' in kwargs:
            window.draggable = kwargs['draggable']

        if 'title' in kwargs:
            window.title = kwargs['title']

        if 'windowed' in kwargs:
            window.windowed = kwargs['windowed']

        window.open()

        return window

    def getThemeImageFilename( self, name, size ):
        return "ui/fontawesome/%s/png/%d/%s.png" % ( self.theme_, size, name )

    def build( self ):
        self.ui_ = FloatLayout()
        self.openWindow( MainWindow, draggable = 'None', title = 'PSB' )
        return self.ui_

    def getUIRoot( self ):
        return self.ui_

if __name__ == '__main__':
    from gi.repository import Gst
    version = Gst.version()
    Logger.info( "GStreamer version %d.%d.%d.%d" % version )
    util.initAudio()
    PSB().run()
