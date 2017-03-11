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
from com.valsr.psb.ui.dialogue import popup, addsound
from com.valsr.psb.ui.dialogue.addsound import AddSoundDialogue
from com.valsr.psb.ui.dialogue.open import OpenDialogue
from com.valsr.psb.ui.dialogue.save import SaveDialogue
from com.valsr.psb.ui.menu import SimpleMenuItem, Menu
from com.valsr.psb.ui.widget.draggabletreeview import DraggableTreeView, DraggableTreeViewNode
from com.valsr.psb.ui.widget.lane import LaneWidget
from com.valsr.psb.ui.window.base import WindowBase, WindowCloseState
from com.valsr.psb.ui.window.manager import WindowManager
from com.valsr.psb.utility import MainTreeMenuActions
from com.valsr.psb.ui.widget.audiotree import AudioTreeViewNode
from com.valsr.psb.project import PSBProject
from com.valsr.psb.ui.widget import draggabletreeview
from com.valsr.type.nodes import AudioFileNode


class MainWindow(WindowBase):
    """Main PSB window"""

    POPUP_WINDOW_ID = "_MAIN_WINDOW_POPUP"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.audio_files_tree = None

    def create_root_ui(self):
        return Builder.load_file("ui/kv/main.kv")

    def on_create(self):
        project = PSBProject()
        project.load_project('test.psb')
        PSBProject.project = project
        self.audio_files_tree = self.get_ui('audio_files')
        self.audio_files_tree.bind(on_touch_up=self.ui_file_tree_touch_up)
        self._update_audio_tree()

    def _update_audio_tree(self):
        PSBProject.project.audio_files._dump_node(logger=Logger.debug)
        draggabletreeview.synchronize_with_tree(self.audio_files_tree, PSBProject.project.audio_files)

    #
    # UI Handling
    #
    def on_add_sound(self, *args):
        """Handle add sound button event"""
        if not WindowManager.window(MainWindow.POPUP_WINDOW_ID):
            window = WindowManager.create_window(AddSoundDialogue, parent=self, window_id=MainWindow.POPUP_WINDOW_ID,
                                                 create_opts={"windowed": True, "size_hint": (0.75, 0.75)})
            window.bind(on_dismiss=self._add_sound_dismiss)
            window.open()
        else:
            Logger.debug("Main popup window is open...")

    def on_save_project(self, *args):
        """Handle save button event"""
        if not PSBProject.project.file:
            return self.on_save_as_project(*args)
        else:
            self._save_project()

    def on_save_as_project(self, *args):
        """Handle save as button event"""
        if not WindowManager.window(MainWindow.POPUP_WINDOW_ID):
            window = WindowManager.create_window(SaveDialogue, parent=None, window_id=MainWindow.POPUP_WINDOW_ID,
                                                 create_opts={'windowed': True, 'size_hint': (0.75, 0.75)})
            window.bind(on_dismiss=lambda x: self._save_project(from_dialogue=True))
            window.open()
        else:
            Logger.debug("Main popup window is open...")

    def on_open_project(self, *args):
        """Handle open button event"""
        if not WindowManager.window(MainWindow.POPUP_WINDOW_ID):
            window = WindowManager.create_window(OpenDialogue, parent=None, window_id=MainWindow.POPUP_WINDOW_ID,
                                                 create_opts={'windowed': True, 'size_hint': (0.75, 0.75)})
            window.bind(on_dismiss=self._open_project)
            window.open()
        else:
            Logger.debug("Main popup window is open...")

    def on_add_category(self, *args):
        """Handle add category button event"""
        selected_node = self.audio_files_tree.selected_node

        if not selected_node:
            selected_node = self.audio_files_tree.root

        # now open the dialogue
        popup.show_text_input_popup(title='New Category', message='Enter Category Name', input_text='Category',
                                    yes_button_label='Create', no_button_label='Cancel', parent=self,
                                    callback=lambda x: self._add_category(x.selection, selected_node.id, x.text))

    # TODO:
    def ui_file_tree_touch_up(self, tree, touch):
        """Handle file tree touch events - opens menu"""
        pos = tree.to_window(touch.pos[0], touch.pos[1], relative=True)

        if tree.collide_point(*pos):
            if touch.button == 'right':
                # create menu
                Logger.debug('Touch up from tree %s', tree.id)

                node = tree.get_node_at_pos(touch.pos)
                if node and node is not self.audio_files_tree.root:
                    # construct menu
                    m = self._create_files_menu(node.id)
                    pos = node.to_window(touch.pos[0], touch.pos[1])  # need to translate to proper coordinates
                    m.show(pos[0], pos[1], node)

    # TODO:
    def ui_add_lane(self, position='bottom'):
        ui_lanes = self.get_ui('lanes')

        lane = LaneWidget()
        ui_lanes.add_widget(lane)

    # TODO:
    def on_menu_press(self, menu, item, pos):
        action, node = item.data

        if node:
            if action == MainTreeMenuActions.RENAME:
                popup.show_text_input_popup(title='Rename Category', message='Enter New Category Name', input_text=node._label.text,
                                            yes_button_label='Rename', no_button_label='Cancel', parent=self,
                                            callback=lambda x: self._rename_tree_node(node.id, x.text))
            elif action == MainTreeMenuActions.DELETE:
                self._delete_tree_node(node.id)
    #
    # MENU
    #

    def _create_files_menu(self, node_id):
        menu = Menu()
        menu.bind(on_select=self.on_menu_press)

        node = PSBProject.project.audio_files.get_node(node_id, decend=True)

        menu.add_menu_item(
            SimpleMenuItem(text="Rename '%s'" % node.label, data=(MainTreeMenuActions.RENAME, node_id)))

        if node.is_leaf:
            menu.add_menu_item(
                SimpleMenuItem(text="Delete sound '%s'" % node.label, data=(MainTreeMenuActions.DELETE, node_id)))
        else:
            menu.add_menu_item(
                SimpleMenuItem(text="Delete category '%s'" % node.label, data=(MainTreeMenuActions.DELETE, node_id)))

        return menu

    def _add_sound_dismiss(self, *args):
        """Handle dismissal of the add sound dialogue"""
        window = WindowManager.window(MainWindow.POPUP_WINDOW_ID)
        if window and window.close_state == WindowCloseState.OK and window.file:
            self._add_audio_file(window.file)

        WindowManager.destroy_window(MainWindow.POPUP_WINDOW_ID)

    def _add_audio_file(self, file):
        # check the fingerprint and see if we already have it
        info = MediaInfoManager.get_media_info(file, reload_on_error=True)
        if not info:
            Clock.schedule_once(lambda x: self._add_audio_file(file), 0.1)
            return

        tree = PSBProject.project.audio_files
        if tree.has_node(lambda x: x.has_data('data') and x.data.fingerprint == info.fingerprint):
            popup.show_ok_popup(
                'File Already Added', 'File by similar fingerprint has already been added', parent=self)
            return

        Logger.debug("Adding to %s to collection", file)

        parent = tree.find_node(lambda x: x.label.lower() == 'uncategorized', False)
        if not parent:
            parent = tree.add_node(AudioFileNode(label="Uncategorized"))

        parent.add_node(AudioFileNode(label=os.path.basename(file), data=info))
        self._update_audio_tree()

    def _save_project(self, from_dialogue=False):
        if from_dialogue:
            window = WindowManager.window(MainWindow.POPUP_WINDOW_ID)
            if window.close_state != WindowCloseState.OK:
                WindowManager.destroy_window(MainWindow.POPUP_WINDOW_ID)
                return
            file = window.file
            WindowManager.destroy_window(MainWindow.POPUP_WINDOW_ID)
        else:
            file = PSBProject.project.file

        PSBProject.project.save_project(file)
        self.title = "PSB: " + file

    def _open_project(self, *args):
        window = WindowManager.window(MainWindow.POPUP_WINDOW_ID)
        if self._open_window.close_state == WindowCloseState.OK:
            PSBProject.load_project(self, window.file)
        WindowManager.destroy_window(self._open_window.id)

    def _add_category(self, button, parent_id, text):
        if button == WindowCloseState.YES:
            # find if we have the node by text
            tree = PSBProject.project.audio_files
            parent_node = tree.find_node(lambda x: x.node_id == parent_id, True)
            Logger.trace('Adding %s node to %s', text, parent_node.label)

            if parent_node.has_node(lambda x: x.label == text, include_self=False):
                Logger.trace('Node by %s already exists', text)
                popup.show_ok_popup(
                    'New Category', message='Category \'%s\' already exists within \'%s\'' % (text, parent_node.label))
                return

            node = AudioFileNode(label=text)
            parent_node.add_node(node)
            self._update_audio_tree()

            # open the node
            # TODO: Open the new node

    def _rename_tree_node(self, node_id, text):
        node = self.audio_files_tree.find_nodes(lambda x: x.id == node_id)
        if node:
            node.label = text

    def _delete_tree_node(self, node_id):
        node = self.audio_files_tree.find_nodes(lambda x: x.id == node_id)

        if node:
            self.audio_files_tree.remove_node(node)
