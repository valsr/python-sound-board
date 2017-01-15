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
        self.getRootUI().ids['fc'].path = self.cwd_
        self.getRootUI().ids['pathinp'].text = self.cwd_
        
    def createRootUI(self):
        return Builder.load_file("ui/kv/addsound.kv")
    
    def on_autoplay_label(self, touch):
        print (touch)
        label = self.getUI('AutoPlayLabel')
        if label.collide_point(*touch.pos):
            self.getUI('AutoPlayButton').active = not self.getUI('AutoPlayButton').active
     
    def cancel(self, *args):   
        self.dismiss()
        
    #def open(self, *args):
    #    self.dismiss()