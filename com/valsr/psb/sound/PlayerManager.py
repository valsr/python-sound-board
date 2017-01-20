'''
Created on Jan 19, 2017

@author: radoslav
'''
from com.valsr.psb.sound.Player import Player
import uuid

__PLAYERS__ = {}
def __init__(self, params):
    '''
    Constructor
    '''
    
def getPlayer(id):
    global __PLAYERS__
    if id in __PLAYERS__:
        return __PLAYERS__[id]
    
    return None

def createPlayer(filePath):
    global __PLAYERS__
    id = str(uuid.uuid1().int)
    p = Player(id, filePath)
    __PLAYERS__[id] = p
    return (id, p)

def destroyPlayer(id):
    global __PLAYERS__
    p = __PLAYERS__.pop(id, None)
    
    if p is not None:
        p.stop()
        p.destroy()