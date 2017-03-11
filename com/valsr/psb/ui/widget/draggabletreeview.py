"""
Created on Feb 4, 2017

@author: valsr <valsr@valsr.com>
"""
import uuid
from kivy.logger import Logger
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.treeview import TreeView, TreeViewException, TreeViewNode

from com.valsr.psb.ui.widget.draggable import Draggable
from com.valsr.psb.ui.widget.droppable import Droppable
from com.valsr.type import tree


class TreeViewNodeInterface(tree.GenericTreeNodeInterface):
    """TreeViewNodeInterface. This provides the a custom implementation of the GenericTreeNodeInterface to account
    for the incomparability between TreeViewNode and GenericTreeView node interface."""

    def iterate_nodes(self, callback=tree.find_all(), descend=False, include_self=True):
        """Iterate over child nodes based on given function

        Args:
            callback: Function to determine whether to iterate over node or not (callback(n), return Boolean)
            descend: Whether to descend into child nodes as well
            include_self: Include self in the iteration

        Returns:
            yields DataTreeNode

        Notes:
            When iterating, it will descend to child nodes if the current node has any.
        """
        if include_self:
            if callback(self):
                yield self

        for n in self.nodes:
            if callback(n):
                yield n

            if descend:
                if len(n.nodes) > 0:
                    # we already did the child nodes here/at this level
                    yield from n.iterate_nodes(callback, descend, False)

    def detach(self):
        """Remove self from parent_node (if attached)

        Returns:
            self
        """
        if self.parent_node:
            self.parent_node.remove_node(self)

        return self


class DraggableTreeView(TreeView, Droppable):
    """Adds ability to drag individual items for kivy's TreeView"""

    draggable = BooleanProperty(True)
    """Drag enabled"""

    draggable_offset = NumericProperty(30)
    """How long of a distance (in pixels) to wait before starting drag"""
    # @TODO: Inherit draggable??? are these properties used at all???

    drop_acceptable_cb = ObjectProperty(None)
    """Drop callback to determine acceptability. Overwrite to provide custom callback."""

    def __init__(self, **kwargs):
        """Constructor"""
        super().__init__(**kwargs)
        self.drop_acceptable_cb = self._drop_acceptable

    def add_node(self, node, position=-1, parent_node=None):
        if self._root:  # allow adding different nodes during tree initialization
            if not isinstance(node, DraggableTreeViewNode):
                raise TreeViewException('The node must be a subclass of DraggableTreeViewNode')
        else:  # convert root nod to DraggabreTreeViewNode
            root_node = DraggableTreeViewNode(label='root', is_open=True, level=0)
            for key, value in self.root_options.items():
                setattr(root_node, key, value)
            node = root_node
            node.draggable = False

        # check if the parent_node has the node already
        if parent_node and parent_node.has_node(tree.find_by_id(node.id)):
            Logger.warning('Node %s already has node by id %s', parent_node.id, node.id)
            return parent_node.node(node.id)

        node = super().add_node(node, parent_node)
        self.order_node(node, position)

        for n in self.iterate_all_nodes(node):
            n._tree = self

        return node

    def order_node(self, node, position):
        if node.parent_node:
            nodes = node.parent_node.nodes

            # calculate position
            if position < 0:
                position = len(nodes) + position

            if position < 0:
                position = 0
            elif position >= len(nodes):
                position = len(nodes) - 1

            # get the node at position
            nodes.insert(position, nodes.pop(nodes.index(node)))

    def remove_node(self, node):
        for n in self.iterate_all_nodes(node):
            n._tree = None

        super().remove_node(node)
        return node

    def remove_all_nodes(self):
        """Remove all nodes from the tree (will not remove root node)"""
        for n in self.root.nodes:
            self.remove_node(n)

    def on_drop(self, draggable, touch):
        if isinstance(draggable, DraggableTreeViewNode):
            node = self.get_node_at_pos(self.to_widget(*touch.pos))
            if not node:
                node = self.root

            Logger.debug('Selected node %s', node._label.text)
            while not self.drop_acceptable_cb(node):
                node = node.parent_node

            Logger.debug('Adding %s to %s', draggable._label.text, node._label.text)
            # add before
            self.select_node(self.add_node(draggable, node))
            return True

        return False

    def on_hover(self, draggable, touch):
        node = self.get_node_at_pos(self.to_widget(*touch.pos))

        if not node:
            node = self.root

        # figure if we can drop here
        while not self.drop_acceptable_cb(node):
            node = node.parent_node

        self.select_node(node)
        return True

    def _drop_acceptable(self, node):
        return True


class DraggableTreeViewNode(TreeViewNode, BoxLayout, Draggable, TreeViewNodeInterface):
    """Node in the DraggableTreeView"""

    id = StringProperty(allownone=False)
    """Node identifier"""

    data = ObjectProperty(defaultvalue=None)
    """Data associated with this node"""

    _tree = ObjectProperty(defaultvalue=None, allownone=True)
    """Parent tree object"""

    ui = ObjectProperty(defaultvalue=None, allownone=True)
    """UI component to use as component"""

    label = StringProperty(defaultvalue=None, allownone=True)
    """String label for node"""

    def __init__(self, node_id=None, data=None, label=None, **kwargs):
        super().__init__(**kwargs)
        if not node_id:
            node_id = str(uuid.uuid1().hex)

        self.id = node_id
        self.data = data
        self.label = label

        # create a label for us
        self._label = Label(text=label)
        self._label.width = self.width
        self._label.shorten = True
        self._label.max_lines = 1
        self._label.shorten_from = 'right'
        self._label.texture_update()

        # add label to ui component
        self.ui = self._label
        self.add_widget(self.ui)

        # fix component height
        self.height = self._label.texture_size[1] + 16
        self._label.text_size = (self._label.texture_size[0], self._label.texture_size[1])

    def do_layout(self, *largs):
        # fix the alignment due to size not being calculated in the init method
        if self.ui is self._label:
            self._label.text_size[0] = self.width
        return BoxLayout.do_layout(self, *largs)

    def add_node(self, node, position=-1):
        """Add node to the tree

        Args:
            node: Node to add
            position: Position index to add to

        Returns:
            The added node
        """
        return self._tree.add_node(node=node, parent_node=self, position=position)

    def node_index(self, node):
        return self.nodes.index(node)

    def node_at(self, position):
        if position < 0:
            position = len(self.nodes) + position

        if position < 0 or position >= len(self.nodes):
            return None

        return self.nodes[position]

    def order_node(self, position):
        return self._tree.order_node(self, position)

    def remove_node(self, node):
        return self.remove_at(self.node_index(node))

    def remove_at(self, position):
        """Remove node at given position

        Args:
            position: The node index. If <0, then it will return the index as counted from the back (-1 being the last
                item)

        Returns:
            Removed node or None if index > child size
        """
        if position < 0:
            position = len(self.nodes) + position

        if position < 0 or position >= len(self.nodes):
            return None

        node = self.nodes[position]
        self._tree.remove_node(node)
        return node

    def clear_nodes(self):
        """Remove all child nodes

        Returns:
            self
        """
        for n in self.nodes:
            n._tree.remove_node(n)

        return self

    def clone(self, deep=False):
        """Performs a shallow clone of the data and nodes (new ids will be generated)

        Args:
            deep: Perform a deep copy instead

        Returns:
            DataTreeNode cloned node
        """
        raise NotImplementedError()

    def open(self, open_parents=False):
        """Open node

        Args:
            open_parents: Whether to open all parent_node nodes as well
        """
        if not self.is_leaf:
            if not self.is_open:
                self._tree.toggle_node(self)
            else:
                Logger.trace('Node %s: Already opened', self.id)
        else:
            Logger.trace('Node %s: is a leaf node', self.id)

        if open_parents and self.parent_node:
            Logger.debug('opening parents')
            self.parent_node.open(open_parents=True)

    def close(self):
        """Close node"""
        if not self.is_leaf:
            if self.is_open:
                self._tree.toggle_node(self)
            else:
                Logger.trace('Node %s: Already closed', self.id)
        else:
            Logger.trace('Node %s: is a leaf node', self.id)

    def toggle(self):
        """Toggle node open/close state"""
        self._tree.toggle_node(self)

    def on_label(self, *args):
        self.label = args[1]

    def _drag_detach_parent(self):
        self._tree.remove_node(self)
        self._original_parent._do_layout()


def synchronize_with_tree(draggable_tree, tree_node):
    draggable_node = draggable_tree.root
    Logger.debug("Synchronizing node %s (root) to N/A(%s)", draggable_node.id, tree_node.label)

    # update the node id for the root (if applicable)
    if draggable_node.id is not tree_node.node_id:
        draggable_node.id = tree_node.node_id

    # update nodes
    updated_child_list = []
    for child in tree_node.nodes():
        updated_child_list.append(child.node_id)
        node = draggable_node.get_node(child.node_id)
        if node:
            synchronize_node_with_tree(node, child)
        else:
            # node does not exist so insert it at position
            insert_tree_at_position(draggable_node, child, tree_node.node_index(child))

    # delete unused child nodes
    delete_nodes = []
    for child in draggable_node.nodes:
        if child.id not in updated_child_list:
            delete_nodes.append(child.id)

    for id in delete_nodes:
        Logger.debug("Removing node %s", id)
        draggable_node.remove_node_by_id(id)


def synchronize_node_with_tree(draggable_node, tree_node):
    Logger.debug("Synchronizing node %s (%s) to %s (%s)", draggable_node.id,
                 draggable_node.label, tree_node.node_id, tree_node.label)
    update_tree_node(draggable_node, tree_node)

    # update nodes
    updated_child_list = []
    for child in tree_node.nodes():
        updated_child_list.append(child.node_id)
        node = draggable_node.node(child.node_id)
        if node:
            synchronize_node_with_tree(node, child)
        else:
            # node does not exist so insert it at position
            insert_tree_at_position(draggable_node, child, tree_node.node_index(child))

    # delete unused child nodes
    delete_nodes = []
    for child in draggable_node.nodes:
        if child.id not in updated_child_list:
            delete_nodes.append(child.id)

    for id in delete_nodes:
        Logger.debug("Removing node %s", id)
        draggable_node.remove_node_by_id(id)


def insert_tree_at_position(parent_node, tree_node, position):
    Logger.debug("Inserting node (parent_node %s) %s (%s) at position %d",
                 parent_node.id, tree_node.node_id, tree_node.label, position)
    node = parent_node.add_node(DraggableTreeViewNode(node_id=tree_node.node_id, label=tree_node.label))
    node.order_node(position)

    for child in tree_node.nodes():
        insert_tree_at_position(node, child, tree_node.node_index(child))


def update_tree_node(draggable_node, tree_node):
    if tree_node.has_data('label'):
        draggable_node.label = tree_node.label

    # update if three is a leaf or a branch
    if len(tree_node.nodes()) == 0:
        draggable_node.is_leaf = True
    else:
        draggable_node.is_leaf = False

    draggable_node.id = tree_node.node_id
