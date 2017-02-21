"""
Created on Jan 17, 2017

@author: valsr <valsr@valsr.com>
"""
from abc import ABC, ABCMeta, abstractmethod
import os
from threading import Thread
import time
import uuid
from gi.repository import Gst, GObject

from com.valsr.psb.callback import CallbackRegister
from com.valsr.psb.sound import PlayerState
from kivy.clock import Clock
from kivy.logger import Logger


_PLAYER_UPDATE_TIMEOUT_ = 0.2
"""Timeout between player updates (callbacks)"""


class PlayerBase(CallbackRegister):
    """Base class for all player objects"""
    __metaclass__ = ABCMeta

    def __init__(self, player_id):
        """Constructor"""
        super().__init__()

        self.id = player_id
        self._state = PlayerState.NOTINIT
        self._error = None
        self.error_debug = None
        self.pipeline = None
        self.source = None
        self.sink = None
        self.message_thread = None
        self.run_ = True
        self._last_update = time.time()

        self.__init()
        self.__set_up_pipeline()

    def __init(self):
        """Initialize all variables to their default state."""
        self._state = PlayerState.NOTINIT
        self._error = None
        self.error_debug = None
        self.pipeline = None
        self.source = None
        self.sink = None
        self.message_thread = None
        self.run_ = True
        self._last_update = time.time()
        self._init()

    def _init(self):
        """Initialize all variables to their default state (overriding classes)"""
        pass

    @abstractmethod
    def _set_up_pipeline(self):
        """Set up the pipeline (overriding classes). This method is called once self.pipeline_ has been initialized and
        before the main loop is started.
        Warning: do not override
        """
        pass

    def __set_up_pipeline(self):
        """Set up the pipeline"""
        self.pipeline = Gst.Pipeline.new(self.id + '_player')

        self._set_up_pipeline()

        self.state = PlayerState.READY

        self.message_thread = Thread(target=self.__message_loop)
        self.message_thread.daemon = True
        self.message_thread.start()

    @abstractmethod
    def _message_loop(self):
        """Message loop (overriding classes)"""
        pass

    def __message_loop(self, **kwargs):
        """Message loop. Will call callbacks.
        Warning: do not override
        """
        global _PLAYER_UPDATE_TIMEOUT_
        next_update = self._last_update + _PLAYER_UPDATE_TIMEOUT_

        while self.run_:
            bus = self.pipeline.get_bus()
            message = bus.peek()

            self._message_loop()  # call child loop
            if message:
                if message.type == Gst.MessageType.EOS:
                    self.__finish()
                elif message.type == Gst.MessageType.ERROR:
                    self.__finish()
                    self.state = PlayerState.ERROR
                    error, debug = message.parse_error()
                    self._error = error
                    self.error_debug = debug
                ret = self.call('message', None, True, player=self, bus=bus, message=message)
                if ret:
                    Logger.debug("Callback %s handled the event." % ret)

            # call the update callbacks
            if time.time() > next_update:
                ret = self.call('update', None, True, player=self, delta=0)
                if ret:
                    Logger.debug("Callback %s handled the event." % ret)

                self._last_update = time.time()
                next_update = self._last_update + _PLAYER_UPDATE_TIMEOUT_

    def register_update_callback(self, cb):
        """Register update callback

        Args:
            cb: callback

        Returns:
            callback identifier
        """
        return self.register_callback('update', cb)

    def unregister_update_callback(self, player_id):
        """Unregister update callback

        Args:
            player_id: Callback identifier

        Returns:
            Registration removal status
        """
        return self.unregister_callback(player_id, callback_type='update')

    def register_message_callback(self, cb):
        """Register message callback

        Args:
            cb: callback

        Returns:
            callback identifier
        """
        return self.register_callback('message', cb)

    def unregister_message_callback(self, player_id):
        """Unregister message callback

        Args:
            player_id: Callback identifier

        Returns:
            Registration removal status
        """
        return self.unregister_callback(player_id, callback_type='message')

    def __finish(self):
        """Called when the stream finishes.
        Warning: do not override.
        """
        self.finish()
        self.state = PlayerState.STOPPED
        Logger.debug("Finished playing %s" % self.id)

    def finish(self):
        """Called when stream finished playing (end of stream)"""
        pass

    def play(self):
        """Called when the stream starts/resume playing"""
        pass

    def pause(self):
        """Called when the stream is paused"""
        pass

    def stop(self, wait_for_stop=True):
        """Called when the stream is stopped

        Args:
            wait_for_stop: Whether to wait for the 
        """
        pass

    def __stop(self, wait_for_stop=True):
        """Called to stop the stream (usually due to _error). Note: will call stop() method first.

        Args:
            wait_for_stop: Whether to wait for the player thread to exit or not (max 5 seconds)
        """
        self.stop()
        self.pipeline.set_state(Gst.State.NULL)
        self.state = PlayerState.STOPPED

        self.pipeline.get_state(Gst.CLOCK_TIME_NONE if wait_for_stop else 0)
        Logger.debug("Stopped playing %s" % self.id)

    def destroy(self):
        """Called to terminate the player and free resources."""
        self.__stop()
        self.run_ = False
        if self.message_thread.is_alive():
            self.message_thread.join(timeout=2)

        if self.message_thread.is_alive():
            Logger.warning("Unable to stop thread")
        self.pipeline = None
        Logger.debug("Destroyed player (%s)" % self.id)

    # Properties (select)
    @property
    def duration(self):
        """Duration property getter"""
        if self.state is PlayerState.PAUSED or self.state is PlayerState.PLAYING or \
                self.state is PlayerState.READY or self.state is PlayerState.STOPPED:
            _, duration = self.pipeline.query_duration(Gst.Format.TIME)
            return duration / Gst.SECOND

        return -1

    @property
    def position(self):
        """Position property getter"""
        if self.state is PlayerState.PAUSED or self.state is PlayerState.PLAYING or \
                self.state is PlayerState.READY or self.state is PlayerState.STOPPED:
            _, position = self.pipeline.query_position(Gst.Format.TIME)
            return position / Gst.SECOND

        return -1

    @position.setter
    def position(self, position):
        """Position property setter"""
        return self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                         position * Gst.SECOND)

    @property
    def state(self):
        """State property getter"""
        return self._state

    @state.setter
    def state(self, state):
        """State property setter"""
        self._state = state

    @property
    def error(self):
        """Error property getter"""
        return self._error


class FilePlayer(PlayerBase):
    """File player"""

    def __init__(self, file):
        """Constructor

        Args:
            file: File (path) to play
        """
        self.file = os.path.abspath(file)
        super().__init__("file://" + file)

    def _set_up_pipeline(self):
        # source
        self.source = Gst.ElementFactory.make("filesrc", self.id + "_source")
        self.source.set_property("location", self.file)
        self.pipeline.add(self.source)

        # decoder
        self.decode = Gst.ElementFactory.make("decodebin", self.id + "_decodebin")
        self.pipeline.add(self.decode)

        # sink
        self.sink = Gst.ElementFactory.make("autoaudiosink", self.id + "_sink")
        self.pipeline.add(self.sink)

        # link static elements
        self.source.link(self.decode)

        # decoder is dynamic so link at runtime
        self.decode.connect("pad-added", self._decode_src_created)

    def _decode_src_created(self, element, pad):
        pad.link(self.sink.get_static_pad('sink'))

    def _message_loop(self):
        pass

    def play(self):
        if self.state is PlayerState.READY or self.state is PlayerState.PAUSED or self.state is PlayerState.STOPPED:
            self.pipeline.set_state(Gst.State.PLAYING)
            Logger.debug("Playing %s" % self.file)
            self.state = PlayerState.PLAYING
        elif self.state is PlayerState.PLAYING:
            Logger.debug("Already playing %s" % self.file)
        else:
            Logger.debug("Not in a state to play - %s" % self.state.name)

    def pause(self):
        if self.state is PlayerState.PLAYING:
            self.pipeline.set_state(Gst.State.PAUSED)
            self.state = PlayerState.PAUSED
        else:
            Logger.debug("Unable to pause since we are not playing")

    def stop(self, wait_for_stop=True):
        self.pipeline.set_state(Gst.State.NULL)
        self.state = PlayerState.STOPPED

        self.pipeline.get_state(Gst.CLOCK_TIME_NONE if wait_for_stop else 0)
        Logger.debug("Stopped playing %s" % self.file)
