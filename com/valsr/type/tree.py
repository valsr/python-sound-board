"""
Created on Mar 3, 2017

@author: valsr <valsr@valsr.com>
"""
import uuid
import copy


class GenericTreeNode(object):
    """A generic tree node/tree structure with ability to store custom data"""

    def __init__(self, **kwargs):
        """Constructor"""
        self._data = {}
        self._parent = None
        self._children = []
        self._id = str(uuid.uuid1())

        for k in kwargs:
            self.__setattr__(k, kwargs[k])

    @property
    def id(self):
        """Node identifier - unique per session (program run)"""
        return self._id

    def __getattr__(self, name):
        if name is "_data":  # we forgot to init _data variable
            self._data = {}
            return self._data

        if name in self._data:
            return self._data[name]

        raise AttributeError("No attribute '%s' defined" % name)

    def __setattr__(self, name, value):
        if name.startswith("_") or name is "id":
            return super().__setattr__(name, value)

        self._data[name] = value

    def has_data(self, name):
        """Check if given data attribute exists in the node

        Args:
            name: name

        Returns:
            Boolean
        """
        return name in self._data

    def get_data(self):
        """Get all data attributes"""
        return self._data

    def set_data(self, value):
        """Set data attributes

        Args:
            value: Must be a dict or None

        Raises:
            TypeError: If value is neither dict nor None
        """
        if value:
            if isinstance(value, dict):
                self._data = value
            else:
                raise TypeError("value must be a dictionary or None")
        else:
            self.clear_data()

    def clear_data(self):
        """Clear data dictionary"""
        self._data = {}

    def add_node(self, node, position=-1):
        """Add node at given position

        Args:
            node: Node to add
            position: Position to add the node at. If >=0, then the node will be inserted before at the position index
                (or end if greater than the child node list). If < 0 then it will be inserted from the back at given
                position (-1 being last, -2 second last..)

        Returns:
            self

        Raises:
            TypeError: If node is not instance of GenericTreeNode
            RuntimeError: If node is - self, already added, detected a recursive node addition
        """
        self._validate_node_add(node)

        if position < 0:
            position = len(self._children) + 1 + position  # +1 since negative is adding after

        if position < 0:
            position = 0

        self._children.insert(position, node)
        node._parent = self

        return self

    def _validate_node_add(self, node):
        if not isinstance(node, GenericTreeNode):
            raise TypeError("Node must be an instance of GenericTreeNode")

        if node is self:
            raise RuntimeError("Can't add self as a child node")

        if node.parent() or node in self._children:
            raise RuntimeError("Node already attached to %s" % node.parent())

        _top = self
        while _top.parent():
            _top = _top.parent()

        if _top is node:
            raise RuntimeError("Detected recursive addition of node")

    def add_at(self, node, position):
        """Equivalent to add_node"""
        return self.add_node(node, position)

    def node_index(self, node):
        """Return the index of given node"""
        return self._children.index(node)

    def iterate_nodes(self, cb=lambda n: True, descend=False):
        """Iterate over child nodes based on given function

        Args:
            cb: Function to determine whether to iterate over node or not (cb(n), return Boolean)
            descend: Whether to descend into child nodes as well

        Returns:
            yields GenericTreeNode

        Notes:
            When iterating, it will descend to child nodes if the current node has any.
        """
        for n in self._children:
            if cb(n):
                yield n

            if descend:
                if len(n.children()) > 0:
                    yield from n.find_nodes(cb, descend)

    def find_nodes(self, cb, descend=False):
        """Return a list of nodes that match based on given function (it actualizes the iterate_nodes function)

        Args:
            cb: Function to determine whether to iterate over node or not (cb(n), return Boolean)
            descend: Whether to descend into child nodes as well

        Returns:
            []
        """

        return [x for x in self.iterate_nodes(cb, descend)]

    def has_node(self, cb, descend=False):
        """Return if given call back returns at least one matched node. This method is faster than find_nodes as it
        stops after/return the first found node.

        Args:
            cb: Function to determine whether to iterate over node or not (cb(n), return Boolean)
            descend: Whether to descend into child nodes as well

        Returns:
            Boolean
        """

        try:
            next(self.iterate_nodes(cb, descend))
            return True
        except StopIteration:
            return False

    def get_node(self, node_id, descend=False):
        """Obtain the node by given node_id

        Args:
            node_id: Node node_id
            descend: Whether to descend into child nodes as well

        Returns:
            GenericTreeNode or None
        """
        nodes = self.find_nodes(lambda n: n.id == node_id, descend)
        if nodes:
            return nodes[0]
        else:
            return None

    def node_at(self, position=0):
        """Obtain node at given position

        Args:
            position: The node index. If <0, then it will return the index as counted from the back (-1 being the last
                item)

        Returns:
            GenericTreeNode or None if index > node's child list
        """
        if position < 0:
            position = len(self._children) + position

        if position < 0 or position >= len(self._children):
            return None

        return self._children[position]

    def remove_node(self, node):
        """Remove given node

        Args:
            node: Node to remove

        Returns:
            self

        Note:
            Scans only immediate nodes (does not scan for children's children nodes). For that use remove_node_by_id
        """
        if node in self._children:
            self._children.remove(node)
            node._parent = None

        return self

    def remove_at(self, position=-1):
        """Remove node at given position

        Args:
            position: The node index. If <0, then it will return the index as counted from the back (-1 being the last
                item)

        Returns:
            Removed node or None if index > child size
        """
        if position < 0:
            position = len(self._children) + position

        if position < 0 or position >= len(self._children):
            return None

        return self._children.pop(position)

    def remove_node_by_id(self, node_id, descend=False):
        """Remove node by given node_id

        Args:
            node_id: Node node_id to remove
            descend: Whether to scan children's children

        Returns:
            Removed node or None
        """
        n = self.get_node(node_id, descend)

        if n:
            n.detach()

        return n

    def clear_nodes(self):
        """Remove all child nodes

        Returns:
            self
        """
        for n in self._children:
            n._parent = None

        self._children = {}
        return self

    def children(self):
        """Obtain child list

        Returns:
            List of GenericTreeNode

        Note:
            Will always return a list, empty if no node has no children
        """
        return self._children

    def parent(self):
        """Obtain parent node

        Returns:
            GenericTreeNode or None
        """
        return self._parent

    def detach(self):
        """Remove self from parent (if attached)

        Returns:
            self
        """
        if self._parent:
            self._parent.remove_node(self)

        return self

    def clone(self, deep=False):
        """Performs a shallow clone of the data and children (new ids will be generated)

        Args:
            deep: Perform a deep copy instead

        Returns:
            GenericTreeNode cloned node
        """
        node = GenericTreeNode()

        data = self.get_data()
        node.set_data(copy.copy(data) if not deep else copy.deepcopy(data))

        for child in self.children():
            child_node = child.clone()
            node.add_node(child_node)

        return node

    def _dump_node(self, logger=print, indent=" ", data_indent=" ", level=0):
        logger("%sNode: %s" % (indent * level, self.id))

        # dump properties
        data = self.get_data()
        if len(data) > 0:
            logger("%s%s%s" % (indent * level, data_indent, "Data:"))
            for v in data:
                logger("%s%s%s:%s" % (indent * level, data_indent, v, str(data[v])))

        children = self.children()
        if len(children) > 0:
            logger("%s%s%s" % (indent * level, data_indent, "Children:"))
            for c in children:
                c._dump_node(logger=logger, indent=indent, data_indent=data_indent, level=level + 1)
