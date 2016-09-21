"""
Created on Sep 17, 2014

@author: woodd
"""

from datetime import datetime
import timeit
from collections import OrderedDict

class Timer(object):

    def __init__(self, task_name = None, start_running = True):
        self.task_name = task_name
        self.stored_time = 0
        self.start_time = None
        self.first_start_time = None
        self.start_time_precise = None
        self.stop_time = None
        self.running = False
        if start_running:
            self.start()

    @staticmethod
    def now():
        return timeit.default_timer()

    @property
    def seconds_elapsed(self):
        if self.running:
            return self.stored_time + (Timer.now() - self.start_time_precise)
        else:
            return self.stored_time

    @property
    def seconds_elapsed_formatted(self):
        return "{:.3f}".format(self.seconds_elapsed)

    @property
    def statistics(self):
        stats = OrderedDict()
        if self.first_start_time != self.start_time:
            stats['first start time'] = self.first_start_time
            stats['recent start time'] = self.start_time
        else:
            stats['start time'] = self.start_time
        stats['stop time'] = self.stop_time
        stats['seconds elapsed'] = self.seconds_elapsed
        if self.task_name is None:
            return stats
        else:
            return {self.task_name: stats}

    def message(self, task_name = None):
        if not task_name:
            task_name = self.task_name or "Un-named task"
        if self.running:
            self.stop()
        return "{task} took {secs}".format(task = task_name, secs = self.seconds_elapsed)

    def message_detailed(self, task_name = None):
        if not task_name:
            task_name = self.task_name or "Un-named task"
        if self.running:
            self.stop()
        return "{task} started at {start} stopped at {stop} and took {secs} seconds".format(task = task_name,
                                                                                            start = self.start_time,
                                                                                            stop = self.stop_time,
                                                                                            secs = self.seconds_elapsed)

    def start(self):
        if not self.running:
            self.start_time = datetime.now()
            if self.first_start_time is None:
                self.first_start_time = self.start_time
            self.start_time_precise = Timer.now()
            self.running = True

    def stop(self):
        if self.running:
            self.stop_time = datetime.now()
            if not self.start_time_precise is None:
                self.stored_time += Timer.now() - self.start_time_precise
            else:
                raise ValueError("stop called on Timer that was not started. Name={}".format(self.task_name))
            self.running = False

    def reset(self):
        """Resets the clock statistics and restarts it."""        
        self.__init__()
