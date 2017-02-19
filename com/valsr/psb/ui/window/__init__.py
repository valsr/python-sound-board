'''
Created on Jan 14, 2017

@author: radoslav
'''
import json
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
import os

from com.valsr.psb import utility
from com.valsr.psb.sound.info import MediaInfoManager
from com.valsr.psb.tree import TreeNode
from com.valsr.psb.ui.dialogue import popup, addsound
from com.valsr.psb.ui.dialogue.addsound import AddSoundDialogue
from com.valsr.psb.ui.dialogue.open import OpenDialogue
from com.valsr.psb.ui.dialogue.save import SaveDialogue
from com.valsr.psb.ui.menu import SimpleMenuItem, Menu
from com.valsr.psb.ui.widget.draggabletreeview import DraggableTreeView, DraggableTreeViewNode
from com.valsr.psb.ui.window.base import WindowBase, WindowCloseState
from com.valsr.psb.ui.window.manager import WindowManager


class MainWindow(WindowBase):
    '''
    classdocs
    '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file = None
        self.audioFilesTree_ = None

    def create_root_ui(self):
        return Builder.load_file("ui/kv/main.kv")

    def on_create(self):
        self.audioFilesTree_ = self.get_ui('uiAudioFiles')
        utility.load_project('test.psb', self.audioFilesTree_)

        root = self.get_ui('test')
        layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        # Make sure the height is such that there is something to scroll.
        layout.bind(minimum_height=layout.setter('height'))
        for i in range(30):
            btn = Button(text=str(i), size_hint_y=None, height=40)
            layout.add_widget(btn)
        sv = ScrollView(size_hint=(None, 1))
        sv.add_widget(layout)
        root.add_widget(sv)

    def uiAddSound(self, *args):
        self.addSoundWindow_ = WindowManager.create_window(
            AddSoundDialogue, self, create_opts={"size_hint": (0.75, 0.75)})
        self.addSoundWindow_.bind(on_dismiss=self.uiAddSoundDismiss)
        self.addSoundWindow_.open()

    def uiAddSoundDismiss(self, *args):
        if self.addSoundWindow_.close_state == WindowCloseState.OK:
            if not self.audioFilesTree_.root.find_node(lambda x: x._label.text.lower() == 'uncategorized'):
                self.audioFilesTree_.add_node(DraggableTreeViewNode(label='Uncategorized'))

            self._addFileImpl(self.addSoundWindow_.file)
        else:
            self.addSoundWindow_ = None

    def _addFileImpl(self, file):
        # check the fingerprint and see if we already have it
        info = MediaInfoManager.get_media_info(file, reload_on_error=True)
        if not info:
            Clock.schedule_once(lambda x: self._addFileImpl(file), 0.1)
            return

        if self.audioFilesTree_.root.find_node(lambda x: x.data is not None and x.data.fingerprint == info.fingerprint):
            popup.showOkPopup('File Already Added', 'File by similar fingerprint has already been added', parent=self)
            return

        Logger.debug("Adding to %s to collection", file)
        parent = self.audioFilesTree_.root.find_node(lambda x: x._label.text.lower() == 'uncategorized', False)
        parent.add_node(DraggableTreeViewNode(id=file, label=os.path.basename(file), data=info))

    def ui_save(self, *args):
        if self.file is None:
            # open file to save assert
            self.saveWindow_ = self.controller_.open_window(SaveDialogue, windowed=True, size_hint=(0.75, 0.75))
            self.saveWindow_.bind(on_dismiss=lambda x: self._saveImpl(fromDialogue=True))
        else:
            self._saveImpl()

    def _saveImpl(self, fromDialogue=False):
        if fromDialogue:
            if self.saveWindow_.close_state != WindowCloseState.OK:
                return
            self.file = self.saveWindow_.file
        utility.save_project(self.file, self.audioFilesTree_, None)
        self.title = "PSB: " + self.file

    def ui_open(self, *args):
        self.openWindow_ = WindowManager.create_window(
            OpenDialogue, parent=None, create_opts={'windowed': True, 'size_hint': (0.75, 0.75)})
        self.openWindow_.bind(on_dismiss=self._openImpl)
        self.openWindow_.open()

    def _openImpl(self, *args):
        self.file = self.openWindow_.file
        if self.openWindow_.close_state == WindowCloseState.OK:
            utility.load_project(self.file, self.audioFilesTree_)
        WindowManager.destroy_window(self.openWindow_.id)

    def uiAddTreeCategory(self, *args):
        selectedNode = self.audioFilesTree_.selected_node

        if selectedNode == None:
            selectedNode = self.audioFilesTree_.root

        # now open the dialogue
        popup.showTextInputPopup(title='New Category', message='Enter Category Name', inputMessage='Category',
                                 yesButton='Create', noButton='Cancel', parent=self,
                                 callback=lambda x: self._completeNewCategory(x.selection_, selectedNode, x.text_))
        return

    def _completeNewCategory(self, button, parentNode, text):
        if button == WindowCloseState.YES:
            Logger.trace('Adding %s node to %s', text, parentNode.id)
            # find if we have the node by text
            if parentNode.find_node(lambda x: x.ui.text == text, False):
                Logger.trace('Node by %s already exists', text)
                popup.showOkPopup(
                    'New Category', message='Category \'%s\' already exists within \'%s\'' % (text, parentNode.id))
                return

            node = DraggableTreeViewNode(label=text)
            parentNode.add_node(node).open(True)

    def uiFileTreeTouchUp(self, fileNode, touch):
        if touch.button == 'left':
            # create menu
            Logger.debug('Touch up from %s', fileNode.text)
            m = Menu(controller=self.controller_)
            m.addMenuItem(SimpleMenuItem(text='test'))
            m.addMenuItem(SimpleMenuItem(text='test2'))
            m.open()
            pass

    # def on_
