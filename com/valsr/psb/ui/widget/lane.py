"""
Created on Jan 22, 2017

@author: valsr <valsr@valsr.com>
"""
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, BoundedNumericProperty
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from com.valsr.psb.ui.widget.droppable import Droppable

Builder.load_file('ui/kv/lane.kv')


class LaneWidget(BoxLayout, Droppable):

    autoscale = BooleanProperty(True)
    """Whether to autoscale the peaks"""

    max_zoom = BoundedNumericProperty(1, min=1)
    """Maximum zoom in seconds between min time and max time"""

    zoom_manual = BooleanProperty(False)
    """Current zoom method"""

    _view_time_start = NumericProperty(0)
    view_time_end = NumericProperty(1)
    #_view_time =

    def __init__(self, **kwargs):
        """Constructor"""
        super().__init__(**kwargs)
        self._trigger_layout = Clock.create_trigger(self._do_layout, -1)
        self._init()
        self.bind(pos=self._prep_draw)
        self.bind(size=self._prep_draw)
        # self._prep_draw()

    def _init(self):
        """Initialize variables"""
        self._view_time_start = 0
        self.view_time_end = 1
        pass

    def do_layout(self, *largs):
        self._prep_draw()
        return BoxLayout.do_layout(self, *largs)

    def _prep_draw(self, *args):
        """Prepare the drawing data - re-scale the waveform"""
        # TODO: Update lane_view nav bar
        self.update_lane_view_canvas()

    def update_lane_view_canvas(self, *args):
        """Redraw the canvas"""
        lane_view = self.ids['lane_view']
        lane_view.canvas.clear()

    def _do_layout(self, *largs):
        return self.do_layout(self)

    def on__view_time_start(self, instance, value):
        print(value)
