# -*- coding: utf-8 -*-
"""
Created on Feb 13, 2016

@author: Derek Wood
"""

_frozenset_cache = dict()


def get_cached_frozen_set(set_to_be_frozen):
    if not isinstance(set_to_be_frozen, set):
        set_to_be_frozen = frozenset(set_to_be_frozen)
    
    if set_to_be_frozen in _frozenset_cache:
        return _frozenset_cache[set_to_be_frozen]
    else:
        _frozenset_cache[set_to_be_frozen] = set_to_be_frozen
        return set_to_be_frozen
