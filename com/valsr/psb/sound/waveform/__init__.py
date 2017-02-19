"""
Created on Jan 17, 2017

@author: valsr <valsr@valsr.com>
"""
import math
import os
from threading import Thread
from time import sleep
from gi.repository import Gst, GObject

from com.valsr.psb.sound.info import MediaInfoManager
from com.valsr.psb.sound.player import PlayerBase
from kivy.clock import Clock
from kivy.logger import Logger


class Waveform(PlayerBase):
    """Waveform generating player"""

    def __init__(self, file):
        """Constructor"""
        self.file = os.path.abspath(file)
        self.left_channel = []
        self.rigth_channel = []
        self.ready_to_draw = False
        self.level = None
        self.info = None
        self._loaded = False
        super().__init__("waveform://" + file)

    def _set_up_pipeline(self):
        # source
        self.source = Gst.ElementFactory.make("filesrc")
        self.source.set_property("location", self.file)
        self.pipeline.add(self.source)

        # decoder
        self.decode = Gst.ElementFactory.make("decodebin")
        self.pipeline.add(self.decode)

        # level
        self.level = Gst.ElementFactory.make("level")
        self.level.set_property('post-messages', True)

        self.pipeline.add(self.level)

        # sink
        self.sink = Gst.ElementFactory.make("fakesink")
        self.pipeline.add(self.sink)

        # link pad-always elements
        self.source.link(self.decode)
        self.level.link(self.sink)

        # decoder is dynamic so link at runtime
        self.decode.connect("pad-added", self._decode_src_created)

    def _decode_src_created(self, element, pad):
        pad.link(self.level.get_static_pad('sink'))

    @property
    def loaded(self):
        """Loaded property getter"""
        return self._loaded

    def analyze(self):
        """Analyze the stream (generate waveform information)"""
        if not self.loaded:
            if not self.info:
                self.info = MediaInfoManager.get_media_info(self.file, True)
                Clock.schedule_once(self.analyze, 0.2)
                return

            if self.info.error:
                raise RuntimeError("Issues during loading media %s: %s %s" %
                                   (self.info.file, self.info.error.src, self.info.error.message))

            self.level.set_property('interval', math.ceil(self.info.duration / self.num_points() * Gst.SECOND))
            self.pipeline.set_state(Gst.State.PLAYING)

    def _message_loop(self, **kwargs):
        bus = self.pipeline.get_bus()
        message = bus.pop()
        if message is not None:
            structure = message.get_structure()
            if structure:
                if structure.get_name() == 'level':
                    rms_array = structure.get_value('rms')
                    start_time = structure.get_value('stream-time')
                    if len(rms_array) > 1:
                        self.left_channel.append((start_time / Gst.SECOND, pow(10, rms_array[0] / 20)))
                        self.rigth_channel.append((start_time / Gst.SECOND, pow(10, rms_array[1] / 20)))
                    else:
                        self.left_channel.append((start_time / Gst.SECOND, pow(10, rms_array[0] / 20)))
                        self.rigth_channel.append((start_time / Gst.SECOND, pow(10, rms_array[0] / 20)))
            if message.type == Gst.MessageType.EOS:
                if len(self.left_channel) < self.num_points():
                    self.left_channel += [[self.info.duration + x / Gst.SECOND, 0]
                                          for x in range(0, self.num_points() - len(self.left_channel))]
                if len(self.rigth_channel) < self.num_points():
                    self.rigth_channel += [[self.info.duration + x / Gst.SECOND, 0]
                                           for x in range(0, self.num_points() - len(self.rigth_channel))]

    def finish(self):
        self.pipeline.set_state(Gst.State.NULL)
        Logger.debug("Finished loading waveform for %s", self.file)
        self._loaded = True

    def num_points(self):
        """Get the number of points used for each channel"""
        return 2000

    def point_interval(self):
        """Get the interval between each interval (in seconds)"""
        if self.loaded:
            return self.info.duration / self.num_points()

        return None

    def point(self, num):
        """Get waveform point

        Args:
            num: Point number

        Returns:
            (time, left channel value, right channel value) or None
        """
        if num < self.num_points() and self.loaded:
            return (self.left_channel[num][0], self.left_channel[num][1], self.rigth_channel[num][1])

        return None
