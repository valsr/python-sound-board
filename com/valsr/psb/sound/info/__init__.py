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
    '''
    Manages all MediaInformation objects - including loading/creating and keeping in memory. Most of the methods are 
    static and no object creation is necessary. When working with the manager keep in mind that information is done
    in a background thread.
    '''

    mediaInfo_ = {} # Information objects
    loading_ = [] # Objects currently being loaded (by key)
    def __init__( self, *args, **kwargs ):
        '''
        Constructor

        Parameters:
            args -- Positional arguments
            kwargs -- Named parameters
        '''
        super().__init__()

    @staticmethod
    def getInfoForMedia( file, reloadOnError = False ):
        '''
        Obtain info for given media. If information is not found, this will create a thread to load it 
        (MediaInfoLoader) and will return None. Note that returning None does not mean that no media info is found,
        it could mean that the MediaInfoLoader is currently loading information.

        Parameters:
            file -- File path (key)
            reloadOnError -- Reload if the loader had an error

        Returns:
            MediaInfo (loaded media info, even on error) or None
        '''
        if file not in MediaInfoManager.loading_:
            if file in MediaInfoManager.mediaInfo_:
                info = MediaInfoManager.mediaInfo_[file]
                if not ( info.error_ and reloadOnError ):
                    return MediaInfoManager.mediaInfo_[file]

            Logger.debug( 'No media information found for %s', file )

            # Queue loading
            MediaInfoManager.loading_.append( file )
            loader = MediaInfoLoader( file, MediaInfoManager._loadedInfo )
            loader.analyze()

        return None

    @staticmethod
    def _loadedInfo( info ):
        '''
        Private callback called when the MediaLoader has finished loading. It finalizes the loading

        Parameters:
            info -- Loaded info
        '''
        infoStruc = MediaInfo()
        infoStruc.duration_ = info.duration_
        infoStruc.file_ = info.file_
        infoStruc.error_ = info.error_
        infoStruc.errorDebug_ = info.errorDebug_
        MediaInfoManager.mediaInfo_[info.file_] = infoStruc
        MediaInfoManager.loading_.remove( infoStruc.file_ )

class MediaInfo( object ):
    '''
    Media information structure. All parameters are accessed directly.
    '''
    def __init__( self, *args, **kwargs ):
        '''
        Constructor

        Parameters:
            args -- Positional arguments
            kwargs -- Named parameters
        '''
        super().__init__( *args, **kwargs )
        self.duration_ = 0
        self.file_ = None
        self.error_ = None
        self.errorDebug_ = None

class MediaInfoLoader( object ):
    '''
    Media loader
    '''
    def __init__( self, file, callback, **kwargs ):
        '''
        Constructor

        Parameters:
            file -- File (path) to analyze
            callback -- Function to call once analysis completed
            kwargs -- Named parameters
        '''
        self.file_ = os.path.abspath( file )
        self.lChannel_ = []
        self.rChannel_ = []
        self.readyToDraw_ = False
        self.error_ = None
        self.errorDebug_ = None
        self.run_ = True
        self._loaded_ = False
        self.duration_ = 0

        # player needed items
        self.pipeline_ = None
        self.source_ = None
        self.level_ = None
        self.sink_ = None
        self.messageThread_ = None
        self.callback_ = callback

    @property
    def loaded_( self ):
        return self._loaded_

    @loaded_.setter
    def loaded( self, loaded ):
        self._loaded_ = loaded
        if loaded and self.callback_:
            self.callback_( self )

    def analyze( self ):
        '''
        Analyze the media stream
        '''
        if not self.loaded_:
            # pipeline
            self.pipeline_ = Gst.Pipeline.new()

            # source
            self.source_ = Gst.ElementFactory.make( 'filesrc' )
            self.source_.set_property( 'location', self.file_ )
            self.pipeline_.add( self.source_ )

            # decoder
            self.decode_ = Gst.ElementFactory.make( 'decodebin' )
            self.pipeline_.add( self.decode_ )

            # level
            self.level_ = Gst.ElementFactory.make( 'level' )
            self.level_.set_property( 'post-messages', True )
            self.level_.set_property( 'interval', 100 * Gst.MSECOND )
            self.pipeline_.add( self.level_ )

            # sink
            self.sink_ = Gst.ElementFactory.make( 'fakesink' )
            self.pipeline_.add( self.sink_ )

            # link pad-always elements
            self.source_.link( self.decode_ )
            self.level_.link( self.sink_ )

            # decoder is dynamic so link at runtime
            self.decode_.connect( 'pad-added', self._decodeSrcCreated )

            self.messageThread_ = Thread( target = self.messageLoop )
            self.messageThread_.daemon = True
            self.messageThread_.start()
            self.pipeline_.set_state( Gst.State.PLAYING )

    def _decodeSrcCreated( self, element, pad ):
        '''
        Link decode pad to sink
        '''
        pad.link( self.level_.get_static_pad( 'sink' ) )

    def messageLoop( self, **kwargs ):
        '''
        Message loop
        '''
        while self.run_:
            bus = self.pipeline_.get_bus()
            message = bus.pop()
            if message is not None:
                if message.type == Gst.MessageType.EOS:
                    _, dur = self.pipeline_.query_duration( Gst.Format.TIME )
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
        Logger.debug( 'Finished loading media information for %s', self.file_ )
        self.loaded_ = True
