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
        pass
    def on_open(self, **kwargs):
        #self.ids['fc'].path = self.cwd_
        print(self.ids)
        print(self.cwd_)
        
    def getRootUI(self):
        return Builder.load_file("ui/kv/addsound.kv")
        