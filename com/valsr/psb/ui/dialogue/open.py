"""
Created on Jan 14, 2017

@author: valsr <valsr@valsr.com>
"""
import os
from kivy.lang import Builder

from com.valsr.psb.ui.dialogue import popup
from com.valsr.psb.ui.window.base import WindowBase, WindowCloseState


class OpenDialogue(WindowBase):
    """Open project dialogue"""

    def __init__(self, **kwargs):
        WindowBase.__init__(self, **kwargs)
        self.title = "Open Project"
        self.cwd = os.getcwd()
        self.file = None

    def on_open(self, **kwargs):
        """Perform post open configuration"""
        self.get_ui('Files').path = self.cwd
        self.get_ui('PathInput').text = self.cwd
        self.get_ui('Files').filters.append(self.project_file_filter)

    def create_root_ui(self):
        return Builder.load_file("ui/kv/open.kv")

    def ui_cancel(self, *args):
        """Handle cancel button action"""
        self.close_state = WindowCloseState.CANCEL
        self.dismiss()

    def ui_open(self, *args):
        """Handle open button action"""
        file_name = self.get_ui('FileName').text

        self.file = os.path.join(self.get_ui('Files').path, file_name)

        if not os.path.exists(self.file):
            popup.show_ok_popup(
                title='File Does Not Exists', message='File %s does not exist. Select an existing file. ' % file_name, )
            return

        self.close_state = WindowCloseState.OK
        self.dismiss()

    def project_file_filter(self, folder, file):
        """File view filter for project files"""
        if os.path.isdir(file):
            return True

        if self.get_ui('PathInput').text is not folder:
            self.get_ui('PathInput').text = folder
        ext = os.path.splitext(file)[1]
        return ext.lower() == '.psb'

    def ui_file_selection(self, *args):
        """Handle file selection in file view"""
        files = self.get_ui('Files')

        if files.selection:
            file = files.selection[0]

            self.get_ui('FileName').text = os.path.basename(file)

        return True
