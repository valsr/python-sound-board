'''
Created on Jan 28, 2017

@author: radoslav
'''
from gi.repository import Gst
from kivy.logger import Logger
import os
from threading import Thread
from time import sleep


class MediaInfoManager( object ):

    mediaInfo_ = {}
    loading_ = []
    def __init__( self, *args, **kwargs ):
        '''
        Constructor
        '''
    @staticmethod
    def getInfoForMedia( file, reloadError = False ):
        if file not in MediaInfoManager.loading_:
            if file in MediaInfoManager.mediaInfo_:
                info = MediaInfoManager.mediaInfo_[file]
                if not ( info.error_ and reloadError ):
                    return MediaInfoManager.mediaInfo_[file]

            Logger.debug( "No media information found for %s", file )
            # Queue loading
            MediaInfoManager.loading_.append( file )
            loader = MediaInfoLoader( file )
            loader.analyse( MediaInfoManager._loadedInfo )

        return None

    @staticmethod
    def _loadedInfo( info ):
        infoStruc = MediaInfo()
        infoStruc.duration_ = info.duration_
        infoStruc.file_ = info.file_
        infoStruc.error_ = info.error_
        infoStruc.errorDebug_ = info.errorDebug_
        MediaInfoManager.mediaInfo_[info.file_] = infoStruc
        MediaInfoManager.loading_.remove( infoStruc.file_ )

class MediaInfo( object ):
    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self.duration_ = 0
        self.file_ = None
        self.error_ = None
        self.errorDebug_ = None

class MediaInfoLoader( object ):
    def __init__( self, file, **kwargs ):
        self.file_ = os.path.abspath( file )
        self.lChannel_ = []
        self.rChannel_ = []
        self.readyToDraw_ = False
        self.error_ = None
        self.errorDebug_ = None
        self.run_ = True
        self.done_ = False
        self.duration_ = 0

        # player needed items
        self.pipeline_ = None
        self.source_ = None
        self.level_ = None
        self.sink_ = None
        self.messageThread_ = None
        self.callback_ = None

    def isReady( self ):
        return self.done_

    def analyse( self, callback ):
        if not self.done_:
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
            self.level_.set_property( 'interval', 100 * Gst.MSECOND )
            self.pipeline_.add( self.level_ )

            # sink
            self.sink_ = Gst.ElementFactory.make( "fakesink" )
            self.pipeline_.add( self.sink_ )

            # link pad-always elements
            self.source_.link( self.decode_ )
            self.level_.link( self.sink_ )

            # decoder is dynamic so link at runtime
            self.decode_.connect( "pad-added", self._decodeSrcCreated )

            self.callback_ = callback

            self.messageThread_ = Thread( target = self.messageLoop )
            self.messageThread_.daemon = True
            self.messageThread_.start()
            self.pipeline_.set_state( Gst.State.PLAYING )

    def _decodeSrcCreated( self, element, pad ):
        pad.link( self.level_.get_static_pad( 'sink' ) )

    def messageLoop( self, **kwargs ):
        while self.run_:
            bus = self.pipeline_.get_bus()
            message = bus.pop()
            if message is not None:
                if message.type == Gst.MessageType.EOS:
                    ret, dur = self.pipeline_.query_duration( Gst.Format.TIME )
                    self.duration_ = dur / Gst.SECOND
                    self.run_ = False
                elif message.type == Gst.MessageType.ERROR:
                    err, debug = Gst.Message.parse_error()
                    self.error_ = err
                    self.errorDebug_ = debug
                    self.run_ = False
                else:
                    structure = message.get_structure()

                    if structure:
                        if structure.get_name() == 'level':
                            pass

        self.pipeline_.set_state( Gst.State.NULL )
        Logger.debug( "Finished loading media information for %s", self.file_ )
        self.done_ = True
        self.callback_( self )
