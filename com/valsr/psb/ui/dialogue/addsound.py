'''
Created on Jan 14, 2017

@author: radoslav
'''
from gi.repository import Gst
from kivy.lang import Builder
import os

from com.valsr.psb.sound import PlayerState
from com.valsr.psb.sound.player.manager import PlayerManager
from com.valsr.psb.ui.widget.waveform import WaveformWidget # Needed by kv file
from com.valsr.psb.ui.window.base import WindowBase, WindowCloseState


class AddSoundDialogue( WindowBase ):
    '''
    classdocs
    '''

    def __init__( self, **kwargs ):
        WindowBase.__init__( self, **kwargs )
        self.title = "Add Audio File"
        self.cwd_ = os.getcwd()
        self.file_ = None
        self.playerId_ = None

    def on_open( self, **kwargs ):
        self.getUI( 'Files' ).path = self.cwd_
        self.getUI( 'PathInput' ).text = self.cwd_
        self.getUI( 'Files' ).filters.append( self.uiFilterFiles )

    def createRootUI( self ):
        return Builder.load_file( "ui/kv/addsound.kv" )

    def uiAutoplayLabel( self, touch ):
        label = self.getUI( 'AutoPlayLabel' )
        if label.collide_point( *touch.pos ):
            self.getUI( 'AutoPlayButton' ).active = not self.getUI( 'AutoPlayButton' ).active

    def uiCancel( self, *args ):
        if self.playerId_ is not None:
            PlayerManager.destroyPlayer( self.playerId_ )

        self.closeState_ = WindowCloseState.CANCEL
        self.dismiss()

    def uiOpen( self, *args ):
        if self.playerId_ is not None:
            PlayerManager.destroyPlayer( self.playerId_ )

        self.closeState_ = WindowCloseState.OK
        self.dismiss()

    def uiFilterFiles( self, folder, file ):
        if os.path.isdir( file ):
            return True

        if self.getUI( 'PathInput' ).text is not folder:
            self.getUI( 'PathInput' ).text = folder
        ext = os.path.splitext( file )[1]
        return ext.lower() in self.controller_.getAllowedAudioFiles()

    def fileSelection( self, *args ):
        files = self.getUI( 'Files' )
        file = files.selection[0]

        if os.path.isfile( file ):
            self.file_ = file
            self.autoPlay( file )
            pass

        return True

    def autoPlay( self, file ):
        if self.getUI( 'AutoPlayButton' ).active:
            if self.playerId_ is not None:
                PlayerManager.destroyPlayer( self.playerId_ )

            ( id, p ) = PlayerManager.createPlayer( file )
            self.getUI( 'Waveform' ).file_ = file
            self.playerId_ = id
            p.registerUpdateCallback( self.updateUI )
            p.registerMessageCallback( self.messageCallback )
            p.play()
            self.getUI( 'Waveform' ).player = p

    def messageCallback( self, player, bus, message ):
        if message.type == Gst.MessageType.EOS:
            self.onStop()

    def updateUI( self, player, delta ):
        pos = player.position
        self.getUI( 'Waveform' ).position_ = pos

    def onStop( self ):
        if self.playerId_ is not None:
            p = PlayerManager.getPlayer( self.playerId_ )
            p.stop()

    def onPlay( self ):
        if self.playerId_ is not None:
            p = PlayerManager.getPlayer( self.playerId_ )
            if p.state_ == PlayerState.PLAYING:
                p.pause()
            else:
                p.play()
