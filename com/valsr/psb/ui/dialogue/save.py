"""
Created on Jan 14, 2017

@author: valsr <valsr@valsr.com>
"""
import os
from kivy.lang import Builder

from com.valsr.psb.ui.dialogue import popup
from com.valsr.psb.ui.window.base import WindowBase, WindowCloseState


class SaveDialogue(WindowBase):
    """Save project dialogue"""

    def __init__(self, **kwargs):
        WindowBase.__init__(self, **kwargs)
        self.title = "Save Project"
        self.cwd = os.getcwd()
        self.file = None

    def on_open(self, **kwargs):
        """Perform post open configuration"""
        self.get_ui('Files').path = self.cwd
        self.get_ui('PathInput').text = self.cwd
        self.get_ui('Files').filters.append(self.ui_filter_files)

    def create_root_ui(self):
        return Builder.load_file("ui/kv/save.kv")

    def ui_cancel(self, *args):
        """Handle cancel button action"""
        self.close_state = WindowCloseState.CANCEL
        self.dismiss()

    def ui_save(self, *args):
        """Handle save button action"""
        file_name = self.get_ui('FileName').text

        if not file_name:
            popup.show_ok_popup(title='Enter name', message='Enter a valid project name', button='Ok')
            return

        if file_name and not file_name.lower().endswith('.psb'):
            file_name += '.psb'

        self.file = os.path.join(self.get_ui('Files').path, file_name)

        if os.path.exists(self.file):
            popup.show_yes_no_popup(title='File Exists', message='Fire %s exists. Overwrite file? ' % file_name,
                                 yes_button_label='Overwrite', no_button_label='Cancel',
                                 callback=self._save_overwrite_callback)
            return

        self.close_state = WindowCloseState.OK
        self.dismiss()

    def _save_overwrite_callback(self, popup):
        """Callback to handle save overwrite action

        Args:
            popup: Overwrite popup
        """
        if popup.selection == WindowCloseState.YES:
            self.close_state = WindowCloseState.OK
            self.dismiss()

    def ui_filter_files(self, folder, file):
        """Filter used to filter only project files

        Args:
            folder: Current folder to filter
            file: Current file (in folder) to apply filter

        Returns:
            Boolean to filter file in (True) or out (False)
        """
        if os.path.isdir(file):
            return True

        if self.get_ui('PathInput').text is not folder:
            self.get_ui('PathInput').text = folder
        ext = os.path.splitext(file)[1]
        return ext.lower() == '.psb'

    def on_file_selection(self, *args):
        """Handle selecting files in file view"""
        files = self.get_ui('Files')

        if files.selection:
            file = files.selection[0]

            self.get_ui('FileName').text = os.path.basename(file)

        return True
