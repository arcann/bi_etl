"""
Created on Apr 17, 2015

@author: Derek Wood
"""
import sys

 
class StdoutQueue(object):
    """
    This is a stdout replacement that sends messages to a Queue.  It ensures that all messages are strings.
    """
    def __init__(self,queue):
        self.queue = queue

    def write(self,msg):
        if not isinstance(msg,str):
            msg = str(msg)
        self.queue.put(msg)

    def flush(self):
        sys.__stdout__.flush()