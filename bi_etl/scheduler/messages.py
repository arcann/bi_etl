"""
Created on Apr 22, 2015

@author: Derek Wood
"""


class ChildRunRequested(object):
    def __init__(self, child_task_id):
        self.child_task_id = child_task_id

    def __repr__(self):
        return "ChildRunRequested(child_task_id={}".format(self.child_task_id)


class ChildRunOK(object):
    def __init__(self, child_task_id):
        self.child_task_id = child_task_id

    def __repr__(self):
        return "ChildRunOK(child_task_id={}".format(self.child_task_id)


class ChildStatusUpdate(object):
    def __init__(self, child_task_id, child_status):
        self.child_task_id = child_task_id
        self.child_status = child_status

    def __repr__(self):
        return "ChildStatusUpdate(child_task_id={}, child_status={}".format(self.child_task_id, self.child_status)


class ChildNotOccupyingCPU(object):
    def __init__(self, child_task_id):
        self.child_task_id = child_task_id

    def __repr__(self):
        return "ChildNotOccupyingCPU(child_task_id={}".format(self.child_task_id)


class ChildOccupyingCPU(object):
    def __init__(self, child_task_id):
        self.child_task_id = child_task_id

    def __repr__(self):
        return "ChildOccupyingCPU(child_task_id={}".format(self.child_task_id)


class SummaryMessage(object):
    def __init__(self, summary_message, append=False):
        self.summary_message = summary_message
        self.append = append

    def __repr__(self):
        return "SummaryMessage(summary_message={}, append={}".format(self.append, self.append)


class ChildSetDisplayName(object):
    def __init__(self, child_task_id, display_name):
        self.child_task_id = child_task_id
        self.display_name = display_name
        
    def __repr__(self):
        return "ChildSetDisplayName(child_task_id={}, display_name={}".format(self.child_task_id, self.display_name)      