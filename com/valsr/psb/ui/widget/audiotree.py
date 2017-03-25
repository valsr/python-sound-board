"""
Created on Mar 3, 2017

@author: valsr <valsr@valsr.com>
"""
from com.valsr.psb.ui.widget.draggabletreeview import DraggableTreeViewNode, DraggableTreeView
from com.valsr.psb.sound.info import MediaInfo
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from com.valsr.psb.ui.window.manager import WindowManager
from kivy.uix.image import Image
from kivy.properties import ObjectProperty
from kivy.logger import Logger
from com.valsr.type.tree import find_by_id, find_by_property


class AudioTreeView(DraggableTreeView):

    audio_tree = ObjectProperty(allownone=True)

    def __init__(self, tree=None, **kwargs):
        self.audio_tree = tree
        super().__init__(**kwargs)

    def _drop_acceptable(self, node):
        if isinstance(node, AudioTreeViewNode):
            return not node.is_file()

        return False

    def _get_root_node(self):
        return AudioTreeViewNode(label="root", is_open=True, level=0)

    def synchronize_with_tree(self):
        if self.audio_tree:
            Logger.debug("Synchronizing node %s (root) to N/A(%s)", self.root.id, self.audio_tree.label)

            # update the node id for the root (if applicable)
            if self.root.id is not self.audio_tree.node_id:
                self.root.id = self.audio_tree.node_id

            # update nodes
            updated_child_list = []
            for child in self.audio_tree.nodes():
                updated_child_list.append(child.node_id)
                view_node = self.root.get_node(child.node_id)
                if view_node:
                    view_node.synchronize_node_with_tree(child)
                else:
                    # node does not exist so insert it at position
                    self.root.insert_node_at_position(child, self.audio_tree.node_index(child))

            # delete unused child nodes
            delete_nodes = []
            for child in self.root.nodes:
                if child.id not in updated_child_list:
                    delete_nodes.append(child.id)

            for id in delete_nodes:
                Logger.debug("Removing node %s", id)
                self.root.remove_nodes(find_by_id(id))
        else:
            Logger.debug("Removing all nodes")
            self.remove_all_nodes()


class AudioTreeViewNode(DraggableTreeViewNode):
    """Node in the DraggableTreeView used for audio files/categories"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._ui_layout = BoxLayout(orientation='horizontal', size_hint=(1, 1))
        self.set_ui(self._ui_layout)
        self._ui_layout.do_layout()

        image_size = WindowManager.theme_closest_smallest_size(
            WindowManager.theme_closest_smallest_size(self.height) - 1)

        image_source = "file-audio-o" if self.is_file() else "folder"
        self._ui_image = Image(source=WindowManager.theme_image_file(
            image_source, image_size), size=(image_size, image_size), size_hint=(None, 1))
        self._ui_layout.add_widget(self._ui_image)

        # make the label left handed and
        self._ui_label = Label(text=self.label)
        self._ui_label.shorten = True
        self._ui_label.max_lines = 1
        self._ui_label.halign = 'left'
        self._ui_label.texture_update()
        self._ui_label.shorten_from = 'right'
        self._ui_label.text_size[0] = self._ui_label.size[0]
        self._ui_label.width = self._ui_layout.width - image_size
        self._ui_layout.add_widget(self._ui_label)

    def do_layout(self, *largs):
        # adjust the label size
        self._ui_label.text_size[0] = self._ui_label.size[0]
        self._ui_label.width = self._ui_layout.width - self._ui_image.width
        return DraggableTreeViewNode.do_layout(self, *largs)

    def on_drag(self, draggable, touch):
        if self.is_file():
            # get the waveform and switch
            pass

    def is_file(self):
        if self._tree and self._tree.audio_tree:
            # find out if it has media
            audio_node = self._tree.audio_tree.find_node(find_by_property('node_id', self.id), descend=True)
            if audio_node:
                return audio_node.is_file()
        return False

    def insert_node_at_position(self, tree_node, position):
        Logger.debug("Inserting node %s (%s) at position %d",
                     tree_node.node_id, tree_node.label, position)
        node = self.add_node(AudioTreeViewNode(node_id=tree_node.node_id, label=tree_node.label))
        node.order_node(position)

        for child in tree_node.nodes():
            node.insert_node_at_position(child, tree_node.node_index(child))

    def update_tree_node(self, tree_node):
        if tree_node.has_data('label'):
            self.label = tree_node.label

        # update if three is a leaf or a branch
        if len(tree_node.nodes()) == 0:
            self.is_leaf = True
        else:
            self.is_leaf = False

        self.id = tree_node.node_id

    def on_add_to_tree(self):
        image_source = "file-audio-o" if self.is_file() else "folder"
        self._ui_image.source = WindowManager.theme_image_file(image_source, self._ui_image.width)
