'''
Created on Jan 17, 2017

@author: radoslav
'''

class Waveform():
    def __init__( self, file, **kwargs ):
        self.file_ = file
        self.lChannel_ = []
        self.rChannel_ = []

    def isReady( self ):
        return True
