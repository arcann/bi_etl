# -*- coding: utf-8 -*-
"""
Created on Dec 23, 2015

@author: Derek Wood
"""

import sys

from bi_etl.scheduler.sdtout_queue import StdoutQueue


def redirect_output_to(queue_instance):
    if queue_instance is not None and not hasattr(sys, 'saved_stds_tuple'):
        sys.saved_stds_tuple = (sys.stdout, sys.stderr)
        queue_out_stream = StdoutQueue(queue_instance)
        sys.stdout = queue_out_stream
        sys.stderr = queue_out_stream
        return queue_out_stream
    else:
        return None


def restore_standard_output():
    if hasattr(sys, 'saved_stds_tuple'):
        sys.stdout, sys.stderr = sys.saved_stds_tuple
        del sys.saved_stds_tuple
