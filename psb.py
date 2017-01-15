'''
Created on Jan 13, 2017

@author: radoslav
'''
from kivy.app import App
from com.valsr.psb.ui.MainWindow import MainWindow
from kivy.uix.floatlayout import FloatLayout
from com.valsr.psb.ui.AddSoundDialogue import AddSoundDialogue
import os

class PSB(App):
    theme_ = 'white'
    ui_ = None
    activeWindow_ = []
    
    def on_autoplay_label(self, touch):
        # if self.ui_.ids['uiAutoPlayLabel'].collide_point(*touch.pos):
        #    self.ui_.ids['uiAutoPlay'].active = not self.ui_.ids['uiAutoPlay'].active
        pass
     
    def on_add_sound(self):
        window = AddSoundDialogue(self)
        window.windowed = True
        self.addWindow(window, size_hint=(0.75, 0.75))
            
    def addWindow(self, window, replace=False, size_hint=(1.0, 1.0)):
        if replace == True:
            old = self.activeWindow_.pop()
            self.ui_.remove_widget(old.ui_)
            if old:
                old.destroy()
        window.size_hint = size_hint
        window.open(self.ui_)
        # self.ui_.add_widget(window.create())
        # self.activeWindow_.append(window)
        
    
    def getThemeImageFilename(self, name, size):
        return "ui/fontawesome/%s/png/%d/%s.png" % (self.theme_, size, name)
            
    def build(self):
        self.ui_ = FloatLayout()
        main = MainWindow(self)
        main.draggable = 'None'
        self.addWindow(main)
        return self.ui_



if __name__ == '__main__':
    PSB().run()
