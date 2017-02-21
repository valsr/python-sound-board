"""
Created on Jan 28, 2017

@author: valsr <valsr@valsr.com>
"""
import hashlib
import math
import os
from threading import Thread
from time import sleep
from gi.repository import Gst
from kivy.logger import Logger

from com.valsr.psb.sound.player import PlayerBase


class MediaInfoManager(object):
    """Manages all MediaInformation objects - including loading/creating and keeping in memory. Most of the methods are
    static and no object creation is necessary. When working with the manager keep in mind that information is done
    in a background thread."""

    media_info = {}  # Information objects
    loading = []  # Objects currently being loaded (by key)

    def __init__(self, *args, **kwargs):
        """Constructor

        Args:
            args: Positional arguments
            kwargs: Named parameters
        """
        super().__init__()

    @staticmethod
    def get_media_info(file, reload_on_error=False):
        """Obtain info for given media. If information is not found, this will create a thread to load it
        (MediaInfoLoader) and will return None. Note that returning None does not mean that no media info is found,
        it could mean that the MediaInfoLoader is currently loading information.

        Args:
            file: File path (key)
            reload_on_error: Reload if the loader had an _error

        Returns:
            MediaInfo (loaded media info, even on _error) or None
        """
        if file not in MediaInfoManager.loading:
            if file in MediaInfoManager.media_info:
                info = MediaInfoManager.media_info[file]
                if not (info._error and reload_on_error):
                    return MediaInfoManager.media_info[file]

            Logger.debug('No media information found for %s', file)

            # Queue loading
            MediaInfoManager.loading.append(file)
            loader = MediaInfoLoader(file, MediaInfoManager._loaded_info)
            loader.analyze()

        return None

    @staticmethod
    def _loaded_info(info):
        """Private callback called when the MediaLoader has finished loading. It finalizes the loading

        Args:
            info: Loaded info
        """
        info_struc = MediaInfo()
        info_struc.duration = info.duration
        info_struc.file = info.file
        info_struc._error = info._error
        info_struc.fingerprint = info.fingerprint
        info_struc.error_debug = info.error_debug
        MediaInfoManager.media_info[info.file] = info_struc
        MediaInfoManager.loading.remove(info_struc.file)


class MediaInfo(object):
    """Media information structure. All parameters are accessed directly."""

    def __init__(self, *args, **kwargs):
        """Constructor

        Args:
            args: Positional arguments
            kwargs: Named parameters
        """
        super().__init__(*args, **kwargs)
        self.duration = 0
        self.file = None
        self._error = None
        self.error_debug = None
        self.fingerprint = 0

    def serialize(self):
        """Serialize it self

        Returns:
            Object dictionary
        """
        return self.__dict__

    def update(self, **entries):
        """Update object dictionary

        Args:
            entries: Dictionary entries to update
        """
        self.__dict__.update(entries)

    @staticmethod
    def deserialize(entries):
        """Deserialize a dictionary into a MediaInfo object

        Args:
            entries: Dictionary to deserialize

        Returns:
            MedioInfo
        """
        info = MediaInfo()
        if entries:
            info.update(**entries)
        return info


class MediaInfoLoader(PlayerBase):
    """Media loader"""

    def __init__(self, file, callback, **kwargs):
        """Constructor

        Args:
            file: File (path) to analyze
            callback: Function to call once analysis completed
            kwargs: Named parameters
        """
        self.file = os.path.abspath(file)
        self._loaded = False
        self._duration = 0
        self.fingerprint = 0
        self.md5 = hashlib.md5()

        # player needed items
        self.level = None
        self.callback = callback
        super().__init__("info://" + file)

    @property
    def loaded(self):
        """Getter for loaded property"""
        return self._loaded

    @loaded.setter
    def loaded(self, loaded):
        """Setter for loaded property"""
        self._loaded = loaded
        if loaded and self.callback:
            self.callback(self)

    def _set_up_pipeline(self):
        """Analyze the media stream"""
        if not self.loaded:
            # source
            self.source = Gst.ElementFactory.make('filesrc')
            self.source.set_property('location', self.file)
            self.pipeline.add(self.source)

            # decoder
            self.decode = Gst.ElementFactory.make('decodebin')
            self.pipeline.add(self.decode)

            # level
            self.level = Gst.ElementFactory.make('level')
            self.level.set_property('post-messages', True)
            self.level.set_property('interval', 100 * Gst.MSECOND)
            self.pipeline.add(self.level)

            # sink
            self.sink = Gst.ElementFactory.make('fakesink')
            self.pipeline.add(self.sink)

            # link pad-always elements
            self.source.link(self.decode)
            self.level.link(self.sink)

            # decoder is dynamic so link at runtime
            self.decode.connect('pad-added', self._decode_src_created)

    def _decode_src_created(self, element, pad):
        """Link decode pad to sink"""
        pad.link(self.level.get_static_pad('sink'))

    def _message_loop(self, **kwargs):
        bus = self.pipeline.get_bus()
        message = bus.pop()
        if message is not None:
            structure = message.get_structure()
            if structure:
                if structure.get_name() == 'level':
                    peak = structure.get_value('peak')
                    # it seems that the left channel always provide a stable value for audio
                    # file (right channel differs each run)
                    self.md5.update(str(round(peak[0], 0)).encode('utf-8'))

            if message.type == Gst.MessageType.EOS:
                _, dur = self.pipeline.query_duration(Gst.Format.TIME)
                self._duration = dur / Gst.SECOND
                self.fingerprint = self.md5.hexdigest()

    def finish(self):
        self.pipeline.set_state(Gst.State.NULL)
        Logger.debug('Finished loading media information for %s, fingerprint %s', self.file, self.fingerprint)
        self.loaded = True

    def analyze(self):
        """Analyze the media stream"""
        if not self.loaded:
            self.pipeline.set_state(Gst.State.PLAYING)

    @property
    def duration(self):
        return self._duration