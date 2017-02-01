'''
'''
from kivy.uix.treeview import TreeViewLabel, TreeView

class TreeNode( TreeViewLabel ):

    def __init__( self, name, tree, label = None, data = None, **kwargs ):
        self.name_ = name
        self.data_ = data
        self.tree_ = tree
        label = name if label is None else label
        super().__init__( text = label, **kwargs )

    def serialize( self ):
        dict = {}
        dict['name'] = self.name_
        dict['label'] = self.text
        dict['data'] = self.data_
        dict['children'] = [x.serialize() for x in self.nodes]

        return dict

    def deserialize( self, tree, parent, dict ):
        self.name_ = dict['name']
        self.text = dict['label']
        self.data_ = dict['data']
        self.tree_ = tree

        tree.add_node( self, parent )
        for k, v in dict['children']:
            child = TreeNode( name = k )
            child.deserialize( tree, self, v )

    def hasChild( self, name ):
        for node in self.nodes:
            if node.name_ == name:
                return True

        return False

    def getChild( self, name ):
        for node in self.nodes:
            if node.name_ == name:
                return node

        return None

    def addChild ( self, child ):
        if not self.hasChild( child.name_ ):
            self.tree_.add_node( child, self )
            return True

        return False

    def removeSelf( self ):
        self.tree_.remove_node( self )

    def removeChild( self, name ):
        node = self.getChild( name )

        if node:
            node.removeSelf()
