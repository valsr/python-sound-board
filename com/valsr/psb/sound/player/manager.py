'''
Created on Jan 19, 2017

@author: radoslav
'''
import uuid

from com.valsr.psb.sound.player import Player


_PLAYERS_ = {}

class PlayerManager:
    def __init__( self, params ):
        '''
        Constructor
        '''
    @staticmethod
    def getPlayer( id ):
        global _PLAYERS_
        if id in _PLAYERS_:
            return _PLAYERS_[id]

        return None

    @staticmethod
    def createPlayer( filePath ):
        global _PLAYERS_
        id = str( uuid.uuid1().int )
        p = Player( id, filePath )
        _PLAYERS_[id] = p
        return ( id, p )

    @staticmethod
    def destroyPlayer( id ):
        global _PLAYERS_
        p = _PLAYERS_.pop( id, None )

        if p is not None:
            p.stop()
            p.destroy()
