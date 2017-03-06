"""
Created on Jan 17, 2017

@author: valsr <valsr@valsr.com>
"""
import uuid
from kivy.logger import Logger
from kivy.uix.treeview import TreeViewLabel, TreeView, TreeViewNode

from com.valsr.psb.callback import CallbackRegister
from com.valsr.psb.sound.info import MediaInfo


class GenericTreeNode(TreeViewLabel, CallbackRegister):
    """Node structure. Provides enhancements to kivy's TreeViewLabel to make it easier to work with."""

    def __init__(self, tree, label=None, data=None, **kwargs):
        """Constructor

        Args:
            tree: Parent tree for this node
            label: Label for the node
            data: Data
            kwargs: Named parameters to pass to super classes
        """
        self.node_id = int(uuid.uuid1())
        self.data = data
        self.tree = tree
        super().__init__(text=label if label else node_id, **kwargs)

    def serialize(self):
        """Serialize the node and child nodes to a dictionary.

        Returns:
            Dictionary of serialized data

        Note:
            data argument must have a serialize method
        """
        data_dict = {}
        data_dict['id'] = self.node_id
        data_dict['label'] = self.text
        data_dict['data'] = self.data.serialize() if self.data else None
        data_dict['children'] = [x.serialize() for x in self.nodes]

        return data_dict

    def deserialize(self, tree, data_dict):
        """Deserialize node data. Will deserialize child nodes as well.

        Args:
            tree: Tree to attach node to
            data_dict: Dictionary with data

        Note:
            Currently data is deserialized as MediaInfo object
        """
        self.node_id = data_dict['id']
        self.text = data_dict['label']
        self.data = MediaInfo.deserialize(data_dict['data'])
        self.tree = tree

        for child in data_dict['children']:
            node = GenericTreeNode(id=child["id"], tree=None)
            node.deserialize(tree, child)
            self.add_child(node)

    def has_child(self, node_id):
        """Check if a child by given id exists

        Args:
            node_id: Node identifier

        Returns:
            Boolean
        """
        for node in self.nodes:
            if node.node_id == node_id:
                return True

        return False

    def child(self, node_id):
        """Obtain child by given node identifier

        Args:
            node_id: Node identifier

        Returns:
            GenericTreeNode or None
        """
        for node in self.nodes:
            if node.node_id == node_id:
                return node

        return None

    def add_child(self, child):
        """Add child to this node

        Args:
            child: Child node

        Returns:
            GenericTreeNode: The added node, or
            None
        """
        if not self.has_child(child.node_id):
            self.tree.add_node(child, self)
            return child

        return None

    def detach(self):
        """Detach self from the tree.

        Returns:
            self
        """
        if self.tree:
            self.tree.remove_node(self)
        return self

    def remove_child(self, node_id):
        """Remove child node by given id

        Args:
            node_id: Child node identifier

        Returns:
            self
        """
        node = self.child(node_id)

        if node:
            node.detach()

        return self

    def remove_children(self):
        """Remove/detach all child nodes

        Returns:
            self
        """
        for child in self.nodes:
            child.detach()

        return self

    def open_parents(self):
        """Open all parent nodes up to the root

        Returns:
            self
        """
        if self.parent_node:
            if not self.parent_node.is_open:
                self.tree.toggle_node(self.parent_node)
            if isinstance(self.parent_node, GenericTreeNode):
                self.parent_node.open_parents()
        return self

    def find_node_by_fingerprint(self, fingerprint):
        """Find node by given MediaInfo fingerprint

        Args:
            fingerprint: Fingerprint identifier

        Returns:
            GenericTreeNode: Found node, or
            None
        """
        if self.data:
            if self.data.fingerprint == fingerprint:
                return self

        for child in self.nodes:
            found = child.find_node_by_fingerprint(fingerprint)
            if found:
                return found

        return None

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.call('touch_down', None, True, self, touch):
                return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            pass

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            if self.call('touch_up', None, True, self, touch):
                return True

    def attach_to(self, tree):
        """Attach node to tree

        Args:
            tree: Tree to attach to
        """

        if self.tree is not tree:
            if self.tree:
                self.detach()

            self.tree = tree
            tree.add_node(self)

    def walk(self):
        yield self, self.nodes

        for node in self.nodes:
            yield from node.walk()
