"""
Created on Apr 23, 2015

@author: Derek Wood
"""


class TaskStopRequested(Exception):
    pass

class ParameterError(Exception):
    pass

class WorkflowFinished(Exception):
    pass

class CircularDependency(Exception):
    def __init__(self, circular_list):
        self.circular_list = circular_list
    
    def __repr__(self):
        return "CircularDependency(circular_list=\n{}".format(self.circular_list)
    
class DependencyDeeperThanLimit(Exception):
    def __init__(self, limit, maxed_list):
        self.limit = limit
        self.maxed_list = maxed_list
    
    def __repr__(self):
        return "DependencyDeeperThanLimit(limit={}, maxed_list={}".format(self.limit, self.maxed_list)