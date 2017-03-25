"""
Created on March 24, 2017

@author: valsr <valsr@valsr.com>
"""


class CustomDataWidget(object):

    def __init__(self, data=None):
        self._widget_data = {}
        if isinstance(data, dict):
            for name in data:
                self.store_data(name, data[name])
        elif data:
            self.store_data('data', data)

    def store_data(self, name, value):
        self._widget_data[name] = value

    def get_data(self, name, default=None):
        if name in self._widget_data:
            return self._widget_data[name]
        else:
            return default

    def has_data(self, name):
        return name in self._widget_data
