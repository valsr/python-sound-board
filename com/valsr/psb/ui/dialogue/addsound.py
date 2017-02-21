"""
Created on Jan 14, 2017

@author: valsr <valsr@valsr.com>
"""
import os
from gi.repository import Gst
from kivy.lang import Builder

from com.valsr.psb import utility
from com.valsr.psb.sound import PlayerState
from com.valsr.psb.sound.player.manager import PlayerManager
from com.valsr.psb.ui.widget.waveform import WaveformWidget  # Needed by kv file
from com.valsr.psb.ui.window.base import WindowBase, WindowCloseState


class AddSoundDialogue(WindowBase):
    """Add sound dialogue"""

    def __init__(self, **kwargs):
        WindowBase.__init__(self, **kwargs)
        self.title = "Add Audio File"
        self.cwd = os.getcwd()
        self.file = None
        self.player_id = None

    def on_open(self, **kwargs):
        """Perform dialogue opening actions"""
        self.get_ui('files').path = self.cwd
        self.get_ui('path_input').text = self.cwd
        self.get_ui('files').filters.append(self.audio_file_filter)

    def create_root_ui(self):
        return Builder.load_file("ui/kv/addsound.kv")

    def ui_autoplay_label(self, touch):
        """Handles clicking on the auto-play label"""
        label = self.get_ui('autoplay_button')
        if label.collide_point(*touch.pos):
            self.get_ui('autoplay_button').active = not self.get_ui('autoplay_button').active

    def ui_cancel(self, *args):
        """Handles cancel button action"""
        if self.player_id is not None:
            PlayerManager.destroy_player(self.player_id)

        self.close_state = WindowCloseState.CANCEL
        self.dismiss()

    def ui_open(self, *args):
        """Handles open button action"""
        if self.player_id is not None:
            PlayerManager.destroy_player(self.player_id)

        self.close_state = WindowCloseState.OK
        self.dismiss()

    def audio_file_filter(self, folder, file):
        """Filters to filter non-audio files

        Args:
            folder: Folder path
            file: File path (in folder)

        Returns:
            Boolean (whether file is acceptable)
        """
        if os.path.isdir(file):
            return True

        if self.get_ui('path_input').text is not folder:
            self.get_ui('path_input').text = folder
        ext = os.path.splitext(file)[1]
        return ext.lower() in utility.allowed_audio_formats()

    def ui_file_selection(self, *args):
        """Handles selecting files in the file selection list"""
        files = self.get_ui('files')
        file = files.selection[0]

        if os.path.isfile(file):
            self.file = file
            self.handle_auto_play(file)

        return True

    def handle_auto_play(self, file):
        """Handle auto-play files"""
        if self.get_ui('autoplay_button').active:
            if self.player_id is not None:
                PlayerManager.destroy_player(self.player_id)

            (player_id, p) = PlayerManager.create_player(file)
            self.get_ui('waveform').file = file
            self.player_id = player_id
            p.register_update_callback(self.update_ui)
            p.register_message_callback(self.message_callback)
            p.play()
            self.get_ui('waveform').associate_player(p)

    def message_callback(self, player, bus, message):
        """Message callback for the player

        Args:
            player: Audio player
            bus: Message bus
            message: Message event
        """
        if message.type == Gst.MessageType.EOS:
            self.stop()

    def update_ui(self, player, delta):
        """Handles player

        Args:
            player: Player
            delta: Time change
        """
        pos = player.position
        self.get_ui('waveform').position = pos

    def ui_stop(self):
        """Handles stopping current player (either via stop button or code)"""
        if self.player_id is not None:
            p = PlayerManager.player(self.player_id)
            p.stop()

    def ui_play(self):
        """Handles starting/pausing current player (either via play button or code)"""
        if self.player_id is not None:
            p = PlayerManager.player(self.player_id)
            if p.state == PlayerState.PLAYING:
                p.pause()
            else:
                p.play()
