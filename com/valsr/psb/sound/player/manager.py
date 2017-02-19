"""
Created on Jan 19, 2017

@author: valsr <valsr@valsr.com>
"""
from kivy.logger import Logger

from com.valsr.psb.sound.player import FilePlayer


class PlayerManager:
    """Manages all players allowing for creation, storage, retrieval by given identifier. All methods are static
    eliminating the need for object creation.
    """
    players = {}

    def __init__(self):
        """Constructor"""
        super().__init__()

    @staticmethod
    def waveform(player_id):
        """Obtain waveform by given identifier

        Args:
            player_id: Player identifier

        Returns:
            PlayerBase or None
        """
        if player_id in PlayerManager.players:
            return PlayerManager.players[player_id]

        return None

    @staticmethod
    def create_player(file_path):
        """Create waveform for given path

        Args:
            file_path: Path to media file

        Returns:
            id, p: Player id and the waveform it self
        """
        p = FilePlayer(file_path)
        PlayerManager.players[p.id] = p

        Logger.debug("Number of active players %d", len(PlayerManager.players))
        return (p.id, p)

    @staticmethod
    def destroy_player(player_id):
        """Destroy given waveform and free resources

        Args:
            player_id: Player player_id
        """
        p = PlayerManager.players.pop(player_id, None)
        Logger.debug("Number of active players %d", len(PlayerManager.players))
        if p is not None:
            p.stop()
            p.destroy()
