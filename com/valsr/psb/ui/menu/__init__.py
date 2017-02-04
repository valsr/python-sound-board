from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from com.valsr.psb.ui.window.base import WindowBase


class MenuItem():
    def __init__( self, **kwargs ):
        self.menu_ = None
        super().__init__( **kwargs )

class SimpleMenuItem( Button, MenuItem ):
    pass

class Menu( WindowBase ):
    def __init__( self, **kwargs ):
        super().__init__( **kwargs )
        self.ui_ = BoxLayout()

    def addMenuItem( self, child ):
        self.ui_.add_widget( child )
        child.menu_ = self
