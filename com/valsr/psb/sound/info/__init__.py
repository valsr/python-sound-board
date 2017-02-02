'''
Created on Jan 28, 2017

@author: radoslav
'''
from gi.repository import Gst
import hashlib
from kivy.logger import Logger
import math
import os
from threading import Thread
from time import sleep

from com.valsr.psb.sound.player import PlayerBase


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
            loader.analyse()

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
        infoStruc.fingerprint_ = info.fingerprint_
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
        self.fingerprint_ = 0

    def serialize( self ):
        return self.__dict__

    def update( self, **entries ):
        self.__dict__.update( entries )

    @staticmethod
    def deserialize( entries ):
        info = MediaInfo()
        if entries:
            info.update( **entries )
        return info

class MediaInfoLoader( PlayerBase ):
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
        self._loaded_ = False
        self.duration_ = 0
        self.fingerprint_ = 0
        self.md5_ = hashlib.md5()

        # player needed items
        self.level_ = None
        self.callback_ = callback
        super().__init__( "info://" + file )

    @property
    def loaded_( self ):
        return self._loaded_

    @loaded_.setter
    def loaded_( self, loaded ):
        self._loaded_ = loaded
        if loaded and self.callback_:
            self.callback_( self )

    def _setUpPipeline( self ):
        '''
        Analyze the media stream
        '''
        if not self.loaded_:
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

    def _decodeSrcCreated( self, element, pad ):
        '''
        Link decode pad to sink
        '''
        pad.link( self.level_.get_static_pad( 'sink' ) )

    def _messageLoop( self, **kwargs ):
        bus = self.pipeline_.get_bus()
        message = bus.pop()
        if message is not None:
            structure = message.get_structure()
            if structure:
                if structure.get_name() == 'level':
                    peak = structure.get_value( 'peak' )
                    # it seems that the left channel always provide a stable value for audio file (right channel differs each run)
                    self.md5_.update( str( round( peak[0], 0 ) ).encode( 'utf-8' ) )

            if message.type == Gst.MessageType.EOS:
                _, dur = self.pipeline_.query_duration( Gst.Format.TIME )
                self.duration_ = dur / Gst.SECOND
                self.fingerprint_ = self.md5_.hexdigest()

    def finish( self ):
        self.pipeline_.set_state( Gst.State.NULL )
        Logger.debug( 'Finished loading media information for %s, fingerprint %s', self.file_, self.fingerprint_ )
        self.loaded_ = True

    def analyse( self ):
        if not self.loaded_:
            self.pipeline_.set_state( Gst.State.PLAYING )
