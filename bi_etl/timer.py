"""
Created on Sep 17, 2014

@author: Derek Wood
"""

import timeit
from collections import OrderedDict
from datetime import datetime


class Timer(object):

    def __init__(self, task_name: str = None, start_running: bool = True) -> None:
        self.task_name = task_name
        self.stored_time = 0
        self.start_time = None
        self.first_start_time = None
        self.start_time_precise = None
        self.stop_time = None
        self.running = False
        self.format_strings = [
            # (Max_Seconds, Format_String)
            (  60, "{total_seconds:.3f} seconds"),
            (None, "{total_seconds:.1f} seconds ({hours:d}h:{minutes:02d}m:{seconds:02.1f}s)"),
            ]
        if start_running:
            self.start()

    @staticmethod
    def now() -> float:
        return timeit.default_timer()

    @property
    def seconds_elapsed(self) -> float:
        if self.running:
            return self.stored_time + (Timer.now() - self.start_time_precise)
        else:
            return self.stored_time

    @property
    def seconds_elapsed_formatted(self) -> str:
        total_seconds = self.seconds_elapsed
        hours = int(total_seconds / 3600)
        seconds = total_seconds - hours * 3600
        minutes = int(seconds / 60)
        seconds = seconds - minutes * 60
        format_index = 0
        while (format_index + 1) < len(self.format_strings) \
                and self.format_strings[format_index][0] is not None \
                and total_seconds > self.format_strings[format_index][0]:
            format_index += 1
        format_string = self.format_strings[format_index][1]
        return format_string.format(total_seconds=total_seconds,
                                    total_minutes=total_seconds/60,
                                    hours=hours,
                                    minutes=minutes,
                                    seconds=seconds,
                                    )

    @property
    def statistics(self) -> dict:
        stats = OrderedDict()
        if self.first_start_time != self.start_time:
            stats['first start time'] = self.first_start_time
            stats['recent start time'] = self.start_time
        else:
            stats['start time'] = self.start_time
        stats['stop time'] = self.stop_time
        stats['seconds elapsed'] = self.seconds_elapsed_formatted
        if self.task_name is None:
            return stats
        else:
            return dict({self.task_name: stats})

    def message(self, task_name: str = None) -> str:
        if not task_name:
            task_name = self.task_name or "Un-named task"
        if self.running:
            self.stop()
        return "{task} took {secs}".format(task=task_name, secs=self.seconds_elapsed_formatted)

    def message_detailed(self, task_name: str = None) -> str:
        if not task_name:
            task_name = self.task_name or "Un-named task"
        if self.running:
            self.stop()
        return "{task} started at {start} stopped at {stop} and took {secs}"\
            .format(task=task_name,
                    start=self.start_time,
                    stop=self.stop_time,
                    secs=self.seconds_elapsed_formatted
                    )

    def print(self) -> None:
        print(self.message_detailed())

    def start(self) -> None:
        if not self.running:
            self.start_time = datetime.now()
            if self.first_start_time is None:
                self.first_start_time = self.start_time
            self.start_time_precise = Timer.now()
            self.running = True

    def stop(self) -> None:
        if self.running:
            self.stop_time = datetime.now()
            if self.start_time_precise is not None:
                self.stored_time += Timer.now() - self.start_time_precise
            else:
                raise ValueError("stop called on Timer that was not started. Name={}"
                                 .format(self.task_name)
                                 )
            self.running = False

    def reset(self) -> None:
        """Resets the clock statistics and restarts it."""        
        self.start_time = datetime.now()
        self.first_start_time = self.start_time
        self.start_time_precise = Timer.now()
        self.running = True
