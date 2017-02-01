'''
Created on Jan 14, 2017

@author: radoslav
'''
from kivy.lang import Builder
import os

from com.valsr.psb.sound.player.manager import PlayerManager
from com.valsr.psb.ui.dialogue import popup
from com.valsr.psb.ui.window.base import WindowBase, WindowCloseState


class SaveDialogue( WindowBase ):
    '''
    classdocs
    '''

    def __init__( self, **kwargs ):
        WindowBase.__init__( self, **kwargs )
        self.title = "Save Project"
        self.cwd_ = os.getcwd()
        self.file_ = None
        self.playerId_ = None

    def on_open( self, **kwargs ):
        self.getUI( 'Files' ).path = self.cwd_
        self.getUI( 'PathInput' ).text = self.cwd_
        self.getUI( 'Files' ).filters.append( self.uiFilterFiles )

    def createRootUI( self ):
        return Builder.load_file( "ui/kv/save.kv" )

    def uiCancel( self, *args ):
        if self.playerId_ is not None:
            PlayerManager.destroyPlayer( self.playerId_ )

        self.closeState_ = WindowCloseState.CANCEL
        self.dismiss()

    def uiSave( self, *args ):
        if self.playerId_ is not None:
            PlayerManager.destroyPlayer( self.playerId_ )

        # compute the file selected
        fileName = self.getUI( 'FileName' ).text

        if not fileName:
            popup.showOkPopup( title = 'Enter name', message = 'Enter a valid project name', button = 'Ok' )
            return

        if fileName and not fileName.lower().endswith( '.psb' ):
            fileName += '.psb'

        self.file_ = os.path.join( self.getUI( 'Files' ).path, fileName )

        if os.path.exists( self.file_ ):
            popup.showYesNoPopup( title = 'File Exists', message = 'Fire %s exists. Overwrite file? ' % fileName,
                                       yesButton = 'Overwrite', noButton = 'Cancel',
                                       callback = self._saveOverwriteCallback )
            return

        self.closeState_ = WindowCloseState.OK
        self.dismiss()

    def _saveOverwriteCallback( self, popup ):
        if popup.selection_ == WindowCloseState.YES:
            self.closeState_ = WindowCloseState.OK
            self.dismiss()

    def uiFilterFiles( self, folder, file ):
        if os.path.isdir( file ):
            return True

        if self.getUI( 'PathInput' ).text is not folder:
            self.getUI( 'PathInput' ).text = folder
        ext = os.path.splitext( file )[1]
        return ext.lower() == '.psb'

    def fileSelection( self, *args ):
        files = self.getUI( 'Files' )

        if files.selection:
            file = files.selection[0]

            # get the base name
            self.getUI( 'FileName' ).text = os.path.basename( file )

        return True
