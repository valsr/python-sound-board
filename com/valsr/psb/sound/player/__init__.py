'''
Created on Jan 17, 2017

@author: radoslav
'''
from abc import ABC, ABCMeta, abstractmethod
from gi.repository import Gst, GObject
from kivy.clock import Clock
from kivy.logger import Logger
from numpy.distutils.environment import __metaclass__
import os
from threading import Thread
import time
import uuid

from com.valsr.psb.sound import PlayerState


_PLAYER_UPDATE_TIMEOUT_ = 0.2 # Update timetout (for update callbacks)

class PlayerBase( object ):
    '''
    Base class for all player objects
    '''
    __metaclass__ = ABCMeta
    def __init__( self, id ):
        '''
        Constructor

        Parameters:
            id -- Player identifier
        '''
        self.id_ = id
        self.__init()
        self.__setUpPipeline()

    def __init( self ):
        '''
        Initialize all variables to their default state.
        '''
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
        self._init()

    def _init( self ):
        '''
        Initialize all variables to their default state (overriding classes)
        '''
        pass

    @abstractmethod
    def _setUpPipeline( self ):
        '''
        Set up the pipeline (overriding classes). This method is called once self.pipeline_ has been initialized and 
        before the main loop is started.
        Warning: do not override
        '''
        pass

    def __setUpPipeline( self ):
        '''
        Set up the pipeline
        '''
        self.pipeline_ = Gst.Pipeline.new( self.id_ + '_player' )

        self._setUpPipeline()

        self.state_ = PlayerState.READY

        self.messageThread_ = Thread( target = self.__messageLoop )
        self.messageThread_.daemon = True
        self.messageThread_.start()

    @abstractmethod
    def _messageLoop( self ):
        '''
        Message loop (overreding classes).
        '''
        pass

    def __messageLoop( self, **kwargs ):
        '''
        Message loop. Will call callbacks. 
        Warning: do not override
        '''
        global _PLAYER_UPDATE_TIMEOUT_
        nextUpdate = self._lastUpdate + _PLAYER_UPDATE_TIMEOUT_

        while self.run_:
            bus = self.pipeline_.get_bus()
            message = bus.peek()

            self._messageLoop() # call child loop
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
        '''
        Register update callback

        Parameters:
            cb -- callback

        Returns:
            callback identifier
        '''
        id = str( uuid.uuid1().int )
        self.updateCallbacks_[id] = cb
        Logger.debug( "Registered callback by id %s" % id )
        return id

    def unregisterUpdateCallback( self, id ):
        '''
        Unregister update callback

        Parameters:
            id -- Callback identifier

        Returns:
            Un-registration status
        '''
        if id in self.updateCallbacks_:
            del self.updateCallbacks_[id]
            Logger.debug( "Unregistered callback by id %s" % id )
            return True

        Logger.debug( "Unable to unregistered callback: %s not found" % id )
        return False

    def registerMessageCallback( self, cb ):
        '''
        Register message callback

        Parameters:
            cb -- callback

        Returns:
            callback identifier
        '''
        id = str( uuid.uuid1().int )
        self.messageCallbacks_[id] = cb
        Logger.debug( "Registered callback by id %s" % id )
        return id

    def unregisterMessageCallback( self, id ):
        '''
        Unregister message callback

        Parameters:
            id -- Callback identifier

        Returns:
            Un-registration status
        '''
        if id in self.messageCallbacks_:
            del self.messageCallbacks_[id]
            Logger.debug( "Unregistered callback by id %s" % id )
            return True

        Logger.debug( "Unable to unregistered callback: %s not found" % id )
        return False

    # Play back Functionality (override the non __ ones)
    def __finish( self ):
        '''
        Called when the stream finishes.
        Warning: do not override.
        '''
        self.finish()
        self.state_ = PlayerState.STOPPED
        Logger.debug( "Finished playing %s" % self.id_ )

    def finish( self ):
        pass

    def play( self ):
        pass

    def pause( self ):
        pass

    def stop( self ):
        pass

    def __stop( self, waitForStop = True ):
        '''
        Called to stop the stream (usually due to error). Note: will call stop() method first.

        Parameters:
            waitForStop -- Whether to wait for the player thread to exit or not (max 5 seconds)
        '''
        self.stop()
        self.pipeline_.set_state( Gst.State.NULL )
        self.state_ = PlayerState.STOPPED

        self.pipeline_.get_state( Gst.CLOCK_TIME_NONE if waitForStop else 0 )
        Logger.debug( "Stopped playing %s" % self.id_ )

    def destroy( self ):
        '''
        Called to terminate the player and free resources.
        '''
        self.__stop()
        self.run_ = False
        if self.messageThread_.is_alive():
            self.messageThread_.join( timeout = 2 )

        if self.messageThread_.is_alive():
            Logger.warning( "Unable to stop thread" )
        self.pipeline_ = None
        Logger.debug( "Destroyed player (%s)" % self.id_ )

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
    def state_( self ):
        return self._state_

    @state_.setter
    def state_( self, state ):
        self._state_ = state

    @property
    def error( self ):
        return self.error_

class FilePlayer( PlayerBase ):
    '''
    File player
    '''
    def __init__( self, id, file ):
        '''
        Constructor

        Parameters:
            id -- Player identifier
            file -- File (path) to play
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
