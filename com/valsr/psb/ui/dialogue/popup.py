'''
Created on Feb 1, 2017

@author: radoslav
'''
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup

from com.valsr.psb.ui.window.base import WindowCloseState


class PopupDialogue( Popup ):
    '''
    classdocs
    '''
    def __init__( self, callback = None, size_hint = ( 0.5, 0.5 ), **kwargs ):
        '''
        Constructor
        '''
        super().__init__( size_hint = size_hint , **kwargs )
        self.selection_ = None
        self.dismissed_ = False
        self.bind( on_dismiss = self.dismissed )
        self.cb_ = callback

    def onButton( self, button ):
        self.selection_ = button
        self.dismiss()

    def dismissed( self, *args ):
        self.dismissed_ = True
        if self.cb_:
            self.cb_( self )

def showOkPopup( title = 'Title Message', message = 'Message', button = 'Ok', parent = None , **kwargs ):
    p = PopupDialogue( title = title, attach_to = parent )
    topBox = BoxLayout( orientation = 'vertical' )
    topBox.add_widget( Label( text = message ) )
    topBox.add_widget( Button( text = button , on_press = lambda x: p.onButton( WindowCloseState.OK ), size_hint = ( 1, None ), height = 35 ) )
    p.content = topBox
    p.open()

def showYesNoPopup( title = 'Title Message', message = 'Message', yesButton = 'Ok', noButton = 'No', parent = None , **kwargs ):
    p = PopupDialogue( title = title, attach_to = parent , **kwargs )
    topBox = BoxLayout( orientation = 'vertical' )
    topBox.add_widget( Label( text = message ) )
    hbox = BoxLayout( orientation = 'horizontal' )
    hbox.add_widget( Button( text = yesButton , on_press = lambda x: p.onButton( WindowCloseState.YES ), size_hint = ( 1, None ), height = 35 ) )
    hbox.add_widget( Button( text = noButton , on_press = lambda x: p.onButton( WindowCloseState.NO ), size_hint = ( 1, None ), height = 35 ) )
    topBox.add_widget( hbox )
    p.content = topBox
    p.open()

