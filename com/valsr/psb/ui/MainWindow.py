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
        
    def getRootUI(self):
        return Builder.load_file("ui/kv/main.kv") 

    def bindActions(self, controller):
        #controller.bindAction(self.ui_.id, 'addsound', self.addSound)
        #print (self.ui_.ids)
        self.ui_.ids['addsound'].bind(on_press=self.addSound)
        
    def addSound2(self, *args, **kwargs):
        print ("EHLO")
        
    def addSound(self, *args):
        # create form and bind to its closing dispatch
        window = AddSoundDialogue(self)
        window.windowed = True
        self.addWindow(window, size_hint=(0.75, 0.75))
        self._parent.open()
        print("hello form here for %s" % self.id)
