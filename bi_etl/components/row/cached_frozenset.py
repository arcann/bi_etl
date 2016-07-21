# -*- coding: utf-8 -*-
'''
Created on Feb 13, 2016

@author: woodd
'''

_frozenset_cache = dict()

def get_cached_frozen_set(example_frozen_set):
    if not isinstance(example_frozen_set, set):
        example_frozen_set = frozenset(example_frozen_set)
    
    if example_frozen_set in _frozenset_cache:
        return _frozenset_cache[example_frozen_set]
    else:
        _frozenset_cache[example_frozen_set] = example_frozen_set
        return example_frozen_set