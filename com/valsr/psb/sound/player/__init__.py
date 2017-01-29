'''
Created on Jan 17, 2017

@author: radoslav
'''
from abc import ABC, ABCMeta, abstractmethod
from builtins import property
from gi.repository import Gst, GObject
from kivy.clock import Clock
from kivy.logger import Logger
from numpy.distutils.environment import __metaclass__
import os
from threading import Thread
import time
import uuid

from com.valsr.psb.sound import PlayerState


_PLAYER_UPDATE_TIMEOUT_ = 0.2

class PlayerBase( object ):
    '''
    classdocs
    '''
    def __init__( self, id ):
        __metaclass__ = ABCMeta
        '''
        Constructor
        '''
        self.id_ = id
        self._init()
        self.__setUpPipeline()

    def _init( self ):
        self.state_ = PlayerState.NOTINIT
        self.error_ = None
        self.pipeline_ = None
        self.source_ = None
        self.sink_ = None
        self.updateCallbacks_ = {}
        self.messageCallbacks_ = {}
        self.messageThread_ = None
        self.run_ = True
        self._lastUpdate = time.time()

    @abstractmethod
    def _setUpPipeline( self ):
        pass

    def __setUpPipeline( self ):
        # pipeline
        self.pipeline_ = Gst.Pipeline.new( self.id_ + '_player' )

        self._setUpPipeline()

        self.state_ = PlayerState.READY

        self.messageThread_ = Thread( target = self.__messageLoop )
        self.messageThread_.daemon = True
        self.messageThread_.start()

    @abstractmethod
    def _messageLoop( self ):
        pass

    def __messageLoop( self, **kwargs ):
        global _PLAYER_UPDATE_TIMEOUT_
        nextUpdate = self._lastUpdate + _PLAYER_UPDATE_TIMEOUT_

        while self.run_:
            bus = self.pipeline_.get_bus()
            message = bus.peek()

            # call child loop
            self._messageLoop()
            if message:
                if message.type == Gst.MessageType.EOS:
                    self.__finish()
                elif message.type == Gst.MessageType.ERROR:
                    self.__finish()
                    self.state_ = PlayerState.ERROR
                    error, debug = message.parse_error()
                    self.error_ = "Error %s: %s" % ( error, debug )

                for key in self.messageCallbacks_:
                    if self.messageCallbacks_[key]( self, bus, message ):
                        Logger.debug( "Callback %s handled the event." % key )
                        break

            # call the update callbacks
            if time.time() > nextUpdate:
                for key in self.updateCallbacks_:
                    if self.updateCallbacks_[key]( self, 0 ):
                        Logger.debug( "Callback %s handled the event." % key )
                        break

                self._lastUpdate = time.time()
                nextUpdate = self._lastUpdate + _PLAYER_UPDATE_TIMEOUT_

    def registerUpdateCallback( self, cb ):
        id = str( uuid.uuid1().int )
        self.updateCallbacks_[id] = cb
        Logger.debug( "Registered callback by id %s" % id )
        return id

    def unregisterUpdateCallback( self, id ):
        if id in self.updateCallbacks_:
            del self.updateCallbacks_[id]
            Logger.debug( "Unregistered callback by id %s" % id )
        else:
            Logger.debug( "Unable to unregistered callback: %s not found" % id )

    def registerMessageCallback( self, cb ):
        id = str( uuid.uuid1().int )
        self.messageCallbacks_[id] = cb
        Logger.debug( "Registered callback by id %s" % id )
        return id

    def unregisterMessageCallback( self, id ):
        if id in self.messageCallbacks_:
            del self.messageCallbacks_[id]
            Logger.debug( "Unregistered callback by id %s" % id )
        else:
            Logger.debug( "Unable to unregistered callback: %s not found" % id )

    # Play back Functionality (override the non __ ones)
    def __finish( self ):
        self.finish()
        self.state_ = PlayerState.STOPPED
        Logger.debug( "Finished playing %s" % self.file_ )

    def finish( self ):
        pass

    def play( self ):
        pass

    def pause( self ):
        pass

    def stop( self ):
        pass

    def __stop( self, waitForStop = True ):
        self._stop()
        self.pipeline_.set_state( Gst.State.NULL )
        self.state_ = PlayerState.STOPPED

        self.pipeline_.get_state( Gst.CLOCK_TIME_NONE if waitForStop else 0 )
        Logger.debug( "Stopped playing %s" % self.file_ )

    def destroy( self ):
        self.__stop()
        self.run_ = False
        if self.messageThread_.is_alive():
            self.messageThread_.join( timeout = 2 )

        if self.messageThread_.is_alive():
            Logger.warning( "Unable to stop thread" )
        self.pipeline_ = None
        Logger.debug( "Destroyed player (%s)" % self.file_ )

    # Properties (select)
    @property
    def duration( self ):
        if self.state_ is PlayerState.PAUSED or self.state_ is PlayerState.PLAYING or self.state_ is PlayerState.READY or self.state_ is PlayerState.STOPPED:
            _, duration = self.pipeline_.query_duration( Gst.Format.TIME )
            return duration / Gst.SECOND

        return -1

    @property
    def position( self ):
        if self.state_ is PlayerState.PAUSED or self.state_ is PlayerState.PLAYING or self.state_ is PlayerState.READY or self.state_ is PlayerState.STOPPED:
            _, position = self.pipeline_.query_position( Gst.Format.TIME )
            return position / Gst.SECOND

        return -1

    @position.setter
    def position( self, position ):
        return self.pipeline_.seek_simple( Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, position * Gst.SECOND )

    @property
    def state( self ):
        return self.state_

    @property
    def error( self ):
        return self.error_

class FilePlayer( PlayerBase ):
    '''
    classdocs
    '''
    def __init__( self, id, file ):
        '''
        Constructor
        '''
        self.file_ = os.path.abspath( file )
        super().__init__( id )

    def _setUpPipeline( self ):
        # source
        self.source_ = Gst.ElementFactory.make( "filesrc", self.id_ + "_source" )
        self.source_.set_property( "location", self.file_ )
        self.pipeline_.add( self.source_ )

        # decoder
        self.decode_ = Gst.ElementFactory.make( "decodebin", self.id_ + "_decodebin" )
        self.pipeline_.add( self.decode_ )

        # sink
        self.sink_ = Gst.ElementFactory.make( "autoaudiosink", self.id_ + "_sink" )
        self.pipeline_.add( self.sink_ )

        # link static elements
        self.source_.link( self.decode_ )

        # decoder is dynamic so link at runtime
        self.decode_.connect( "pad-added", self._decodeSrcCreated )

    def _decodeSrcCreated( self, element, pad ):
        pad.link( self.sink_.get_static_pad( 'sink' ) )

    def _messageLoop( self ):
        pass

    def play( self ):
        if self.state_ is PlayerState.READY or self.state_ is PlayerState.PAUSED or self.state_ is PlayerState.STOPPED:
            self.pipeline_.set_state( Gst.State.PLAYING )
            Logger.debug( "Playing %s" % self.file_ )
            self.state_ = PlayerState.PLAYING
        elif self.state_ is PlayerState.PLAYING:
            Logger.debug( "Already playing %s" % self.file_ )
        else:
            Logger.debug( "Not in a state to play - %s" % self.state_.name )

    def pause( self ):
        if self.state_ is PlayerState.PLAYING:
            self.pipeline_.set_state( Gst.State.PAUSED )
            self.state_ = PlayerState.PAUSED
        else:
            Logger.debug( "Unable to pause since we are not playing" )

    def stop( self, waitForStop = True ):
        self.pipeline_.set_state( Gst.State.NULL )
        self.state_ = PlayerState.STOPPED

        self.pipeline_.get_state( Gst.CLOCK_TIME_NONE if waitForStop else 0 )
        Logger.debug( "Stopped playing %s" % self.file_ )
