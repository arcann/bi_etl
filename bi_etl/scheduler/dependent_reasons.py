"""
Created on Dec 12, 2015

@author: Derek Wood
"""
from bi_etl.scheduler.task import Status


def getFromString(reason_string):
    # TODO: Performance tune
    for reason_instance in {Predecessor, MutuallyExclusive, OtherSelf, Follower}:
        if reason_string == reason_instance.name:
            break
    return reason_instance


class _DependentReason(object):
    def __init__(self, name):
        self.name = name
        
    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
    
    def wait_on_status(self, status):
        raise NotImplementedError()
    
    def release_wait_on_status(self, status):
        return not(self.wait_on_status(status))


class _Predecessor(_DependentReason):
    def __init__(self):
        super().__init__('Predecessor')
        
    def wait_on_status(self, status):
        return status.is_active()


Predecessor = _Predecessor()    


class _MutuallyExclusive(_DependentReason):
    def __init__(self):
        super().__init__('Mutually exclusive instance is still is_alive')
        
    def wait_on_status(self, status):
        return status.is_active()

MutuallyExclusive = _MutuallyExclusive()


class _OtherSelf(_DependentReason):
    def __init__(self):
        super().__init__('Another instance of same task is_waiting (ahead of us)')
        
    def wait_on_status(self, status):
        return status.is_waiting() or status.is_active()


OtherSelf = _OtherSelf()         


class _Follower(_DependentReason):
    def __init__(self):
        super().__init__('Follower task is_alive')
        
    def wait_on_status(self, status):
        return (status in [Status.waiting_for_cpu, Status.running])

    
Follower = _Follower()