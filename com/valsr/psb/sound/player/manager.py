'''
Created on Jan 19, 2017

@author: radoslav
'''
import uuid

from com.valsr.psb.sound.player import Player


__PLAYERS__ = {}

class PlayerManager:
    def __init__( self, params ):
        '''
        Constructor
        '''
    @staticmethod
    def getPlayer( id ):
        global __PLAYERS__
        if id in __PLAYERS__:
            return __PLAYERS__[id]

        return None

    @staticmethod
    def createPlayer( filePath ):
        global __PLAYERS__
        id = str( uuid.uuid1().int )
        p = Player( id, filePath )
        __PLAYERS__[id] = p
        return ( id, p )

    @staticmethod
    def destroyPlayer( id ):
        global __PLAYERS__
        p = __PLAYERS__.pop( id, None )

        if p is not None:
            p.stop()
            p.destroy()
