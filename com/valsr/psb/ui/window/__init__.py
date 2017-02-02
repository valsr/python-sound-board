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
from com.valsr.psb.ui.dialogue import popup
from com.valsr.psb.ui.dialogue.addsound import AddSoundDialogue
from com.valsr.psb.ui.dialogue.open import OpenDialogue
from com.valsr.psb.ui.dialogue.save import SaveDialogue
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
        self.audioFilesTree_ = TreeNode( id = 'root', tree = self.getUI( 'uiAudioFiles' ) )
        self.getUI( 'uiAudioFiles' ).add_node( self.audioFilesTree_ )

    def uiAddSound( self, *args ):
        self.addSoundWindow_ = self.controller_.openWindow( AddSoundDialogue, windowed = True, size_hint = ( 0.75, 0.75 ) )
        self.addSoundWindow_.bind( on_dismiss = self.uiAddSoundDismiss )

    def uiAddSoundDismiss( self, *args ):
        if self.addSoundWindow_.closeState_ == WindowCloseState.OK:
            if not self.audioFilesTree_.hasChild( 'uncategorized' ):
                self.audioFilesTree_.addChild( TreeNode( id = 'uncategorized', tree = self.audioFilesTree_.tree_ ) )
                self.audioFilesTree_.getChild( 'uncategorized' ).openParents()

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
        node = TreeNode( id = info.fingerprint_, label = os.path.basename( file ) , data = info, tree = self.audioFilesTree_.tree_ )
        self.audioFilesTree_.getChild( 'uncategorized' ).addChild( node )
        node.openParents()

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
        utility.saveProject( self.file_, self.audioFilesTree_, None )

    def uiOpen( self, *args ):
        self.openWindow_ = self.controller_.openWindow( OpenDialogue, windowed = True, size_hint = ( 0.75, 0.75 ) )
        self.openWindow_.bind( on_dismiss = self._openImpl )

    def _openImpl( self , *args ):
        self.file_ = self.openWindow_.file_

        tree, _ = utility.loadProject( self.file_ )
        treeRoot = self.getUI( 'uiAudioFiles' )
        self.audioFilesTree_.removeAllChildren()
        self.audioFilesTree_.detach()
        self.audioFilesTree_ = tree
        self.audioFilesTree_.attachTo( treeRoot )

    def uiAddTreeCategory( self, *args ):
        treeUI = self.getUI( 'uiAudioFiles' )

        selectedNode = treeUI.selected_node

        if not selectedNode or not isinstance( selectedNode, TreeNode ):
            selectedNode = self.audioFilesTree_

        # now open the dialogue
        popup.showTextInputPopup( title = 'New Category', message = 'Enter Category Name', inputMessage = 'Category',
                                  yesButton = 'Create', noButton = 'Cancel', parent = self,
                                  callback = lambda x: self._completeNewCategory( x.selection_, selectedNode, x.text_ ) )
        return

    def _completeNewCategory( self, button, parentNode, text ):
        if button == WindowCloseState.YES:
            Logger.trace( 'Adding %s node to %s', text, parentNode.id_ )
            if parentNode.hasChild( text ):
                Logger.trace( 'Node already exists', text, parentNode.id_ )
                popup.showOkPopup( 'New Category', message = 'Category \'%s\' already exists within \'%s\'' % ( text, parentNode.id_ ) )
                return

            node = TreeNode( id = text, tree = parentNode.tree_ )
            parentNode.addChild( node )
            node.openParents()
