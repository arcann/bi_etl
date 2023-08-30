# -*- coding: utf-8 -*-
"""
Created on Jan 12, 2016

@author: Derek Wood
"""
import gc
import os
import sys
from copy import copy

from bi_etl.components.row.row import Row


def get_size_gc(obj,
                depth_limit=10,
                depth=0,
                processed_objects=None,
                processed_classes=None,
                ref_chain=None):
    """
    For debugging only!  This function is very slow. 10,000 cells (rows * columns) takes 1 second.
    """
    if processed_objects is None:
        processed_objects = set()
    if id(obj) in processed_objects:
        return 0
    type_name = str(type(obj))
    if type_name in ["<class 'function'>",
                     "<class 'property'>",
                     "<class 'staticmethod'>",
                     "<class 'module'>",
                     "<class 'classmethod'>",
                     "<class 'ipykernel.iostream.OutStream'>",
                     "<class 'IPython.core.completer.IPCompleter'>",
                     ]:
        return 0
    processed_objects.add(id(obj))
    size = sys.getsizeof(obj)
    if processed_classes is not None:
        if ref_chain is None:
            ref_chain = [type_name]
        else:
            ref_chain.append(type_name)
        d = processed_classes.get(type_name, {'cnt': 0, 'size': 0, 'max_depth': 0})
        d['cnt'] += 1
        d['size'] += size
        if depth > d.get('max_depth', 0):
            d['max_depth'] = depth
            d['ref_chain'] = copy(ref_chain)
        processed_classes[type_name] = d
    if isinstance(obj, Row):
        for child in obj.values():
            size += get_size_gc(child,
                                depth_limit=depth_limit,
                                depth=depth + 1,
                                processed_objects=processed_objects,
                                processed_classes=processed_classes,
                                ref_chain=ref_chain)
    else:
        for child in gc.get_referents(obj):
            size += get_size_gc(child,
                                depth_limit=depth_limit,
                                depth=depth + 1,
                                processed_objects=processed_objects,
                                processed_classes=processed_classes,
                                ref_chain=ref_chain)
    if ref_chain is not None:
        ref_chain.pop()
    return size


def sort_key(item):
    return item[1]['size']


def get_size_summary(obj, print_summary=True):
    procssed_objects = set()
    processed_classes = dict()

    sz = get_size_gc(obj, processed_objects=procssed_objects, processed_classes=processed_classes)
    if print_summary:
        for cls, data in sorted(processed_classes.items(), key=sort_key):
            print(f'{cls} size = {data["size"]:,} cnt= {data["cnt"]:,} max_depth={data["max_depth"]}')
            print(f'\t ref_chain={data.get("ref_chain", None)}')
            print()
        print(f'size={sz:,}')
    return sz


def get_dir_size(path):
    total_size = 0
    if os.path.isfile(path):
        total_size = os.path.getsize(path)
    else:
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
    return total_size
