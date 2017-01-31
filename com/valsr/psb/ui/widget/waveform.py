'''
Created on Jan 22, 2017

@author: radoslav
'''
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Line
from kivy.logger import Logger
from kivy.properties import *
from kivy.uix.widget import Widget
from math import floor

from com.valsr.psb.sound.waveform import Waveform


class WaveformWidget( Widget ):
    '''
    classdocs
    '''
    file_ = StringProperty( "" )
    position_ = NumericProperty( 0.0 )
    autoscale_ = BooleanProperty( True )
    def __init__( self, **kwargs ):
        '''
        Constructor
        '''
        Widget.__init__( self, **kwargs )
        self._init()
        self.bind( pos = self._prepDraw )
        self.bind( size = self._prepDraw )
        self.updateCanvas()

    def _init( self ):
        self.waveform_ = None
        self.maxAmp_ = None
        self.readyToDraw_ = False
        self.lPoints_ = []
        self.rPoints_ = []
        self.player_ = None

    def updateCanvas( self, *args ):
        self.canvas.clear()

        offset = self.pos
        top = [offset[0] + self.width, offset[1] + self.height]
        with self.canvas:
            # background
            Color( 0, 0, 0, 0.0 )
            Rectangle( pos = offset, size = ( self.width, self.height ) )

            # borders and stuff
            Color( 0.443, 0.474, 0.509, 0.75 )
            Line( points = [offset[0], offset[1], top[0], offset[1], top[0], top[1], offset[0], top[1]], width = 1 )
            Line( points = [offset[0], offset[1] + self.height / 2, top[0], offset[1] + self.height / 2] )

            if self.readyToDraw_:
                Color( 0.203, 0.396, 0.643, 1 )
                Line( points = self.lPoints_ )
                Line( points = self.rPoints_ )

                # tracker
                pps = self.width / self.waveform_.info_.duration_
                pos = self.position_ if self.position_ != -1 else 0
                Color( 1, 1, 1, 0.75 )
                Line( points = [pos * pps + offset[0], offset[1], pos * pps + offset[0], offset[1] + self.height], width = 1 )

    def _convertToPoint( self, time, amp ):
        x = time * self.width / self.waveform_.info_.duration_
        y = amp * floor( ( self.height - 1 ) / 2 )

        return ( x, y )

    def on_file_( self, *args ):
        self._init()
        # load the wave form.. and get it displayed (maybe wait for it to build)
        wv = Waveform( args[1] )
        self.waveform_ = wv
        wv.analyze()
        self.loadWaveFormCallback()
        self.updateCanvas()

    def loadWaveFormCallback( self, *args ):
        if self.waveform_.loaded_:
            self._prepDraw()
        else:
            Clock.schedule_once( self.loadWaveFormCallback, 1 )

    def on_position_( self, *args ):
        self.updateCanvas()

    def on_autoscale_( self, *args ):
        self.updateCanvas()

    def _prepDraw( self, *args ):
        self.readyToDraw_ = False
        offset = self.pos
        if self.waveform_ is not None and self.waveform_.loaded_:
            lChannelPoints = []
            rChannelPoints = []
            ampMulti = 1

            # figure out max amplitude
            if self.maxAmp_ == None:
                ampList = []
                for i in range( 0, self.waveform_.numPoints() ):
                    wavePoint = self.waveform_.getPoint( i )
                    ampList.append( wavePoint[1] )
                    ampList.append( wavePoint[2] )
                    self.maxAmp_ = max( ampList )

            if self.autoscale_ and self.maxAmp_:
                ampMulti = 1 / self.maxAmp_

            midHeightOffset = offset[1] + self.height / 2
            for i in range( 0, self.waveform_.numPoints() ):
                wavePoint = self.waveform_.getPoint( i )
                pt = self._convertToPoint( wavePoint[0], wavePoint[1] )
                lChannelPoints.append( pt[0] + offset[0] )
                lChannelPoints.append( midHeightOffset )
                lChannelPoints.append( pt[0] + offset[0] )
                lChannelPoints.append( pt[1] * ampMulti + midHeightOffset )

                pt = self._convertToPoint( wavePoint[0], wavePoint[2] )
                rChannelPoints.append( pt[0] + offset[0] )
                rChannelPoints.append( midHeightOffset )
                rChannelPoints.append( pt[0] + offset[0] )
                rChannelPoints.append( -pt[1] * ampMulti + midHeightOffset )

            self.lPoints_ = lChannelPoints
            self.rPoints_ = rChannelPoints

            Logger.debug( "Canvas ready for drawing" )
            self.readyToDraw_ = True
        self.updateCanvas()

    def on_touch_down( self, touch ):
        if self.collide_point( *touch.pos ):
            if self.player_ and self.waveform_.info_:
                x = touch.pos[0] - self.pos[0]

                # convert x to position and seek to that position
                pps = self.width / self.waveform_.info_.duration_
                toPosition = x / pps

                self.player_.position = toPosition
            return True

    @property
    def player( self ):
        return self.player_

    @player.setter
    def player( self, player ):
        self.player_ = player
        # reset all the shit...
