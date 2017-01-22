'''
Created on Jan 14, 2017

@author: radoslav
'''
from gi.repository import Gst
from kivy.lang import Builder
from kivy.logger import Logger
import os

from com.valsr.psb.sound import PlayerManager
from com.valsr.psb.sound.Util import PlayerState
from com.valsr.psb.ui.WindowBase import WindowBase
from com.valsr.psb.ui.widget.WaveformWidget import WaveformWidget


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

        self.dismiss()

    def uiOpen( self, *args ):
        if self.playerId_ is not None:
            PlayerManager.destroyPlayer( self.playerId_ )

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
            self.autoPlay( file )
            pass

        return True

    def autoPlay( self, file ):
        if self.getUI( 'AutoPlayButton' ).active:
            if self.playerId_ is not None:
                PlayerManager.destroyPlayer( self.playerId_ )

            ( id, p ) = PlayerManager.createPlayer( file )
            self.playerId_ = id
            p.registerUpdateCallback( self.updateUI )
            p.registerMessageCallback( self.messageCallback )
            p.play()

            # load wave FORM
            # play file

    def messageCallback( self, player, bus, message ):
        if message.type == Gst.MessageType.EOS:
            print( "blha" )
            self.onStop()

    def updateUI( self, player, delta ):
        dur = player.queryTime()
        pos = player.queryPos()

        Logger.debug( player.getState().name )
        Logger.debug( str( pos ) + "/" + str( dur ) )

    def onStop( self ):
        if self.playerId_ is not None:
            p = PlayerManager.getPlayer( self.playerId_ )
            p.stop()

    def onPlay( self ):
        if self.playerId_ is not None:
            p = PlayerManager.getPlayer( self.playerId_ )
            if p.getState() == PlayerState.PLAYING:
                p.pause()
            else:
                p.play()
