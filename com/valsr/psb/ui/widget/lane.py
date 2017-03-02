"""
Created on Jan 22, 2017

@author: valsr <valsr@valsr.com>
"""
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

Builder.load_file('ui/kv/lane.kv')


class LaneWidget(BoxLayout):

    autoscale = BooleanProperty(True)
    """Whether to autoscale the peaks"""

    def __init__(self, **kwargs):
        """Constructor"""
        super().__init__(**kwargs)
        self._trigger_layout = Clock.create_trigger(self._do_layout, -1)
        self._init()
        self.bind(pos=self._prep_draw)
        self.bind(size=self._prep_draw)
        self.update_canvas()

    def _init(self):
        """Initialize variables"""
        pass

    def _prep_draw(self, *args):
        """Prepare the drawing data - re-scale the waveform"""
        self.update_canvas()

    def update_canvas(self, *args):
        """Redraw the canvas"""
        pass

    def _do_layout(self, *largs):
        return BoxLayout.do_layout(self)
