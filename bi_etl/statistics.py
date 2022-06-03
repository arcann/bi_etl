"""
Created on Mar 20, 2015

@author: Derek Wood
"""
import sys
import typing
from collections import OrderedDict

OrderedDict = dict if sys.version_info >= (3, 6) else OrderedDict
from typing import List

from bi_etl.timer import Timer
from bi_etl.utility import dict_to_str


class Statistics(object):
    """
    classdocs
    """

    def __init__(self, stats_id: str, parent: 'Statistics' = None, print_start_stop_times: bool = True):
        """
        Constructor
        """
        self.stats_id = stats_id
        self._stats_data = OrderedDict()
        self.parent_path = None
        if parent is not None:
            self.parent_path = parent.path
            parent[stats_id] = self
        self._timer = Timer(start_running=False)

        self.print_start_stop_times = print_start_stop_times

        # Add place-holders to the OrderedDict so that these timer stats are listed in keys or iterators
        # Needs to be at the end of __init__ so the place-holders don't set it to True
        self.used = False

    def __str__(self):
        return self.stats_id

    def __repr__(self):
        return dict_to_str(self)

    # Allow a Statistics object to follow the ETLTask interface as used by bi_etl.scheduler.task.ETLTask#statistics
    @property
    def statistics(self):
        return self

    @property
    def path(self) -> List[str]:
        if self.parent_path is not None:
            return self.parent_path + [self.stats_id]
        else:
            return [self.stats_id]

    def get_unique_stats_id(self, stats_id) -> str:
        id_nbr = 1
        base_stats_id = stats_id
        while stats_id in self:
            id_nbr += 1
            stats_id = '{} {}'.format(base_stats_id, id_nbr)
        return stats_id

    @property
    def timer(self):
        self.used = True
        return self._timer

    def __getitem__(self, key):
        if key == 'start time':
            return self.timer.first_start_time
        elif key == 'stop  time':
            return self.timer.stop_time
        elif key == 'seconds elapsed':
            return self.timer.seconds_elapsed
        elif key in self._stats_data:
            return self._stats_data[key]
        else:
            # Makes stats['new stat'] += x possible (although we do have add_to_stat)
            return 0

    def __setitem__(self, key, value):
        # Don't count assignment of 0 or None as used
        if value:
            self.used = True
        self._stats_data[key] = value
        if isinstance(value, Statistics):
            value.parent_path = self.path
            value.stats_id = key

    def add_to_stat(self, key, increment):
        if key in self:
            self[key] += increment
        else:
            self[key] = increment

    def ensure_exists(self, key, initial_value=0):
        if key not in self:
            self[key] = initial_value

    def iteritems(self):
        # Needs to be based on keys() because we force extra special keys
        for k in list(self.keys()):
            yield k, self[k]

    def items(self):
        # Needs to be based on keys() because we force extra special keys
        return list(self.iteritems())

    def keys(self):
        key_list = list()
        if self.timer.start_time is not None:
            if self.print_start_stop_times:
                key_list.append('start time')
                key_list.append('stop  time')
            key_list.append('seconds elapsed')
        key_list += list(self._stats_data.keys())
        return key_list

    def values(self):
        # Needs to be based on keys() because we force extra special keys
        values_data = []
        for k in list(self.keys()):
            values_data.append(self[k])
        return values_data

    def update(self, other):
        return self._stats_data.update(other)

    def merge(self, other):
        for stats_key in other.keys():
            value = other[stats_key]
            if isinstance(value, int):
                self.add_to_stat(stats_key, value)
            elif (isinstance(value, dict)
                  or isinstance(value, Statistics)):
                if self[stats_key] == 0:
                    self[stats_key] = value
                elif isinstance(self[stats_key], Statistics):
                    self[stats_key].merge(value)
                elif isinstance(self[stats_key], OrderedDict):
                    self[stats_key] = Statistics(stats_id=stats_key,
                                                 parent=self)
                    self[stats_key].merge(value)
                else:
                    raise ValueError(
                        "Can't merge {path}:{key} type {type} "
                        "with {opath}:{okey} type {otype}".format(
                            path=self.path,
                            key=stats_key,
                            type=type(self[stats_key]),
                            opath=other.path,
                            okey=stats_key,
                            otype=type(value),
                        )
                    )

    def __contains__(self, key):
        return self._stats_data.__contains__(key)

    def get(self, key, default=None):
        if key in self:
            return self[key]
        else:
            return default

    def __len__(self):
        return len(self._stats_data)

    def __delitem__(self, key):
        self._stats_data.__delitem__(key)

    def __iter__(self):
        for k in list(self.keys()):
            yield self[k]

    @staticmethod
    def format_statistics(container):
        return dict_to_str(container,
                           show_list_item_number=False,
                           show_type=False,
                           show_length=False,
                           indent_per_level=4,
                           type_formats={
                               int:   ',',
                               float: '.3f',
                           },
                           )

    @staticmethod
    def find_item(obj: typing.Union[str, dict, list], key: str):
        if isinstance(obj, str):
            return None
        elif hasattr(obj, 'values'):
            # If this key matches the target key, return it's value
            if key in obj:
                return obj[key]
            # Otherwise recursively check values
            for v in list(obj.values()):
                item = Statistics.find_item(v, key)
                if item is not None:
                    return item
                # Otherwise keep iterating keys
        elif isinstance(obj, list):
            for v in obj:
                item = Statistics.find_item(v, key)
                if item is not None:
                    return item
