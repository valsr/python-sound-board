'''
'''
from kivy.logger import Logger
from kivy.uix.treeview import TreeViewLabel, TreeView, TreeViewNode

from com.valsr.psb.callback import CallbackRegister
from com.valsr.psb.sound.info import MediaInfo


class TreeNode( TreeViewLabel, CallbackRegister ):


    def __init__( self, id, tree, label = None, data = None, **kwargs ):
        self.id = id
        self.data_ = data
        self.tree_ = tree
        super().__init__( text = label if label else id, **kwargs )

    def serialize( self ):
        dict = {}
        dict['id'] = self.id
        dict['label'] = self.text
        dict['data'] = self.data_.serialize() if self.data_ else None
        dict['children'] = [x.serialize() for x in self.nodes]

        return dict

    def deserialize( self, tree, dict ):
        self.id = dict['id']
        self.text = dict['label']
        self.data_ = MediaInfo.deserialize( dict['data'] )
        self.tree_ = tree

        for child in dict['children']:
            childNode = TreeNode( id = child["id"], tree = None )
            childNode.deserialize( tree, child )
            self.addChild( childNode )

    def hasChild( self, id ):
        for node in self.nodes:
            if node.id == id:
                return True

        return False

    def getChild( self, id ):
        for node in self.nodes:
            if node.id == id:
                return node

        return None

    def addChild ( self, child ):
        if not self.hasChild( child.id ):
            self.tree_.add_node( child, self )
            return child

        return None

    def removeSelf( self ):
        if self.tree_:
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

    def on_touch_down( self, touch ):
        if self.collide_point( *touch.pos ):
            if self.call( 'touch_down', None, True, self, touch ):
                return True

    def on_touch_move( self, touch ):
        if touch.grab_current is self:
            pass

    def on_touch_up( self, touch ):
        if self.collide_point( *touch.pos ):
            if self.call( 'touch_up', None, True, self, touch ):
                return True

    def detach( self ):
        return self.removeSelf()

    def attachTo( self, tree ):
        if self.tree_:
            self.detach()

        self.tree_ = tree
        tree.add_node( self )

    def walk( self ):
        yield self, self.nodes

        for node in self.nodes:
            yield from node.walk()
