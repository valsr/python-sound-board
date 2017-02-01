'''
'''

class TreeNode( object ):

    def __init__( self, name, label = None, data = None, parent = None ):
        self.name_ = name
        self.label_ = name if label is None else label
        self.children_ = []
        self.data_ = data
        self.parent_ = parent

    def serialize( self ):
        dict = {}
        dict['name'] = self.name_
        dict['label'] = self.label_
        dict['data'] = self.data_
        dict['children'] = [x.serialize() for x in self.children_]

        return dict

    def deserialize( self, dict ):
        self.name_ = dict['name']
        self.label_ = dict['label']
        self.data_ = dict['data']
        self.children_ = []
        for x in dict['children']:
            child = TreeNode( name = 'child', parent = self )
            child.deserialize( x )
            self.children_.append( child )
