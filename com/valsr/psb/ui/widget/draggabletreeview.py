"""
Created on Feb 4, 2017

@author: valsr <valsr@valsr.com>
"""
import uuid
from kivy.logger import Logger
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty, NumericProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.treeview import TreeView, TreeViewException, TreeViewNode

from com.valsr.psb.ui.widget.draggable import Draggable
from com.valsr.psb.ui.widget.droppable import Droppable
from com.valsr.type import tree
from com.valsr.type.tree import find_by_id
from kivy.clock import Clock


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
    # TODO: On drag highlight between spots
    """Adds ability to drag individual items for kivy's TreeView"""

    draggable = BooleanProperty(True)
    """Drag enabled"""

    drop_acceptable_cb = ObjectProperty(None)
    """Drop callback to determine acceptability. Overwrite to provide custom callback."""

    def __init__(self, drop_callback=None, **kwargs):
        """Constructor"""
        super().__init__(**kwargs)
        if not drop_callback:
            self.drop_acceptable_cb = self._drop_acceptable
        else:
            self.drop_acceptable_cb = drop_callback
        self.__last_hover_node = None
        self.__last_hover_clock = None
        self.__last_hover_pos = None

    def add_node(self, node, position=-1, parent_node=None):
        if self._root:  # allow adding different nodes during tree initialization
            if not isinstance(node, DraggableTreeViewNode):
                raise TreeViewException('The node must be a subclass of DraggableTreeViewNode')
        else:  # convert root nod to DraggabreTreeViewNode
            root_node = self._get_root_node()
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

        node.on_add_to_tree()
        return node

    def _get_root_node(self):
        return DraggableTreeViewNode(label='root', is_open=True, level=0)

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
        node.on_remove_from_tree(self)
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
            self.select_node(self.add_node(node=draggable, parent_node=node))
            return True

        return False

    def on_hover(self, draggable, touch):
        node = self.get_node_at_pos(self.to_widget(*touch.pos))

        if not node:
            node = self.root

        self._check_hover_unschedule(touch.pos)

        if self.__last_hover_node is not node:
            Logger.debug("Schedule to expand node %s", node.label)
            self.__last_hover_node = node
            self.__last_hover_clock = Clock.schedule_once(self._expand_on_hover, 1.5)
            self.__last_hover_pos = touch.pos

        # figure if we can drop here
        while not self.drop_acceptable_cb(node):
            node = node.parent_node

        self.select_node(node)
        return True

    def on_hover_out(self, draggable, touch):
        if self.__last_hover_clock:
            self._clear_on_hover_expand()

    def _check_hover_unschedule(self, pos):
        if self.__last_hover_pos:
            distance = pow(pos[0] - self.__last_hover_pos[0], 2) + pow(pos[1] - self.__last_hover_pos[1], 2)
            if distance > 25:
                self._clear_on_hover_expand()

    def _drop_acceptable(self, node):
        return True

    def _expand_on_hover(self, *args):
        if self.__last_hover_node:
            self.__last_hover_node.open()

    def _clear_on_hover_expand(self):
        Clock.unschedule(self.__last_hover_clock)
        self.__last_hover_node = None


class DraggableTreeViewNode(TreeViewNode, BoxLayout, Draggable, TreeViewNodeInterface):
    """Node in the DraggableTreeView"""

    id = StringProperty(allownone=False)
    """Node identifier"""

    _tree = ObjectProperty(defaultvalue=None, allownone=True)
    """Parent tree object"""

    ui = ObjectProperty(defaultvalue=None, allownone=True)
    """UI component to use as component"""

    label = StringProperty(defaultvalue=None, allownone=True)
    """String label for node"""

    drag_selected_color = ListProperty([.5, .5, .5, 1.0])
    """Drag background colour"""

    def __init__(self, node_id=None, label=None, **kwargs):
        super().__init__(**kwargs)
        if not node_id:
            node_id = str(uuid.uuid1().hex)

        self.id = node_id

        self._selected_selected = self.color_selected

        # create a label for us
        self._label = Label(text=label)
        self._label.width = self.width
        self._label.shorten = True
        self._label.max_lines = 1
        self._label.shorten_from = 'right'
        self._label.texture_update()

        self.label = label

        # add label to ui component
        self.set_ui(self._label)

        # fix component height
        self.height = self._label.texture_size[1] + 16
        self._label.text_size = (self._label.texture_size[0], self._label.texture_size[1])

    def set_ui(self, ui):
        if self.ui:
            self.remove_widget(self.ui)

        self.ui = ui
        self.add_widget(self.ui)

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
        self._label.text = args[1]

    def drag_detach(self):
        self._tree.remove_node(self)
        self._drag_parent._do_layout()

        # switch the ui
        return self

    def on_drag_select(self, draggable, touch):
        # modify drag color
        self._selected_selected = self.color_selected
        self.color_selected = self.drag_selected_color
        self._trigger_layout

    def on_drag_release(self, draggable, touch):
        # modify drag color
        self.color_selected = self._selected_selected
        self._trigger_layout

    def on_add_to_tree(self):
        pass

    def on_remove_from_tree(self, tree):
        pass
