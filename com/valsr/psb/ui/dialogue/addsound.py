'''
Created on Jan 14, 2017

@author: radoslav
'''
from gi.repository import Gst
from kivy.lang import Builder
import os

from com.valsr.psb import utility
from com.valsr.psb.sound import PlayerState
from com.valsr.psb.sound.player.manager import PlayerManager
from com.valsr.psb.ui.widget.waveform import WaveformWidget  # Needed by kv file
from com.valsr.psb.ui.window.base import WindowBase, WindowCloseState


class AddSoundDialogue(WindowBase):
    '''
    classdocs
    '''

    def __init__(self, **kwargs):
        WindowBase.__init__(self, **kwargs)
        self.title = "Add Audio File"
        self.cwd_ = os.getcwd()
        self.file = None
        self.playerId_ = None

    def on_open(self, **kwargs):
        self.get_ui('Files').path = self.cwd_
        self.get_ui('PathInput').text = self.cwd_
        self.get_ui('Files').filters.append(self.uiFilterFiles)

    def create_root_ui(self):
        return Builder.load_file("ui/kv/addsound.kv")

    def uiAutoplayLabel(self, touch):
        label = self.get_ui('AutoPlayLabel')
        if label.collide_point(*touch.pos):
            self.get_ui('AutoPlayButton').active = not self.get_ui('AutoPlayButton').active

    def uiCancel(self, *args):
        if self.playerId_ is not None:
            PlayerManager.destroy_player(self.playerId_)

        self.close_state = WindowCloseState.CANCEL
        self.dismiss()

    def uiOpen(self, *args):
        if self.playerId_ is not None:
            PlayerManager.destroy_player(self.playerId_)

        self.close_state = WindowCloseState.OK
        self.dismiss()

    def uiFilterFiles(self, folder, file):
        if os.path.isdir(file):
            return True

        if self.get_ui('PathInput').text is not folder:
            self.get_ui('PathInput').text = folder
        ext = os.path.splitext(file)[1]
        return ext.lower() in utility.allowed_audio_formats()

    def fileSelection(self, *args):
        files = self.get_ui('Files')
        file = files.selection[0]

        if os.path.isfile(file):
            self.file = file
            self.autoPlay(file)
            pass

        return True

    def autoPlay(self, file):
        if self.get_ui('AutoPlayButton').active:
            if self.playerId_ is not None:
                PlayerManager.destroy_player(self.playerId_)

            (id, p) = PlayerManager.create_player(file)
            self.get_ui('Waveform').file = file
            self.playerId_ = id
            p.register_update_callback(self.updateUI)
            p.register_message_callback(self.messageCallback)
            p.play()
            self.get_ui('Waveform').waveform = p

    def messageCallback(self, waveform, bus, message):
        if message.type == Gst.MessageType.EOS:
            self.onStop()

    def updateUI(self, waveform, delta):
        pos = waveform.position
        self.get_ui('Waveform').position_ = pos

    def onStop(self):
        if self.playerId_ is not None:
            p = PlayerManager.waveform(self.playerId_)
            p.stop()

    def onPlay(self):
        if self.playerId_ is not None:
            p = PlayerManager.waveform(self.playerId_)
            if p.state == PlayerState.PLAYING:
                p.pause()
            else:
                p.play()
