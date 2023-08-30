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
        return f"CircularDependency(circular_list=\n{self.circular_list}"


class DependencyDeeperThanLimit(Exception):
    def __init__(self, limit, maxed_list):
        self.limit = limit
        self.maxed_list = maxed_list
    
    def __repr__(self):
        return f"DependencyDeeperThanLimit(limit={self.limit}, maxed_list={self.maxed_list}"
