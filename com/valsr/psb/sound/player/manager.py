'''
Created on Jan 19, 2017

@author: radoslav
'''
from kivy.logger import Logger
import uuid

from com.valsr.psb.sound.player import FilePlayer

class PlayerManager:
    '''
    Manages all players allowing for creation, storage, retrieval by given identifier. All methods are static 
    eliminating the need for object creation.
    '''
    _PLAYERS_ = {}
    def __init__( self ):
        '''
        Constructor
        '''
        super().__init__()

    @staticmethod
    def getPlayer( id ):
        '''
        Obtain player by given identifier

        Parameters:
            id -- Player identifier

        Returns:
            PlayerBase or None
        '''
        if id in PlayerManager._PLAYERS_:
            return PlayerManager._PLAYERS_[id]

        return None

    @staticmethod
    def createPlayer( filePath ):
        '''
        Create player for given path

        Parameters:
            filePath -- Path to media file

        Returns:
            id, p -- Player id and the player it self
        '''
        id = str( uuid.uuid1().int )
        p = FilePlayer( id, filePath )
        PlayerManager._PLAYERS_[id] = p

        Logger.debug( "Number of active players %d" , len( PlayerManager._PLAYERS_ ) )
        return ( id, p )

    @staticmethod
    def destroyPlayer( id ):
        '''
        Destroy given player and free resources
        
        Parameters:
            id -- Player id
        '''
        p = PlayerManager._PLAYERS_.pop( id, None )
        Logger.debug( "Number of active players %d" , len( PlayerManager._PLAYERS_ ) )
        if p is not None:
            p.stop()
            p.destroy()
