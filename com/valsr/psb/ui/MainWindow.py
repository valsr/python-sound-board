'''
Created on Jan 14, 2017

@author: radoslav
'''
from kivy.lang import Builder
from com.valsr.psb.ui.WindowBase import WindowBase
from com.valsr.psb.ui.AddSoundDialogue import AddSoundDialogue

class MainWindow(WindowBase):
    '''
    classdocs
    '''
        
    def createRootUI(self):
        return Builder.load_file("ui/kv/main.kv") 

    def uiAddSound(self, *args):
        window = self.controller_.openWindow(AddSoundDialogue, windowed = True, size_hint=(0.75,0.75))
