'''
Created on Feb 2, 2017

@author: radoslav
'''
import json
from kivy.logger import Logger
from kivy.uix.treeview import TreeView

from com.valsr.psb.tree import TreeNode


def saveProject( file, treeFileStructure = None, streamList = None ):
    Logger.info( 'Saving project to %s', file )

    jsonDict = {}
    if treeFileStructure:
        jsonDict['files'] = treeFileStructure.serialize()

    if streamList:
        jsonDict['streams'] = streamList.seralize()

    with open( file, 'w' ) as f:
        json.dump( jsonDict, f, indent = 2 )

    Logger.info( 'Project successfully saved to file %s', file )

def loadProject( file ):
    Logger.info( 'Opening project %s', file )
    with open( file, 'r' ) as f:
        jsonDict = json.load( f )

    tree = None
    stream = None
    if 'files' in jsonDict:
        tree = TreeNode( id = 'root', tree = None )
        tree.deserialize( tree = TreeView(), dict = jsonDict['files'] )

    Logger.info( 'Project file %s loaded successfully', file )

    return ( tree, stream )
