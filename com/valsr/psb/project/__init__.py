"""
Created on Mar 3, 2017

@author: valsr <valsr@valsr.com>
"""
from com.valsr.type.tree import GenericTreeNode
from kivy.logger import Logger

from com.valsr.psb.sound.info import MediaInfo
from com.valsr.psb.project.file import SaveFile
from com.valsr.psb.project import file


class PSBProject(object):
    """Project Data object

    The project contains two trees - files and lanes. Files represent the added music files to the project and have
    the following structure:
        node:
            label: string
            info: media information (none if this is a category instead), obtained from MediaInfo class
            node_id: internal node identifier (different from node)

    Lanes represent the lanes of music files added to the project.
    """

    project = None
    """Current open/loaded project"""

    def __init__(self):
        """Constructor"""
        self._audio_tree = GenericTreeNode(label='files')
        self._lanes = GenericTreeNode(label='lanes')
        self._file = None

    def load_project(self, path):
        """Load project file from given path

        Args:
            path: Path to file to load
        """
        savefile = file.load_project(path)
        # clear previous information
        self._audio_tree.clear_nodes()
        self._audio_tree.clear_data()
        self._audio_tree.label = 'files'

        self._lanes.clear_nodes()
        self._lanes.clear_data()
        self._lanes.label = 'lanes'

        self._file = savefile
        self._audio_tree = savefile.audio_tree.clone(deep=True)
        self._lanes = savefile.lanes.clone(deep=True)

    def save_project(self, path):
        Logger.info('Saving project to %s', path)

        savefile = SaveFile()
        savefile.audio_tree = self._audio_tree.clone(deep=True)
        savefile.lanes = self._lanes.clone(deep=True)
        savefile.file = path
        file.save_project(savefile)

    @property
    def audio_files(self):
        return self._audio_tree

    @property
    def file(self):
        return self._file

    @property
    def lanes(self):
        return self._lanes

    def dump(self):
        print("PSBProject")
        print("File: %s" % self._file)
        self._audio_tree._dump_node(logger=print, indent="  ", data_indent="-")
        self._lanes._dump_node(logger=print, indent="  ", data_indent="-")
