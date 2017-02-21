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

from com.valsr.psb.sound.waveform.manager import WaveformManager


class WaveformWidget(Widget):
    """Widget to display a waveform for audio file"""
    file = StringProperty("")
    """Audio file"""

    position = NumericProperty(0.0)
    """Current position for the play indicator"""

    autoscale = BooleanProperty(True)
    """Whether to autoscale the peaks"""

    def __init__(self, **kwargs):
        """Constructor"""
        Widget.__init__(self, **kwargs)

        self._waveform = None
        self.max_amp = None
        self.ready_to_draw = False
        self.left_points = []
        self.right_points = []
        self.player = None

        self._init()
        self.bind(pos=self._prep_draw)
        self.bind(size=self._prep_draw)
        self.update_canvas()

    def _init(self):
        """Initialize variables"""
        self._waveform = None
        self.max_amp = None
        self.ready_to_draw = False
        self.left_points = []
        self.right_points = []
        self.player = None

    def _prep_draw(self, *args):
        """Prepare the drawing data - re-scale the waveform"""
        self.ready_to_draw = False
        offset = self.pos
        if self._waveform is not None and self._waveform.loaded:
            left_channel_points = []
            right_channel_points = []
            amplitude_multiplier = 1

            # figure out max amplitude
            if not self.max_amp:
                points_list = []
                for i in range(0, self._waveform.num_points()):
                    raw_point = self._waveform.point(i)
                    points_list.append(raw_point[1])
                    points_list.append(raw_point[2])
                    self.max_amp = max(points_list)

            if self.autoscale and self.max_amp:
                amplitude_multiplier = 1 / self.max_amp

            mid_height_offset = offset[1] + self.height / 2
            for i in range(0, self._waveform.num_points()):
                raw_point = self._waveform.point(i)
                point = self._convert_to_point(raw_point[0], raw_point[1])
                left_channel_points.append(point[0] + offset[0])
                left_channel_points.append(mid_height_offset)
                left_channel_points.append(point[0] + offset[0])
                left_channel_points.append(point[1] * amplitude_multiplier + mid_height_offset)

                point = self._convert_to_point(raw_point[0], raw_point[2])
                right_channel_points.append(point[0] + offset[0])
                right_channel_points.append(mid_height_offset)
                right_channel_points.append(point[0] + offset[0])
                right_channel_points.append(-point[1] * amplitude_multiplier + mid_height_offset)

            self.left_points = left_channel_points
            self.right_points = right_channel_points

            Logger.debug("Canvas ready for drawing")
            self.ready_to_draw = True
        self.update_canvas()

    def update_canvas(self, *args):
        """Redraw the canvas"""

        # draw element that don't require to have any data
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
                pos = self.position if self.position != -1 else 0
                Color(1, 1, 1, 0.75)
                Line(
                    points=[pos * pps + offset[0], offset[1], pos * pps + offset[0], offset[1] + self.height], width=1)

    def _convert_to_point(self, time, amp):
        x = time * self.width / self._waveform.info.duration
        y = amp * floor((self.height - 1) / 2)

        return (x, y)

    def on_file(self, *args):
        """Change the file (waveform)"""
        self._init()

        # load the wave form.. and get it displayed (maybe wait for it to build)
        waveform = WaveformManager.waveform(args[1])
        if not waveform:
            _, waveform = WaveformManager.create_waveform(args[1])

        self.file = args[1]
        self._waveform = waveform
        waveform.analyze()
        self._wait_for_waveform_analyze()
        self.update_canvas()

    def _wait_for_waveform_analyze(self, *args):
        if self._waveform.loaded:
            self._prep_draw()
        else:
            Clock.schedule_once(self._wait_for_waveform_analyze, 1)

    def on_position(self, *args):
        """Handle position changes"""
        self.update_canvas()

    def on_autoscale(self, *args):
        """Handle autoscale changes"""
        self.update_canvas()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.player and self._waveform.info:
                x = touch.pos[0] - self.pos[0]

                # convert x to position and seek to that position
                pps = self.width / self._waveform.info.duration
                position = x / pps

                self.player.position = position
            return True

    def associate_player(self, player):
        """Associate player with widget

        Args:
            player: PlayerBase to associate
        """
        if player and player is not self.player:
            self.player = player

    def associated_player(self):
        """Obtain the associated player with widget

        Returns:
            PlayerBase or None
        """
        return self.player
