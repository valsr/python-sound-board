"""
Created on Mar 3, 2017

@author: valsr <valsr@valsr.com>
"""
import uuid
import copy


class GenericTreeNodeSearcher():
    """Class used for creating searchers through GenericTreeNode. In stores search parameters and delegates the call/
    searching.

    Use:
        searcher = GenericTreeNodeSearcher(func, .....)
        tree.find_nodes(searcher,...)
    """

    def __init__(self, f, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._f = f

    def __call__(self, node):
        return self._f(node, *self._args, **self._kwargs)


def find_by_id(id):
    """Search by id

    Args:
        id: Node identifier

    Returns:
        GenericTreeNodeSearcher
    """
    def _find(node, id):
        return node.id == id
    return GenericTreeNodeSearcher(_find, id)


def find_by_property(name, value):
    """Search by property name and value

    Args:
        name: Property name
        value: Property value

    Returns:
        GenericTreeNodeSearcher
    """
    def _find(node, name, value):
        if hasattr(node, name):
            return node.__getattr__(property) == value
        return False
    return GenericTreeNodeSearcher(_find, name, value)


def find_all():
    """Generic node iterator/searcher"""
    def _find(node):
        return True
    return GenericTreeNodeSearcher(_find)


class GenericTreeNodeInterface(object):
    """GenericTreeNodeInterface. This provides the a basic implementation of a tree-node interface provided the
    implementing class provides implementation to few methods:
        add_node (at position)
        node_index (get index for node)
        node_at (get node at given position)
        remove_at (remove position)
        clear_nodes (clear all nodes, technically we could iterate over the nodes nodes)
        nodes (obtain child node list)
        parent_node (obtain parent_node node if any)
        clone (obtain a clone of self and nodes nodes)"""

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
            TypeError: If node is not instance of DataTreeNode
            RuntimeError: If node is - self, already added, detected a recursive node addition
        """
        raise NotImplementedError()

    def add_at(self, node, position):
        """Equivalent to add_node"""
        return self.add_node(node, position)

    def node_index(self, node):
        """Return the index of given node"""
        raise NotImplementedError()

    def iterate_nodes(self, callback=find_all(), descend=False, include_self=True):
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

        for n in self.nodes():
            if callback(n):
                yield n

            if descend:
                if len(n.nodes()) > 0:
                    # we already did the child nodes here/at this level
                    yield from n.iterate_nodes(callback, descend, False)

    def find_nodes(self, callback, descend=False, include_self=True):
        """Return a list of nodes that match based on given function (it actualizes the iterate_nodes function)

        Args:
            callback: Function to determine whether to iterate over node or not (callback(n), return Boolean)
            descend: Whether to descend into child nodes as well
            include_self: Whether to include self in the search

        Returns:
            []
        """
        return [x for x in self.iterate_nodes(callback, descend, include_self)]

    def find_node(self, callback, descend=False, include_self=True):
        """Return the first node found by given callback function.

        Args:
            callback: Function to determine whether to iterate over node or not (callback(n), return Boolean)
            descend: Whether to descend into child nodes as well
            include_self: Whether to include self in the search

        Returns:
            DataTreeNode or None
        """
        try:
            return next(self.iterate_nodes(callback, descend, include_self))
        except StopIteration:
            return None

    def has_node(self, callback, descend=False, include_self=True):
        """Return if given call back returns at least one matched node. This method is faster than find_nodes as it
        stops after/return the first found node.

        Args:
            callback: Function to determine whether to iterate over node or not (callback(n), return Boolean)
            descend: Whether to descend into child nodes as well
            include_self: Whether to include self in the search

        Returns:
            Boolean
        """
        return self.find_node(callback, descend, include_self=include_self) is not None

    def has_child(self, id, descend=False):
        """Return if given call back returns at least one matched node. This method is faster than find_nodes as it
        stops after/return the first found node.

        Args:
            id: Node id
            descend: Whether to descend into child nodes as well

        Returns:
            Boolean
        """
        return self.has_node(find_by_id(id), descend, include_self=False)

    def get_node(self, id, descend=False):
        """Obtain the node by given id

        Args:
            id: Node id
            descend: Whether to descend into child nodes as well

        Returns:
            DataTreeNode or None
        """
        return self.find_node(find_by_id(id), descend)

    def node_at(self, position=0):
        """Obtain node at given position

        Args:
            position: The node index. If <0, then it will return the index as counted from the back (-1 being the last
                item)

        Returns:
            DataTreeNode or None if index > node's child list
        """
        raise NotImplementedError()

    def remove_node(self, node):
        """Remove given node

        Args:
            node: Node to remove

        Returns:
            self

        Note:
            Scans only immediate nodes (does not scan for children's nodes nodes). For that use remove_node_by_id
        """
        self.remove_at(self.node_index(node))
        return self

    def remove_at(self, position=-1):
        """Remove node at given position

        Args:
            position: The node index. If <0, then it will return the index as counted from the back (-1 being the last
                item)

        Returns:
            Removed node or None if index > child size
        """
        raise NotImplementedError()

    def remove_nodes(self, callback, descend=False, include_self=False):
        """Scan and remove nodes by matching callback

        Args:
            callback: Callback to determine nodes removal status
            descend: Whether to scan children's nodes
            include_self: Whether to include self (detach) from its parent 

        Returns:
            self
        """
        if include_self:
            if callback(self):
                self.detach()

        nodes = self.find_nodes(callback,  descend, False)
        for node in nodes:
            node.detach()

        return self

    def clear_nodes(self):
        """Remove all child nodes

        Returns:
            self
        """
        raise NotImplementedError()

    def nodes(self):
        """Obtain child list

        Returns:
            List of DataTreeNode

        Note:
            Will always return a list, empty if node has no child nodes
        """
        raise NotImplementedError()

    def parent_node(self):
        """Obtain parent_node node

        Returns:
            DataTreeNode or None
        """
        raise NotImplementedError()

    def detach(self):
        """Remove self from parent_node (if attached)

        Returns:
            self
        """
        if self.parent_node():
            self.parent_node().remove_node(self)

        return self

    def clone(self, deep=False):
        """Performs a shallow clone of the data and nodes (new ids will be generated)

        Args:
            deep: Perform a deep copy instead

        Returns:
            DataTreeNode cloned node
        """
        raise NotImplementedError()


class DataTreeNode(GenericTreeNodeInterface):
    """A generic tree node/tree structure with ability to store custom data"""

    def __init__(self, **kwargs):
        """Constructor"""
        self._data = {}
        self._parent_node = None
        self._nodes = []
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
        self._validate_node_add(node)

        if position < 0:
            position = len(self._nodes) + 1 + position  # +1 since negative is adding after

        if position < 0:
            position = 0

        self._nodes.insert(position, node)
        node._parent_node = self

        return self

    def _validate_node_add(self, node):
        if not isinstance(node, DataTreeNode):
            raise TypeError("Node must be an instance of DataTreeNode")

        if node is self:
            raise RuntimeError("Can't add self as a child node")

        if node.parent_node() or node in self._nodes:
            raise RuntimeError("Node already attached to %s" % node.parent_node())

        _top = self
        while _top.parent_node():
            _top = _top.parent_node()

        if _top is node:
            raise RuntimeError("Detected recursive addition of node")

    def node_index(self, node):
        return self._nodes.index(node)

    def node_at(self, position=0):
        if position < 0:
            position = len(self._nodes) + position

        if position < 0 or position >= len(self._nodes):
            return None

        return self._nodes[position]

    def remove_at(self, position=-1):
        if position < 0:
            position = len(self._nodes) + position

        if position < 0 or position >= len(self._nodes):
            return None

        node = self._nodes.pop(position)
        node._parent_node = None
        return node

    def clear_nodes(self):
        for n in self._nodes:
            n._parent_node = None

        self._nodes = {}
        return self

    def nodes(self):
        return self._nodes

    def parent_node(self):
        return self._parent_node

    def clone(self, deep=False):
        node = DataTreeNode()

        data = self.get_data()
        node.set_data(copy.copy(data) if not deep else copy.deepcopy(data))

        for child in self.nodes():
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

        children = self.nodes()
        if len(children) > 0:
            logger("%s%s%s" % (indent * level, data_indent, "Children:"))
            for c in children:
                c._dump_node(logger=logger, indent=indent, data_indent=data_indent, level=level + 1)
