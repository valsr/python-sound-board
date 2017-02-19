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
        self.file = None

    def on_open( self, **kwargs ):
        self.get_ui( 'Files' ).path = self.cwd_
        self.get_ui( 'PathInput' ).text = self.cwd_
        self.get_ui( 'Files' ).filters.append( self.uiFilterFiles )

    def create_root_ui( self ):
        return Builder.load_file( "ui/kv/save.kv" )

    def uiCancel( self, *args ):
        self.close_state = WindowCloseState.CANCEL
        self.dismiss()

    def uiSave( self, *args ):
        fileName = self.get_ui( 'FileName' ).text

        if not fileName:
            popup.showOkPopup( title = 'Enter name', message = 'Enter a valid project name', button = 'Ok' )
            return

        if fileName and not fileName.lower().endswith( '.psb' ):
            fileName += '.psb'

        self.file = os.path.join( self.get_ui( 'Files' ).path, fileName )

        if os.path.exists( self.file ):
            popup.showYesNoPopup( title = 'File Exists', message = 'Fire %s exists. Overwrite file? ' % fileName,
                                       yesButton = 'Overwrite', noButton = 'Cancel',
                                       callback = self._saveOverwriteCallback )
            return

        self.close_state = WindowCloseState.OK
        self.dismiss()

    def _saveOverwriteCallback( self, popup ):
        if popup.selection_ == WindowCloseState.YES:
            self.close_state = WindowCloseState.OK
            self.dismiss()

    def uiFilterFiles( self, folder, file ):
        if os.path.isdir( file ):
            return True

        if self.get_ui( 'PathInput' ).text is not folder:
            self.get_ui( 'PathInput' ).text = folder
        ext = os.path.splitext( file )[1]
        return ext.lower() == '.psb'

    def fileSelection( self, *args ):
        files = self.get_ui( 'Files' )

        if files.selection:
            file = files.selection[0]

            # get the base name
            self.get_ui( 'FileName' ).text = os.path.basename( file )

        return True
