'''
'''
from kivy.uix.treeview import TreeViewLabel, TreeView
from com.valsr.psb.sound.info import MediaInfo


class TreeNode( TreeViewLabel ):

    def __init__( self, id, tree, label = None, data = None, **kwargs ):
        self.id_ = id
        self.data_ = data
        self.tree_ = tree
        super().__init__( text = label if label else id, **kwargs )

    def serialize( self ):
        dict = {}
        dict['id'] = self.id_
        dict['label'] = self.text
        dict['data'] = self.data_.serialize() if self.data_ else None
        dict['children'] = [x.serialize() for x in self.nodes]

        return dict

    def deserialize( self, tree, parent, dict ):
        self.id_ = dict['id']
        self.text = dict['label']
        self.data_ = MediaInfo.deserialize( dict['data'] )
        self.tree_ = tree

        tree.add_node( self, parent )
        for k, v in dict['children']:
            child = TreeNode( id = k )
            child.deserialize( tree, self, v )

    def hasChild( self, id ):
        for node in self.nodes:
            if node.id_ == id:
                return True

        return False

    def getChild( self, id ):
        for node in self.nodes:
            if node.id_ == id:
                return node

        return None

    def addChild ( self, child ):
        if not self.hasChild( child.id_ ):
            self.tree_.add_node( child, self )
            return child

        return None

    def removeSelf( self ):
        self.removeAllChildren()
        self.tree_.remove_node( self )
        return self

    def removeChild( self, id ):
        node = self.getChild( id )

        if node:
            node.removeSelf()

        return self

    def removeAllChildren( self ):
        for child in self.nodes:
            child.removeSelf()

        return self

    def openParents( self ):
        if self.parent_node:
            if not self.parent_node.is_open:
                self.tree_.toggle_node( self.parent_node )
            if isinstance ( self.parent_node, TreeNode ):
                self.parent_node.openParents()
        return self

    def findNodeByFingerprint( self, fingerprint ):
        if self.data_:
            if self.data_.fingerprint_ == fingerprint:
                return self

        for child in self.nodes:
            found = child.findNodeByFingerprint( fingerprint )
            if found:
                return found

        return None
