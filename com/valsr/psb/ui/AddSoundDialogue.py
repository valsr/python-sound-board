'''
Created on Jan 14, 2017

@author: radoslav
'''
from kivy.lang import Builder
from com.valsr.psb.ui.WindowBase import WindowBase
import os
from com.valsr.psb.sound import PlayerManager
from kivy.logger import Logger
from kivy.clock import Clock
from com.valsr.psb.sound.Util import PlayerState

class AddSoundDialogue(WindowBase):
    '''
    classdocs
    '''
    cwd_ = os.getcwd()
    file_ = None
    playerId_ = None
    
    def init(self, **kwargs):
        self.title = "Add Audio File"
        pass
    
    def on_open(self, **kwargs):
        self.getUI('Files').path = self.cwd_
        self.getUI('PathInput').text = self.cwd_
        self.getUI('Files').filters.append(self.uiFilterFiles)
        
    def createRootUI(self):
        return Builder.load_file("ui/kv/addsound.kv")
    
    def uiAutoplayLabel(self, touch):
        label = self.getUI('AutoPlayLabel')
        if label.collide_point(*touch.pos):
            self.getUI('AutoPlayButton').active = not self.getUI('AutoPlayButton').active
     
    def uiCancel(self, *args):
        if self.playerId_ is not None:
            PlayerManager.destroyPlayer(self.playerId_)
            
        self.dismiss()
        
    def uiOpen(self, *args):
        if self.playerId_ is not None:
            PlayerManager.destroyPlayer(self.playerId_)
        
        self.dismiss()
    
    def uiFilterFiles(self, folder, file):
        if os.path.isdir(file):
            return True
        
        if self.getUI('PathInput').text is not folder:
            self.getUI('PathInput').text = folder
        ext = os.path.splitext(file)[1]
        return ext.lower() in self.controller_.getAllowedAudioFiles()
    
    def fileSelection(self, *args):
        files = self.getUI('Files')
        
        file = files.selection[0]
             
        if os.path.isfile(file):
            self.autoPlay(file)
            pass
        
        return True
    
    def autoPlay(self, file):
        if self.getUI('AutoPlayButton').active:
            if self.playerId_ is not None:
                PlayerManager.destroyPlayer(self.playerId_)
            
            (id, p) = PlayerManager.createPlayer(file)
            self.playerId_ = id
            p.play()
            Clock.schedule_once(self.updateUI, 1)
            
            # load wave FORM
            # play file
            
    def updateUI(self, delta):
        if self.playerId_:
            p = PlayerManager.getPlayer(self.playerId_)
            dur = p.queryTime()
            pos = p.queryPos()
            
            Logger.debug(str(pos) + "/" + str(dur))
            Logger.debug(p.getState().name)
            if p.getState() is PlayerState.READY:
                PlayerManager.destroyPlayer(self.playerId_)
                self.playerId_ = None
            Clock.schedule_once(self.updateUI, 1)
            
    def onStop(self):
        if self.playerId_ is not None:
            p = PlayerManager.getPlayer(self.playerId_)
            p.stop()
    
    def onPlay(self):
        if self.playerId_ is not None:
            p = PlayerManager.getPlayer(self.playerId_)
            if p.getState() == PlayerState.PLAYING:
                p.pause()
            else:
                p.play()