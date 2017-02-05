'''
Created on Jan 14, 2017

@author: radoslav
'''
import json
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.logger import Logger
import os

from com.valsr.psb import utility
from com.valsr.psb.sound.info import MediaInfoManager
from com.valsr.psb.tree import TreeNode
from com.valsr.psb.ui.dialogue import popup, addsound
from com.valsr.psb.ui.dialogue.addsound import AddSoundDialogue
from com.valsr.psb.ui.dialogue.open import OpenDialogue
from com.valsr.psb.ui.dialogue.save import SaveDialogue
from com.valsr.psb.ui.menu import SimpleMenuItem, Menu
from com.valsr.psb.ui.widget.draggabletreeview import DraggableTreeView, DraggableTreeViewNode
from com.valsr.psb.ui.window.base import WindowBase, WindowCloseState


class MainWindow( WindowBase ):
    '''
    classdocs
    '''
    def __init__( self, **kwargs ):
        super().__init__( **kwargs )
        self.file_ = None
        self.audioFilesTree_ = None

    def createRootUI( self ):
        return Builder.load_file( "ui/kv/main.kv" )

    def onPostCreate( self ):
        self.audioFilesTree_ = self.getUI( 'uiAudioFiles' )

    def uiAddSound( self, *args ):
        self.addSoundWindow_ = AddSoundDialogue( controller = self.controller_ , size_hint = ( 0.75, 0.75 ) )
        self.addSoundWindow_.bind( on_dismiss = self.uiAddSoundDismiss )
        self.addSoundWindow_.open()

    def uiAddSoundDismiss( self, *args ):
        if self.addSoundWindow_.closeState_ == WindowCloseState.OK:
            if not self.audioFilesTree_.hasChild( 'uncategorized' ):
                self.audioFilesTree_.addChild( DraggableTreeViewNode( label = 'Uncategorized' ) )

            self._addFileImpl( self.addSoundWindow_.file_ )
        else:
            self.addSoundWindow_ = None

    def _addFileImpl( self, file ):
        # check the fingerprint and see if we already have it
        info = MediaInfoManager.getInfoForMedia( file, reloadOnError = True )
        if not info:
            Clock.schedule_once( lambda x: self._addFileImpl( file ) , 0.1 )
            return

        if self.audioFilesTree_.findNodeByFingerprint( info.fingerprint_ ):
            popup.showOkPopup( 'File Already Added', 'File by similar fingerprint has already been added', parent = self )
            return

        Logger.debug( "Adding to %s to collection", file )
        node = DraggableTreeViewNode( label = os.path.basename( file ) )

    def uiSave( self, *args ):
        if self.file_ is None:
            # open file to save assert
            self.saveWindow_ = self.controller_.openWindow( SaveDialogue, windowed = True, size_hint = ( 0.75, 0.75 ) )
            self.saveWindow_.bind( on_dismiss = lambda x: self._saveImpl( fromDialogue = True ) )
        else:
            self._saveImpl()

    def _saveImpl( self, fromDialogue = False ):
        if fromDialogue:
            if self.saveWindow_.closeState_ != WindowCloseState.OK:
                return
            self.file_ = self.saveWindow_.file_
        utility.saveProject( self.file_, self.audioFilesTree_, None )
        self.title = "PSB: " + self.file_

    def uiOpen( self, *args ):
        self.openWindow_ = self.controller_.openWindow( OpenDialogue, windowed = True, size_hint = ( 0.75, 0.75 ) )
        self.openWindow_.bind( on_dismiss = self._openImpl )

    def _openImpl( self , *args ):
        self.file_ = self.openWindow_.file_
        if self.openWindow_.closeState_ == WindowCloseState.OK:
            utility.loadProject( self.file_, self.audioFilesTree_ )

    def uiAddTreeCategory( self, *args ):
        selectedNode = self.audioFilesTree_.selected_node

        if selectedNode == None:
            selectedNode = self.audioFilesTree_.root

        # now open the dialogue
        popup.showTextInputPopup( title = 'New Category', message = 'Enter Category Name', inputMessage = 'Category',
                                  yesButton = 'Create', noButton = 'Cancel', parent = self,
                                  callback = lambda x: self._completeNewCategory( x.selection_, selectedNode, x.text_ ) )
        return

    def _completeNewCategory( self, button, parentNode, text ):
        if button == WindowCloseState.YES:
            Logger.trace( 'Adding %s node to %s', text, parentNode.id )
            # find if we have the node by text
            if parentNode.find_node( lambda x: x.ui.text == text, False ):
                Logger.trace( 'Node by %s already exists', text )
                popup.showOkPopup( 'New Category', message = 'Category \'%s\' already exists within \'%s\'' % ( text, parentNode.id ) )
                return

            node = DraggableTreeViewNode( label = text )
            parentNode.add_node( node ).open( True )

    def uiFileTreeTouchUp( self, fileNode, touch ):
        if touch.button == 'left':
            # create menu
            Logger.debug( 'Touch up from %s', fileNode.text )
            m = Menu( controller = self.controller_ )
            m.addMenuItem( SimpleMenuItem( text = 'test' ) )
            m.addMenuItem( SimpleMenuItem( text = 'test2' ) )
            m.open()
            pass
