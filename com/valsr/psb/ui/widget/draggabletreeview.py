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

    def add_node(self, node, parent=None):
        if self._root != None:  # allow adding different nodes during tree initialization
            if not isinstance(node, DraggableTreeViewNode):
                raise TreeViewException('The node must be a subclass of DraggableTreeViewNode')
        else:  # convert root nod to DraggabreTreeViewNode
            root_node = DraggableTreeViewNode(label='root', is_open=True, level=0)
            for key, value in self.root_options.items():
                setattr(root_node, key, value)
            node = root_node
            node.draggable = False

        # check if the parent has the node already
        if parent and parent.has_node(node.id):
            Logger.warning('Node %s already has node by id %s', parent.id, node.id)
            return parent.node(node.id)

        node = super().add_node(node, parent)

        for n in self.iterate_all_nodes(node):
            n._tree = self

        return node

    def remove_node(self, node):
        for n in self.iterate_all_nodes(node):
            n._tree = None

        super().remove_node(node)
        return node

    def remove_all_nodes(self):
        """Remove all nodes from the tree (will not remove root node)"""
        for n in self.root.nodes:
            self.remove_node(n)

    def find_node(self, cb):
        """Find node by given function

        Args:
            cb: Callback accepting a single argument (node) and returns Boolean value

        Returns:
            DraggableTrieViewNode or None
        """
        return self.root.find_node(cb, True)

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
        return node.data is None


class DraggableTreeViewNode(TreeViewNode, BoxLayout, Draggable):
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

    def add_node(self, node):
        """Add node to the tree

        Args:
            node: Node to add

        Returns:
            The added node
        """
        return self._tree.add_node(node, self)

    def remove_node_id(self, node_id):
        """Remove node by given id

        Args:
            node_id: Node identifier
        """
        node = self.node(node_id)
        if node:
            self._tree.remove_node(node)

    def node(self, node_id):
        """Get node by given identifier

        Args:
            node_id: Node identifier

        Returns:
            Found node or None
        """
        return self.find_node(lambda x: x.id == node_id, False)

    def has_node(self, node_id):
        """Check if given node exists in the tree

        Args:
            node_id: Node identifier

        Returns:
            Boolean
        """
        return self.node(node_id) is not None

    def find_node(self, cb, descend=False):
        """Use a callback to locate a node

        Args:
            cb: Callback accepting a single parameter (node) and returning Boolean value
            descend: Descend into child nodes as well

        Returns:
            Node or None
        """
        for node in self.nodes:
            if cb(node):
                return node
            elif descend:
                found = node.find_node(cb, descend)
                if found:
                    return found

        return None

    def open(self, open_parents=False):
        """Open node

        Args:
            open_parents: Whether to open all parent nodes as well
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
        self._label.text = args[1]

    def _drag_detach_parent(self):
        self._tree.remove_node(self)
        self._original_parent._do_layout()
