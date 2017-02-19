"""
Created on Jan 22, 2017

@author: valsr <valsr@valsr.com>
"""
from math import floor
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Line
from kivy.logger import Logger
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.widget import Widget

from com.valsr.psb.sound.waveform import Waveform


class WaveformWidget(Widget):
    """Widget to display a waveform for audio file"""
    file = StringProperty("")
    """Audio file"""

    position_ = NumericProperty(0.0)
    """Current position for the play indicator"""

    autoscale_ = BooleanProperty(True)
    """Whether to autoscale the peaks"""

    def __init__(self, **kwargs):
        """Constructor"""
        Widget.__init__(self, **kwargs)
        self._init()
        self.bind(pos=self._prepDraw)
        self.bind(size=self._prepDraw)
        self.updateCanvas()

    def _init(self):
        """Initialize variables"""
        self._waveform = None
        self.max_amp = None
        self.ready_to_draw = False
        self.left_points = []
        self.right_points = []
        self.player = None

    def updateCanvas(self, *args):
        self.canvas.clear()

        offset = self.pos
        top = [offset[0] + self.width, offset[1] + self.height]
        with self.canvas:
            # background
            Color(0, 0, 0, 0.0)
            Rectangle(pos=offset, size=(self.width, self.height))

            # borders and stuff
            Color(0.443, 0.474, 0.509, 0.75)
            Line(points=[offset[0], offset[1], top[0], offset[1], top[0], top[1], offset[0], top[1]], width=1)
            Line(points=[offset[0], offset[1] + self.height / 2, top[0], offset[1] + self.height / 2])

            if self.ready_to_draw:
                Color(0.203, 0.396, 0.643, 1)
                Line(points=self.left_points)
                Line(points=self.right_points)

                # tracker
                pps = self.width / self._waveform.info.duration
                pos = self.position_ if self.position_ != -1 else 0
                Color(1, 1, 1, 0.75)
                Line(
                    points=[pos * pps + offset[0], offset[1], pos * pps + offset[0], offset[1] + self.height], width=1)

    def _convertToPoint(self, time, amp):
        x = time * self.width / self._waveform.info.duration
        y = amp * floor((self.height - 1) / 2)

        return (x, y)

    def on_file_(self, *args):
        self._init()

        # load the wave form.. and get it displayed (maybe wait for it to build)
        wv = Waveform(args[1])
        self._waveform = wv
        wv.analyze()
        self.loadWaveFormCallback()
        self.updateCanvas()

    def loadWaveFormCallback(self, *args):
        if self._waveform.loaded:
            self._prepDraw()
        else:
            Clock.schedule_once(self.loadWaveFormCallback, 1)

    def on_position_(self, *args):
        self.updateCanvas()

    def on_autoscale_(self, *args):
        self.updateCanvas()

    def _prepDraw(self, *args):
        self.ready_to_draw = False
        offset = self.pos
        if self._waveform is not None and self._waveform.loaded:
            lChannelPoints = []
            rChannelPoints = []
            ampMulti = 1

            # figure out max amplitude
            if self.max_amp == None:
                ampList = []
                for i in range(0, self._waveform.num_points()):
                    wavePoint = self._waveform.point(i)
                    ampList.append(wavePoint[1])
                    ampList.append(wavePoint[2])
                    self.max_amp = max(ampList)

            if self.autoscale_ and self.max_amp:
                ampMulti = 1 / self.max_amp

            midHeightOffset = offset[1] + self.height / 2
            for i in range(0, self._waveform.num_points()):
                wavePoint = self._waveform.point(i)
                pt = self._convertToPoint(wavePoint[0], wavePoint[1])
                lChannelPoints.append(pt[0] + offset[0])
                lChannelPoints.append(midHeightOffset)
                lChannelPoints.append(pt[0] + offset[0])
                lChannelPoints.append(pt[1] * ampMulti + midHeightOffset)

                pt = self._convertToPoint(wavePoint[0], wavePoint[2])
                rChannelPoints.append(pt[0] + offset[0])
                rChannelPoints.append(midHeightOffset)
                rChannelPoints.append(pt[0] + offset[0])
                rChannelPoints.append(-pt[1] * ampMulti + midHeightOffset)

            self.left_points = lChannelPoints
            self.right_points = rChannelPoints

            Logger.debug("Canvas ready for drawing")
            self.ready_to_draw = True
        self.updateCanvas()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.player and self._waveform.info:
                x = touch.pos[0] - self.pos[0]

                # convert x to position and seek to that position
                pps = self.width / self._waveform.info.duration
                toPosition = x / pps

                self.player.position = toPosition
            return True

    @property
    def waveform(self):
        return self.player

    @waveform.setter
    def waveform(self, waveform):
        self.player = waveform
        # reset all the shit...
