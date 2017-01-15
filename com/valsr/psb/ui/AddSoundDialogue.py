'''
Created on Jan 14, 2017

@author: radoslav
'''
from kivy.lang import Builder
from com.valsr.psb.ui.WindowBase import WindowBase
import os

class AddSoundDialogue(WindowBase):
    '''
    classdocs
    '''
    cwd_ = os.getcwd()
    file_ = None
    
    def init(self, **kwargs):
        self.title = "Add Audio File"
        pass
    def on_open(self, **kwargs):
        self.ui_.ids['fc'].path = self.cwd_
        self.ui_.ids['pathinp'].text = self.cwd_
        
    def getRootUI(self):
        return Builder.load_file("ui/kv/addsound.kv")
        