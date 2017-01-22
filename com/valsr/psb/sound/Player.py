'''
Created on Jan 17, 2017

@author: radoslav
'''
from gi.repository import Gst
from com.valsr.psb.sound.Util import PlayerState
from kivy.logger import Logger
import os
from kivy.clock import Clock

_PLAYER_MESSAGE_LIMIT_ = 10
class Player(object):
    '''
    classdocs
    '''
 
    file_ = None
    state_ = PlayerState.NOTINIT
    time_ = 0
    error_ = None
    pipeline_ = None
    source_ = None
    sink_ = None
    id_ = None
    updatecallbacks_ = []
    messageCallbacks_ = []
     
    def __init__(self, id, file):
        '''
        Constructor
        '''
        self.file_ = os.path.abspath(file)
        self.id_ = id
        self._setUpPipeline()
    
    def _setUpPipeline(self):
        self.pipeline_ = Gst.Pipeline.new(self.id_ + '_player')

        # creating the filesrc element, and adding it to the pipeline
        self.source_ = Gst.ElementFactory.make("filesrc", self.id_ + "_source")
        self.source_.set_property("location", self.file_)
        self.pipeline_.add(self.source_)
        
        # creating and adding the decodebin element , an "automagic" element able to configure itself to decode pretty much anything
        self.decode_ = Gst.ElementFactory.make("decodebin", self.id_ + "_decodebin")
        self.pipeline_.add(self.decode_)
        # connecting the decoder's "pad-added" event to a handler: the decoder doesn't yet have an output pad (a source), it's created at runtime when the decoders starts receiving some data
        self.decode_.connect("pad-added", self._decodeSrcCreated) 
        
        # setting up (and adding) the alsasin, which is actually going to "play" the sound it receives
        self.sink_ = Gst.ElementFactory.make("autoaudiosink", self.id_ + "_sink")
        self.pipeline_.add(self.sink_)

        # linking elements one to another (here it's just the filesrc - > decoder link , the decoder -> sink link's going to be set up later)
        self.source_.link(self.decode_)
        self.state_ = PlayerState.READY
        
    def _decodeSrcCreated(self, element, pad):
        pad.link(self.sink_.get_static_pad('sink'))
   
    def registerCallback(self):
        if self.state_ == PlayerState.PLAYING or self.state_ == PlayerState.PAUSED:
            Clock.schedule_once(self.messageLoop, 1)
        
    def messageLoop(self, delta):
        global _PLAYER_MESSAGE_LIMIT_
        # check for messages
        bus = self.pipeline_.get_bus()
        
        # check upto 10 messages
        for i in range(0, _PLAYER_MESSAGE_LIMIT_):
            message = bus.pop()
            if message == None:
                break
            
            self.onMessage(bus, message)
            for cb in self.messageCallbacks_:
                if cb(bus, message):
                    self.registerCallback()
                    return
        
        # call the update callbacks
        for cb in self.updatecallbacks_:
            if cb(delta):
                self.registerCallback()
                return
        
        self.registerCallback()
             
    def onMessage(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.onFinish(bus)
        elif t == Gst.MessageType.ERROR:
            self.onFinish(bus)
            self.state_ = PlayerState.ERROR
            error, debug = message.parse_error()
            self.error_ = "Error %s: %s" % (error, debug)
     
    def getState(self):
        return self.state_
     
    def getLastError(self):
        return self.error_
     
    def onFinish(self, bus):
        self.state_ = PlayerState.STOPPED
        Logger.debug("Finished playing %s" % self.file_)
         
    def play(self):
        if self.state_ is PlayerState.READY or self.state_ is PlayerState.PAUSED or self.state_ is PlayerState.STOPPED:
            self.pipeline_.set_state(Gst.State.PLAYING)
            Logger.debug("Playing %s" % self.file_)
            self.state_ = PlayerState.PLAYING
            self.registerCallback()
        elif self.state_ is PlayerState.PLAYING:
            Logger.debug("Already playing %s" % self.file_)
        else:
            Logger.debug("Not in a state to play - %s" % self.state_.name)
      
    def pause(self):
        if self.state_ is PlayerState.PLAYING:
            self.pipeline_.set_state(Gst.State.PAUSED)
            self.state_ = PlayerState.PAUSED
        else:
            Logger.debug("Unable to pause since we are not playing")
               
    def stop(self):
        if self.state_ == PlayerState.PLAYING:
            self.pipeline_.set_state(Gst.State.PAUSED)
            self.state_ = PlayerState.PAUSED
         
        if self.state_ == PlayerState.PAUSED or self.state_ == PlayerState.READY:
            self.pipeline_.set_state(Gst.State.NULL)
            self.state_ = PlayerState.STOPPED
             
        Logger.debug("Stopped playing %s" % self.file_)
     
    def destroy(self):
        self.stop()
        self.pipeline_ = None
        Logger.debug("Destroyed player (%s)" % self.file_)

    def queryPos(self):
        if self.state_ is PlayerState.PAUSED or self.state_ is PlayerState.PLAYING:
            ret, current = self.pipeline_.query_position(Gst.Format.TIME)
            return current/Gst.SECOND
        
        return -1
    
    def queryTime(self):
        if self.state_ is PlayerState.PAUSED or self.state_ is PlayerState.PLAYING or self.state_ is PlayerState.READY or self.state_ is PlayerState.STOPPED:
            ret, current = self.pipeline_.query_duration(Gst.Format.TIME)
            return current/Gst.SECOND
        
        return -1