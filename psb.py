'''
Created on Jan 13, 2017

@author: radoslav
'''
from kivy.app import App
from com.valsr.psb.ui.MainWindow import MainWindow
from kivy.uix.floatlayout import FloatLayout
from kivy.logger import Logger

class PSB(App):
    theme_ = 'white'
    ui_ = None
    activeWindow_ = []
    actionBinds_ = {}
 
    def bindAction(self, windowId, action, callback):
        actionsDict = self.actionBinds_[action] if action in self.actionBinds_ else {}
        callbackList = actionsDict[windowId] if windowId in actionsDict else [] 
        
        Logger.debug("Binding %s for %s " %(action, windowId))
        callbackList.append(callback)
        actionsDict[windowId] = callbackList
        self.actionBinds_[action] = actionsDict
        
    def action(self, windowId, action, *args, **kwargs):
        actionsDict = self.actionBinds_[action] if action in self.actionBinds_ else {}
        
        if windowId is not None:
            callbackList = actionsDict[windowId] if windowId in actionsDict else []
        else:
            callbackList = [v for k,v in actionsDict]
        
        handled = False
        for callback in callbackList:
            print('Callback found')
            handled = callback(*args, **kwargs)
            if handled:
                break
        
        if not handled:
            Logger.info("Unhandled action %s for window %s" %(action, windowId))
    
    def unBindAction(self, windowId, action, all = False):
        actionsDict = self.actionBinds_[action] if action in self.actionBinds_ else {}
        callbackList = actionsDict[windowId] if windowId in actionsDict else [] 
        
        if all:
            callbackList = []
        else:
            callbackList.pop()
        
        actionsDict[windowId] = callbackList
        self.actionBinds_[action] = actionsDict
    
    def openWindow(self, windowClass, **kwargs):
        window = windowClass(self)
        
        if 'size_hint' in kwargs:
            window.size_hint = kwargs['size_hint']
            
        if 'draggable' in kwargs:
            window.draggable = kwargs['draggable']
        
        if 'title' in kwargs:
            window.title = kwargs['title']
            
        window.open(self.ui_)
        
        return window
    
    def addWindow(self, window, replace=False, size_hint=(1.0, 1.0)):
        if replace == True:
            old = self.activeWindow_.pop()
            self.ui_.remove_widget(old.ui_)
            if old:
                old.destroy()
        window.size_hint = size_hint
        window.open()
        
    
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
