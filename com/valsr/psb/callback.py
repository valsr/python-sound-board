'''
Created on Feb 2, 2017

@author: radoslav
'''
import uuid

class CallbackRegister( object ):
    '''
    classdocs
    '''
    def __init__( self, **kwargs ):
        '''
        Constructor
        '''
        self.callbacks_ = {}
        super().__init__( **kwargs )

    def registerCallback( self, t, cb ):
        id = CallbackRegister.genCallbackId()

        if t not in self.callbacks_:
            self.callbacks_[t] = {}

        self.callbacks_[t][id] = cb

        return id

    def unregisterCallback( self, t, id ):
        if t in self.callbacks_:
            if id in self.callbacks_[t]:
                self.callbacks_[t].pop( id )
                return True

        return False

    def getCallbacks( self, t ):
        if t in self.callbacks_:
            return self.callbacks_[t]

        return {}

    def call( self, t, id = None, exitOnTrue = False, *args, **kwargs ):
        cbs = self.getCallbacks( t )
        for key in cbs:
            if id == None or id == key:
                ret = cbs[key]( *args, **kwargs )
                if exitOnTrue and ret:
                    return key

        return None
    @staticmethod
    def genCallbackId():
        return uuid.uuid1().int

