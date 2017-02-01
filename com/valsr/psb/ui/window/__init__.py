'''
Created on Jan 14, 2017

@author: radoslav
'''
import json
from kivy.lang import Builder
from kivy.logger import Logger

from com.valsr.psb.ui.dialogue.addsound import AddSoundDialogue
from com.valsr.psb.ui.dialogue.save import SaveDialogue
from com.valsr.psb.ui.window.base import WindowBase, WindowCloseState


class MainWindow( WindowBase ):
    '''
    classdocs
    '''
    def __init__( self, **kwargs ):
        super().__init__( **kwargs )
        self.file_ = None

    def createRootUI( self ):
        return Builder.load_file( "ui/kv/main.kv" )

    def uiAddSound( self, *args ):
        self.addSoundWindow_ = self.controller_.openWindow( AddSoundDialogue, windowed = True, size_hint = ( 0.75, 0.75 ) )
        self.addSoundWindow_.bind( on_dismiss = self.uiAddSoundDismiss )

    def uiAddSoundDismiss( self, *args ):
        if self.addSoundWindow_.closeState_ == WindowCloseState.OK:
            Logger.debug( "Adding to sound stuff" )

    def uiSave( self, *args ):
        if self.file_ is None:
            # open file to save assert
            self.saveWindow_ = self.controller_.openWindow( SaveDialogue, windowed = True, size_hint = ( 0.75, 0.75 ) )
            self.saveWindow_.bind( on_dismiss = lambda x: self._saveImpl( fromDialogue = True ) )
        else:
            self._saveImpl()

    def _saveImpl( self, fromDialogue = False ):
        if fromDialogue:
            self.file_ = self.saveWindow_.file_

        # serialize
        Logger.info( 'Saving project to %s', self.file_ )
        dict = self.controller_.audioFiles_.serialize()
        with open( self.file_, 'w' ) as f:
            json.dump( dict, f )
