'''
Created on Jan 14, 2017

@author: radoslav
'''
from kivy.lang import Builder
from com.valsr.psb.ui.WindowBase import WindowBase

class MainWindow(WindowBase):
    '''
    classdocs
    '''
        
    def getRootUI(self):
        return Builder.load_file("ui/kv/main.kv") 