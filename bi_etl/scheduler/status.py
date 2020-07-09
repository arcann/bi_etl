# -*- coding: utf-8 -*-
"""
Created on Dec 23, 2015

@author: Derek Wood
"""
from enum import IntEnum, unique


@unique
class Status(IntEnum):
    # Note: The scheduler uses the lowest valued status as the summary status for a parent task
    
    new = 0
    # Waiting to run
    waiting_for_cpu = 1
    waiting_for_dependencies = 2
    waiting_for_workflow = 3
    # Running
    running = 10
    ancestors_running = 11  # Not actually running in a thread but ancestors haven't finished yet
    # Stop steps
    stop_requested = 21
    stop_signal_sent = 22    
    stopped = -20
    # Kill steps
    kill_requested = 31
    kill_signal_sent = 32
    killed = -30
    # Completed statuses
    succeeded = 100
    failed = -99
    ancestor_failed = -98
    cancelled = -5
    
    def status_category(self):
        if self.is_finished():
            return 'Finished'
        elif self.is_alive():
            return 'Running'
        else:
            return 'Waiting'
    
    def is_finished(self):
        return self.value == Status.succeeded or self.value < 0
    
    def is_active(self):
        if self.is_finished():
            return False
        elif self.value == Status.ancestors_running:
            return False
        else:
            return True
        
    def is_not_active(self):
        return not self.is_active()            
    
    def is_waiting(self):
        return self.value in [Status.new, Status.waiting_for_dependencies, Status.waiting_for_cpu, Status.waiting_for_workflow]
    
    def is_alive(self):
        return self.value >= Status.running.value and self != Status.succeeded
    
    def is_terminated(self):
        return self in [Status.killed, Status.stopped]
    
    def is_termination_pending(self):
        return (self in [Status.stop_requested, 
                         Status.stop_signal_sent, 
                         Status.kill_requested, 
                         Status.kill_signal_sent
                         ]
                )
    @staticmethod
    def print_status_list():
        for s in sorted(Status):
            fmt = "{s.name:25} {s.value:3} category={status_category:8s} waiting={is_waiting:2} alive={alive:2} active={active:2} Finished={finished:2} Terminated={terminated:2} Termination_pending={termination_pending:2}"
            print(fmt.format(s=s, 
                             status_category=s.status_category(),
                             is_waiting=s.is_waiting(),
                             alive=s.is_alive(), 
                             active=s.is_active(),
                             finished=s.is_finished(), 
                             terminated=s.is_terminated(), 
                             termination_pending= s.is_termination_pending(),
                            )
                 )
