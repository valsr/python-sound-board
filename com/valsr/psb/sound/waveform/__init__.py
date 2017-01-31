'''
Created on Jan 17, 2017

@author: radoslav
'''
from OpenGL.arrays import lists
from gi.repository import Gst, GObject
from kivy.clock import Clock
from kivy.logger import Logger
import math
import os
from threading import Thread
from time import sleep

from com.valsr.psb.sound.info import MediaInfoManager
from com.valsr.psb.sound.player import PlayerBase


class Waveform( PlayerBase ):
    def __init__( self, file, **kwargs ):
        self.file_ = os.path.abspath( file )
        self.lChannel_ = []
        self.rChannel_ = []
        self.readyToDraw_ = False
        self.level_ = None
        self.info_ = None
        self._loaded_ = False
        super().__init__( "waveform://" + file )

    def _setUpPipeline( self ):
        # source
        self.source_ = Gst.ElementFactory.make( "filesrc" )
        self.source_.set_property( "location", self.file_ )
        self.pipeline_.add( self.source_ )

        # decoder
        self.decode_ = Gst.ElementFactory.make( "decodebin" )
        self.pipeline_.add( self.decode_ )

        # level
        self.level_ = Gst.ElementFactory.make( "level" )
        self.level_.set_property( 'post-messages', True )

        self.pipeline_.add( self.level_ )

        # sink
        self.sink_ = Gst.ElementFactory.make( "fakesink" )
        self.pipeline_.add( self.sink_ )

        # link pad-always elements
        self.source_.link( self.decode_ )
        self.level_.link( self.sink_ )

        # decoder is dynamic so link at runtime
        self.decode_.connect( "pad-added", self._decodeSrcCreated )

    def _decodeSrcCreated( self, element, pad ):
        pad.link( self.level_.get_static_pad( 'sink' ) )

    @property
    def loaded_( self ):
        return self._loaded_

    @loaded_.setter
    def loaded_( self, value ):
        self._loaded_ = value

    def analyze( self, *args ):
        if not self.loaded_:
            if not self.info_:
                self.info_ = MediaInfoManager.getInfoForMedia( self.file_, True )
                Clock.schedule_once( self.analyze, 0.2 )
                return

            if self.info_.error_:
                raise RuntimeError( "Issues during loading media %s: %s %s" % ( self.info_.file_, self.info_.error_.src, self.info_.error_.message ) )

            self.level_.set_property( 'interval', math.ceil( self.info_.duration_ / self.numPoints() * Gst.SECOND ) )
            self.pipeline_.set_state( Gst.State.PLAYING )

    def _messageLoop( self, **kwargs ):
        bus = self.pipeline_.get_bus()
        message = bus.pop()
        if message is not None:
            structure = message.get_structure()
            if structure:
                if structure.get_name() == 'level':
                    rmsArray = structure.get_value( 'rms' )
                    startTime = structure.get_value( 'stream-time' )
                    if len( rmsArray ) > 1:
                        self.lChannel_.append( ( startTime / Gst.SECOND, pow( 10, rmsArray[0] / 20 ) ) )
                        self.rChannel_.append( ( startTime / Gst.SECOND, pow( 10, rmsArray[1] / 20 ) ) )
                    else:
                        print( "Single Channel Only" )
                        self.lChannel_.append( ( startTime / Gst.SECOND, pow( 10, rmsArray[0] / 20 ) ) )
                        self.rChannel_.append( ( startTime / Gst.SECOND, pow( 10, rmsArray[0] / 20 ) ) )
            if message.type == Gst.MessageType.EOS:
                if len( self.lChannel_ ) < self.numPoints():
                    self.lChannel_ += [[self.info_.duration_ + x / Gst.SECOND, 0] for x in range ( 0, self.numPoints() - len( self.lChannel_ ) )]
                if len( self.rChannel_ ) < self.numPoints():
                    self.rChannel_ += [[self.info_.duration_ + x / Gst.SECOND, 0] for x in range ( 0, self.numPoints() - len( self.rChannel_ ) )]

    def finish( self ):
        self.pipeline_.set_state( Gst.State.NULL )
        Logger.debug( "Finished loading waveform for %s", self.file_ )
        self.loaded_ = True

    def numPoints( self ):
        return 2000

    def pointInterval( self ):
        if self.loaded_():
            return self.info_.duration_ / self.numPoints()

        return None

    def getPoint( self, num ):
        if num < self.numPoints() and self.loaded_:
            return ( self.lChannel_[num][0], self.lChannel_[num][1], self.rChannel_[num][1] )

        return None
