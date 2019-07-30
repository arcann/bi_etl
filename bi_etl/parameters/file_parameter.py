"""
Created on Apr 16, 2015

@author: Derek Wood
"""
from os.path import os

class FileParameter(object):
    """
    Wrapper for passing files via ETLTask parameters
    """

    def __init__(self, file_name, file_contents= None):
        """
        Constructor
        """
        self.file_name = file_name
        self.file_contents = file_contents
       
    def __str__(self):
        return "FileParameter(file_name=r'{}', file_contents has length {})".format(self.file_name, len(self.file_contents)) 
        
    def load_contents(self, file_path):
        with open(os.path.join(file_path, self.file_name), 'rb') as fh:
            self.file_contents = fh.read()
        
    def save_contents(self, file_path, file_name=None):
        if file_name is None:
            file_name = self.file_name
        path = os.path.join(file_path, file_name)
        with open(path, 'wb') as fh:
            fh.write(self.file_contents)
        return path