'''
Created on Jan 19, 2017

@author: radoslav
'''
from kivy.logger import Logger
import uuid

from com.valsr.psb.sound.player import FilePlayer


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
        p = FilePlayer( id, filePath )
        _PLAYERS_[id] = p

        Logger.debug( "Number of active players %d" % len( _PLAYERS_ ) )
        return ( id, p )

    @staticmethod
    def destroyPlayer( id ):
        global _PLAYERS_
        p = _PLAYERS_.pop( id, None )
        Logger.debug( "Number of active players %d" % len( _PLAYERS_ ) )
        if p is not None:
            p.stop()
            p.destroy()
