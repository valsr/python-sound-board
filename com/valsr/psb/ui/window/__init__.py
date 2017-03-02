"""
Created on Jan 14, 2017

@author: valsr <valsr@valsr.com>
"""
import json
import os
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView

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
    """Main PSB window"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file = None
        self.audio_files_tree = None

        # windows
        self._open_window = None
        self._save_window = None
        self._add_sound_window = None

    def create_root_ui(self):
        return Builder.load_file("ui/kv/main.kv")

    def on_create(self):
        self.audio_files_tree = self.get_ui('audio_files')
        utility.load_project('test.psb', self.audio_files_tree)

        self.audio_files_tree.bind(on_touch_up=self.ui_file_tree_touch_up)

    def ui_add_sound(self, *args):
        """Handle add sound button event"""
        self._add_sound_window = WindowManager.create_window(AddSoundDialogue, self,
                                                             create_opts={"size_hint": (0.75, 0.75)})
        self._add_sound_window.bind(on_dismiss=self._add_sound_dismiss)
        self._add_sound_window.open()

    def _add_sound_dismiss(self, *args):
        """Handle dismissal of the add sound dialogue"""
        if self._add_sound_window.close_state == WindowCloseState.OK:
            if not self.audio_files_tree.root.find_node(lambda x: x._label.text.lower() == 'uncategorized'):
                self.audio_files_tree.add_node(DraggableTreeViewNode(label='Uncategorized'))

            self._add_audio_file(self._add_sound_window.file)
        else:
            self._add_sound_window = None

    def _add_audio_file(self, file):
        # check the fingerprint and see if we already have it
        info = MediaInfoManager.get_media_info(file, reload_on_error=True)
        if not info:
            Clock.schedule_once(lambda x: self._add_audio_file(file), 0.1)
            return

        if self.audio_files_tree.root.find_node(lambda x: x.data and x.data.fingerprint == info.fingerprint):
            popup.show_ok_popup(
                'File Already Added', 'File by similar fingerprint has already been added', parent=self)
            return

        Logger.debug("Adding to %s to collection", file)
        parent = self.audio_files_tree.root.find_node(lambda x: x._label.text.lower() == 'uncategorized', False)
        parent.add_node(DraggableTreeViewNode(id=file, label=os.path.basename(file), data=info))

    def ui_save_project(self, *args):
        """Handle save button event"""
        if self.file is None:
            # open file to save assert
            self._save_window = WindowManager.create_window(SaveDialogue, parent=None,
                                                            create_opts={'windowed': True, 'size_hint': (0.75, 0.75)})
            self._save_window.bind(on_dismiss=lambda x: self._save_project(from_dialogue=True))
            self._save_window.open()
        else:
            self._save_project()

    def _save_project(self, from_dialogue=False):
        if from_dialogue:
            if self._save_window.close_state != WindowCloseState.OK:
                WindowManager.destroy_window(self._save_window.id)
                return
            self.file = self._save_window.file
            WindowManager.destroy_window(self._save_window.id)
        utility.save_project(self.file, self.audio_files_tree, None)
        self.title = "PSB: " + self.file

    def ui_open_project(self, *args):
        """Handle open button event"""
        self._open_window = WindowManager.create_window(OpenDialogue, parent=None,
                                                        create_opts={'windowed': True, 'size_hint': (0.75, 0.75)})
        self._open_window.bind(on_dismiss=self._open_project)
        self._open_window.open()

    def _open_project(self, *args):
        self.file = self._open_window.file
        if self._open_window.close_state == WindowCloseState.OK:
            utility.load_project(self.file, self.audio_files_tree)
        WindowManager.destroy_window(self._open_window.id)

    def ui_add_tree_category(self, *args):
        """Handle add category button event"""
        selected_node = self.audio_files_tree.selected_node

        if not selected_node:
            selected_node = self.audio_files_tree.root

        # now open the dialogue
        popup.show_text_input_popup(title='New Category', message='Enter Category Name', input_text='Category',
                                    yes_button_label='Create', no_button_label='Cancel', parent=self,
                                    callback=lambda x: self._add_tree_category(x.selection, selected_node, x.text))
        return

    def _add_tree_category(self, button, parent_node, text):
        if button == WindowCloseState.YES:
            Logger.trace('Adding %s node to %s', text, parent_node.id)
            # find if we have the node by text
            if parent_node.find_node(lambda x: x.ui.text == text, False):
                Logger.trace('Node by %s already exists', text)
                popup.show_ok_popup(
                    'New Category', message='Category \'%s\' already exists within \'%s\'' % (text, parent_node.id))
                return

            node = DraggableTreeViewNode(label=text)
            parent_node.add_node(node).open(True)

    def ui_file_tree_touch_up(self, tree, touch):
        """Handle file tree touch events - opens menu"""
        if touch.button == 'right':
            # create menu
            Logger.debug('Touch up from tree %s', tree.id)

            node = tree.get_node_at_pos(touch.pos)
            if node and node is not self.audio_files_tree.root:
                # construct menu
                m = Menu()
                m.bind(on_select=self.on_menu_press)

                m.add_menu_item(SimpleMenuItem(text="Rename '%s'" % node._label.text, data=('RENAME', node)))

                if node.is_leaf:
                    m.add_menu_item(
                        SimpleMenuItem(text="Delete sound '%s'" % node._label.text, data=('DELETE', node)))
                else:
                    m.add_menu_item(
                        SimpleMenuItem(text="Delete category '%s'" % node._label.text, data=('DELETE', node)))

                pos = node.to_window(touch.pos[0], touch.pos[1])  # need to translate to proper coordinates
                m.show(pos[0], pos[1], node)

    def on_menu_press(self, menu, item, pos):
        action, node = item.data

        if node:
            if action == 'RENAME':
                popup.show_text_input_popup(title='Rename Category', message='Enter New Category Name', input_text=node._label.text,
                                            yes_button_label='Rename', no_button_label='Cancel', parent=self,
                                            callback=lambda x: self._rename_tree_node(node.id, x.text))
            elif action == 'DELETE':
                self._delete_tree_node(node.id)

    def _rename_tree_node(self, node_id, text):
        node = self.audio_files_tree.find_node(lambda x: x.id == node_id)
        if node:
            node.label = text

    def _delete_tree_node(self, node_id):
        node = self.audio_files_tree.find_node(lambda x: x.id == node_id)

        if node:
            self.audio_files_tree.remove_node(node)
