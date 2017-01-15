'''
Created on Jan 13, 2017

@author: radoslav
'''
from kivy.app import App
from com.valsr.psb.ui.MainWindow import MainWindow
from kivy.uix.floatlayout import FloatLayout

class PSB(App):
    theme_ = 'white'
    ui_ = None
    activeWindow_ = []
  
    def openWindow(self, windowClass, **kwargs):
        window = windowClass(self)
        
        if 'size_hint' in kwargs:
            window.size_hint = kwargs['size_hint']
            
        if 'draggable' in kwargs:
            window.draggable = kwargs['draggable']
        
        if 'title' in kwargs:
            window.title = kwargs['title']
         
        if 'windowed' in kwargs:
            window.windowed = kwargs['windowed']
               
        window.open()
        
        return window        
    
    def getThemeImageFilename(self, name, size):
        return "ui/fontawesome/%s/png/%d/%s.png" % (self.theme_, size, name)
            
    def build(self):
        self.ui_ = FloatLayout()
        self.openWindow(MainWindow, draggable = 'None', title='PSB')
        return self.ui_

    def getUIRoot(self):
        return self.ui_

if __name__ == '__main__':
    PSB().run()
