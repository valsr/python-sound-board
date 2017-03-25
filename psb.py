"""
Created on Jan 13, 2017

@author: valsr <valsr@valsr.com>
"""
from gi.repository import Gst
import gi
from kivy.app import App
from kivy.config import Config
from kivy.logger import Logger

from com.valsr.psb import sound
from com.valsr.psb.ui.window import MainWindow
from com.valsr.psb.ui.window.manager import WindowManager
from kivy.lang import Builder

gi.require_version('Gst', '1.0')

# TODO: Separate kivy UI definitions in separate file and load it first


class PSB(App):
    """Main application"""

    MAIN_WINDOW_ID = "_PSB_MAIN_"

    def __init__(self, **kwargs):
        """Constructor"""
        App.__init__(self, **kwargs)

    def build(self):
        """Create the main window and open it"""
        window = WindowManager.create_window(
            MainWindow, parent=None, window_id=PSB.MAIN_WINDOW_ID, create_opts={'draggable': 'None', 'title': 'PSB'})
        window.open()
        return None  # don't actually return a widget as WindowManager will take care of creating the root widget

    def theme_image_file(self, name, size=24, theme='white'):
        """Obtain (most appropriate) theme image file. See WindowManager.theme_image_file"""
        return WindowManager.theme_image_file(name=name, size=size, theme=theme)

    def init_utility_ui(self):
        Builder.load_file("ui/kv/utility.kv")

if __name__ == '__main__':
    sound.init_audio()
    Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
    Logger.info("GStreamer version %d.%d.%d.%d" % Gst.version())

    app = PSB()
    app.init_utility_ui()
    app.run()
