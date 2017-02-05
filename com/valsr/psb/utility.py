'''
Created on Feb 2, 2017

@author: radoslav
'''
from Crypto.Protocol.AllOrNothing import isInt
import json
from kivy.logger import Logger
from kivy.uix.treeview import TreeView

from com.valsr.psb.sound.info import MediaInfo
from com.valsr.psb.tree import TreeNode
from com.valsr.psb.ui.widget.draggabletreeview import DraggableTreeViewNode


def saveProject( file, treeFileStructure = None, streamList = None ):
    Logger.info( 'Saving project to %s', file )

    jsonDict = {}
    files = []
    if treeFileStructure:
        for child in treeFileStructure.root.nodes:
            files.append( serializeNodeStructure( child ) )
        jsonDict['files'] = files

    if streamList:
        jsonDict['streams'] = streamList.seralize()

    with open( file, 'w' ) as f:
        json.dump( jsonDict, f, indent = 2 )

    Logger.info( 'Project successfully saved to file %s', file )

def serializeNodeStructure( node ):

    if not isinstance( node, DraggableTreeViewNode ):
        raise RuntimeError( "Can only serialize DraggableTreeViewNodes" )

    d = {}
    d['id'] = node.id
    d['label'] = node._label.text

    if isinstance( node.data, MediaInfo ):
        d['data'] = node.data.serialize()
    else:
        d['data'] = None

    # serialize children
    d['children'] = []
    for child in node.nodes:
        d['children'].append( serializeNodeStructure( child ) )

    return d

def deserializeNodeStructure( d, parent ):
    node = DraggableTreeViewNode( id = d['id'], data = d['data'], label = d['label'] )
    node.is_open = True
    parent.add_node( node )
    if 'children' in d:
        for child in d['children']:
            deserializeNodeStructure( child, node )

def loadProject( file, tree ):
    Logger.info( 'Opening project %s', file )
    with open( file, 'r' ) as f:
        jsonDict = json.load( f )

    # clear up the files tree
    tree.remove_all_nodes()

    nodes = None
    stream = None
    if 'files' in jsonDict:
        for n in jsonDict['files']:
            deserializeNodeStructure( n, tree.root )

    Logger.info( 'Project file %s loaded successfully', file )

    return ( nodes, stream )
