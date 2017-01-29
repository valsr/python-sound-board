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


class Waveform():
    def __init__( self, file, **kwargs ):
        self.file_ = os.path.abspath( file )
        self.lChannel_ = []
        self.rChannel_ = []
        self.readyToDraw_ = False
        self.error_ = None
        self.pipeline_ = None
        self.source_ = None
        self.level_ = None
        self.sink_ = None
        self.messageThread_ = None
        self.run_ = True
        self.done_ = False
        self.info_ = None

    def isReady( self ):
        return self.done_

    def _waitForInfo( self, *args ):
        if not self.info_:
            self.info_ = MediaInfoManager.getInfoForMedia( self.file_, True )

            if not self.info_:
                Clock.schedule_once( self._waitForInfo, 0.2 )
                return

        self.analyse()

    def analyse( self ):
        if not self.done_:
            if not self.info_:
                self._waitForInfo()
                return

            if self.info_.error_:
                raise RuntimeError( "Issues during loading media %s: %s %s" % ( self.info_.file_, self.info_.error_.src, self.info_.error_.message ) )

            # pipeline
            self.pipeline_ = Gst.Pipeline.new()

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
            # we need 1000 points at most so make only than many
            self.level_.set_property( 'interval', math.ceil( self.info_.duration_ / self.numPoints() * Gst.SECOND ) )
            self.pipeline_.add( self.level_ )

            # sink
            self.sink_ = Gst.ElementFactory.make( "fakesink" )
            self.pipeline_.add( self.sink_ )

            # link pad-always elements
            self.source_.link( self.decode_ )
            self.level_.link( self.sink_ )

            # decoder is dynamic so link at runtime
            self.decode_.connect( "pad-added", self._decodeSrcCreated )

            self.messageThread_ = Thread( target = self.messageLoop )
            self.messageThread_.daemon = True
            self.messageThread_.start()
            self.pipeline_.set_state( Gst.State.PLAYING )

    def _decodeSrcCreated( self, element, pad ):
        pad.link( self.level_.get_static_pad( 'sink' ) )

    def messageLoop( self, **kwargs ):
        while self.run_:
            # check for messages
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
                    self.done_ = True
                    self.run_ = False

        self.pipeline_.set_state( Gst.State.NULL )
        Logger.debug( "Finished loading waveform for %s", self.file_ )


    def numPoints( self ):
        return 2000

    def pointInterval( self ):
        if self.isReady():
            return self.info_.duration_ / self.numPoints()

        return None

    def getPoint( self, num ):
        if num < self.numPoints() and self.isReady():
            return ( self.lChannel_[num][0], self.lChannel_[num][1], self.rChannel_[num][1] )

        return None
