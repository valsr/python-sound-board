"""
Created on Feb 2, 2017

@author: valsr <valsr@valsr.com>
"""
import uuid


class CallbackRegister(object):
    """Handles callback registration to allow multiple callbacks per registration event"""

    def __init__(self, **kwargs):
        """Constructor"""
        self._callbacks = {}
        super().__init__(**kwargs)

    def register_callback(self, callback_type, cb):
        """Register callback

        Args:
            callback_type: Callback type
            cb: Callback to register

        Returns:
            callback identifier
        """
        cb_id = CallbackRegister.generate_callback_id()

        if callback_type not in self._callbacks:
            self._callbacks[callback_type] = {}

        self._callbacks[callback_type][cb_id] = cb

        return cb_id

    def unregister_callback(self, cb_id, callback_type=None):
        """Unregister callback.

        Args:
            cb_id: Callback identifier
            callback_type: Callback type. If type is None a search will be performed on all callbacks

        Returns:
            True if the callback has been removed, False otherwise
        """

        if callback_type is None:
            for k, v in self._callbacks:
                if cb_id in v:
                    callback_type = k
                    break

        if callback_type in self._callbacks:
            if cb_id in self._callbacks[callback_type]:
                self._callbacks[callback_type].pop(cb_id)
                return True

        return False

    def callbacks(self, callback_type):
        """Obtain callbacks of given type

        Args:
            callback_type: Callback type identifier

        Returns:
            Dictionary (empty dictionary if type does not exist)
        """
        if callback_type in self._callbacks:
            return self._callbacks[callback_type]

        return {}

    def call(self, callback_type=None, cb_id=None, exit_on_true=False, *args, **kwargs):
        """Call specific callback to all register callback. If cb_id is provided it will filter callbacks by that id.
        If callback_type is provided the method will filter based on that type

        Args:
            callback_type: Callback type
            cb_id: Callback identifier to call
            exit_on_true: Stop calling other callbacks if any callbacks returns True
            args: Positional arguments added to the call
            kwargs: Arguments to add to the call

        Returns:
            int: callback id that returned True (if exit_on_true is True) or
            None
        """
        if not callback_type:
            for key, cbs in self._callbacks:
                for key in cbs:
                    if not cb_id or cb_id == key:
                        ret = cbs[key](*args, **kwargs)
                        if exit_on_true and ret:
                            return key
        else:
            cbs = self.callbacks(callback_type)
            for key in cbs:
                if not cb_id or cb_id == key:
                    ret = cbs[key](*args, **kwargs)
                    if exit_on_true and ret:
                        return key
        return None

    @staticmethod
    def generate_callback_id():
        """Generate an unique callback identifier

        Returns:
            int
        """
        return int(uuid.uuid1())
