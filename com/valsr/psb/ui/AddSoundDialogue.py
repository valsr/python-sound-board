'''
Created on Jan 14, 2017

@author: radoslav
'''
from kivy.lang import Builder
from com.valsr.psb.ui.WindowBase import WindowBase

class AddSoundDialogue(WindowBase):
    '''
    classdocs
    '''
    def getRootUI(self):
        return Builder.load_file("ui/kv/addsound.kv")
        