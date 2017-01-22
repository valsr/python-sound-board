'''
Created on Jan 22, 2017

@author: radoslav
'''
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Line
from kivy.logger import Logger
from kivy.properties import *
from kivy.uix.widget import Widget

from com.valsr.psb.sound.waveform import Waveform


class WaveformWidget( Widget ):
    '''
    classdocs
    '''
    file_ = StringProperty( "" )
    def __init__( self, **kwargs ):
        '''
        Constructor
        '''
        Widget.__init__( self, **kwargs )

        self.waveform_ = None

        self.bind( pos = self.updateCanvas )
        self.bind( size = self.updateCanvas )
        self.updateCanvas()

    def updateCanvas( self, *args ):
        self.canvas.clear()

        # background
        offset = self.pos
        top = [offset[0] + self.width, offset[1] + self.height]
        with self.canvas:
            Color( 0, 0, 0, 0.0 )
            Rectangle( pos = offset, size = ( self.width, self.height ) )
            Color( 0.443, 0.474, 0.509, 0.75 )
            Line( points = [offset[0], offset[1], top[0], offset[1], top[0], top[1], offset[0], top[1]], width = 1 )
            Line( points = [offset[0], offset[1] + self.height / 2, top[0], offset[1] + self.height / 2] )

            if self.waveform_ is not None:
                # get points and draw them
                pass
        Logger.debug( "Update canvas. Size is %d, %d" % ( self.width, self.height ) )

    def on_file_( self, *args ):
        # load the wave form.. and get it displayed (maybe wait for it to build)
        wv = Waveform( args[1] )
        self.waveform_ = wv
        self.loadWaveFormCallback()

    def loadWaveFormCallback( self, *args ):
        if self.waveform_.isReady():
            self.updateCanvas()
        else:
            Clock.schedule_once( self.loadWaveFormCallback, 1 )
