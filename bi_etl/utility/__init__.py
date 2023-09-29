"""
Created on Nov 18, 2014

@author: Derek Wood
"""
import logging
import math
import typing


def dict_to_list(obj,
                 depth=0,
                 **kwargs
                 ):
    # This proc will catch all exceptions in many places.
    # This is done because dict_to_list is used to print debug
    # and error messages and shouldn't raise exceptions itself. 
    # pylint: disable= broad-except

    # Optional Arguments
    indent_per_level = kwargs.get('indent_per_level', 2)
    depth_limit = kwargs.get('depth_limit')
    entry_name = kwargs.get('entry_name')
    if entry_name is not None and not isinstance(entry_name, str):
        entry_name = str(entry_name)
    # Don't pass entry name to next call
    if 'entry_name' in kwargs:
        del kwargs['entry_name']
    item_limit = kwargs.get('item_limit')
    sorted_dicts = kwargs.get('sorted_dicts')
    show_type = kwargs.get('show_type', True)
    show_length = kwargs.get('show_length', True)
    show_list_item_number = kwargs.get('show_list_item_number', True)
    type_formats = kwargs.get('type_formats')
    display_internal_dict = kwargs.get('display_internal_dict', False)
    result = []
    name_value_separator = ': '
    # Performance tweak.  Store result.append reference once locally since that's faster
    result_add = result.append
    try:

        if indent_per_level * depth > 0:
            indent = (' ' * indent_per_level * depth)
        else:
            indent = ''
        if entry_name is not None:
            entry_header = [entry_name, name_value_separator]
        else:
            entry_header = []
        if show_length and hasattr(obj, '__len__'):
            try:
                entry_header.append("length = " + str(len(obj)) + " ")
            except TypeError:
                pass

        if depth_limit:
            if depth >= depth_limit:
                result_add(indent)
                return result + ["--Depth Limit--"]
        item_number = 0
        # If we have a format specified for this type
        if type_formats is not None and type(obj) in type_formats:
            result_add(indent)
            result += entry_header
            try:
                line_format = '{:' + type_formats[type(obj)] + '}'
                result_add(line_format.format(obj))
            except Exception as e:
                result_add(repr(e))
            if show_type:
                result_add(' ' + str(type(obj)))
        elif isinstance(obj, int):
            result_add(indent)
            result += entry_header
            try:
                result_add(str(obj))
            except Exception as e:
                result_add(repr(e))
            if show_type:
                result_add(" <type 'int'>")
        elif isinstance(obj, str):
            result_add(indent)
            result += entry_header
            try:
                result_add(obj)
            except Exception as e:
                result_add(repr(e))
            if show_type:
                result_add(' ')
                result_add(str(type(obj)))
        elif isinstance(obj, bytes):
            result_add(indent)
            result += entry_header
            try:
                result_add(str(obj))
            except Exception as e:
                result_add(repr(e))
            if show_type:
                result_add(' ')
                result_add(str(type(obj)))
        elif isinstance(obj, type):
            result_add(indent)
            result += entry_header
            try:
                result_add(str(obj))
            except Exception as e:
                result_add(repr(e))
            if show_type:
                result_add(' ')
                result_add(str(type(obj)))
        # -----------------------------------------------------------------------
        # Row like (use columns_in_order to get the columns in the correct order)
        elif hasattr(obj, 'columns_in_order'):
            if show_type:
                if len(entry_header) != 0:
                    entry_header.append(' ')
                entry_header.append(str(type(obj)))
            if len(entry_header) != 0:
                result_add(indent)
                result += entry_header
                result_add('\n')
            for k in obj.columns_in_order:
                v = obj[k]
                item_number += 1
                if item_number > 1:
                    result += ['\n']
                if item_limit:
                    if item_number >= item_limit:
                        result_add("--Item Limit--")
                        break
                result += dict_to_list(v, depth=depth + 1, entry_name=k, **kwargs)
        # -----------------------------------------------------------------------
        # Dict like object
        elif hasattr(obj, 'items'):
            if show_type:
                if len(entry_header) != 0:
                    entry_header.append(' ')
                entry_header.append(str(type(obj)))
            if len(entry_header) != 0:
                result_add(indent)
                result += entry_header
                result_add('\n')
            try:
                if sorted_dicts:
                    items = sorted(obj.items())
                else:
                    items = list(obj.items())
            except TypeError as e:
                result_add(repr(e))
                return result

            for k, v in items:
                item_number += 1
                if item_number > 1:
                    result += ['\n']
                if item_limit:
                    if item_number >= item_limit:
                        result_add("--Item Limit--")
                        break
                result += dict_to_list(v, depth=depth + 1, entry_name=k, **kwargs)
        # -----------------------------------------------------------------------
        # list like
        elif hasattr(obj, '__iter__'):
            if show_type:
                if len(entry_header) != 0:
                    entry_header.append(' ')
                entry_header.append(str(type(obj)))
            if len(entry_header) != 0:
                result_add(indent)
                result += entry_header
                result_add('\n')
            try:
                for v in obj:
                    item_number += 1
                    if item_number > 1:
                        result_add('\n')
                    if item_limit:
                        if item_number >= item_limit:
                            result_add("--Item Limit--")
                            break
                    if show_list_item_number:
                        kwargs['entry_name'] = ('list item ' + str(item_number))
                    result += dict_to_list(v, depth=depth + 1, **kwargs)
            except IOError as e:
                result_add(repr(e))
            except TypeError as e:
                result_add(repr(e))
        # -----------------------------------------------------------------------
        # SQLAlchemy ORM object
        elif hasattr(obj, '__table__'):
            if show_type:
                if len(entry_header) != 0:
                    entry_header.append(' ')
                entry_header.append(str(type(obj)))
            if len(entry_header) != 0:
                result_add(indent)
                result += entry_header
                result_add('\n')
            for column in obj.__table__.columns:
                attr = column.name
                result_add('\n')
                v = getattr(obj, attr)
                result += dict_to_list(v, depth=depth + 1, entry_name=attr, **kwargs)
                if show_type:
                    result_add(' ' + str(type(v)))
        elif display_internal_dict and hasattr(obj, '__dict__'):
            result_add(indent)
            result += entry_header
            result_add(str(obj))
            if show_type:
                try:
                    result_add(' ' + str(type(obj)))
                except Exception as e:
                    result_add(repr(e))
            result_add('\n')
            result += dict_to_list(obj.__dict__, depth=depth + 1, entry_name=entry_name + '.__dict__', **kwargs)
        # -----------------------------------------------------------------------
        # Otherwise use the default str
        else:
            result_add(indent)
            result += entry_header
            result_add(str(obj))
            if show_type:
                try:
                    result_add(' ' + str(type(obj)))
                except Exception as e:
                    result_add(repr(e))
        return result
    except Exception as e:
        # print((traceback.format_exc()))
        return [repr(e)]


def dict_to_str(obj,
                depth=0,
                **kwargs
                ):
    """
    Parameters:
    obj is the object to convert to a string format

    entry_name is the main title to put at the top (default blank)

    depth is the starting depth (default 0)

    indent_per_level is the number of spaces to indent per depth level (default 2)

    depth_limit is the limit on how many levels deep to recurse (default no limit)

    item_limit is the limit on how many items in a given container to output (default no limit)

    show_type is a boolean indicating if the type of each entry should be included (default True)

    show_list_item_number is a boolean indicating if the sequence number should be included for list entries
    (default True)

    type_formats is a dictionary mapping types to print format specifiers

    """
    return ''.join(dict_to_list(obj, depth, **kwargs))


def dict_to_pairs(obj, prefix=None, delimit='.'):
    for k in list(obj.keys()):
        val = obj[k]

        if prefix is None:
            name = k
        else:
            name = prefix + delimit + k

        if hasattr(val, 'keys') and hasattr(val, '__getitem__'):
            for stat_tuple in dict_to_pairs(val, prefix=name, delimit=delimit):
                yield stat_tuple
        else:
            yield name, obj[k]


def log_logging_level(log):
    original_level = log.getEffectiveLevel()
    if original_level > logging.INFO:
        # If we aren't at INFO level or more detailed, then temporarily set it to INFO and restore it later
        log.setLevel(logging.INFO)
    log.info(
        f'Logging level is {logging.getLevelName(original_level)} ({log.getEffectiveLevel()})'
        )
    if original_level > logging.INFO:
        # Restore logging level
        log.setLevel(original_level)


def get_integer_places(number):
    abs_number = int(abs(number))
    if abs_number == 0:
        return 0
    # For numbers larger than 999999999999997 the log10 function's rounding causes the result to be too big
    elif abs_number <= 999999999999997:
        return int(math.log10(abs_number)) + 1
    else:
        # str tested as faster than trying to count digits via exponentiation
        return len(str(abs_number))


def single_quote_value(value) -> str:
    return f"'{value}'"


def double_quote_value(value) -> str:
    return f'"{value}"'


def quote_delimited_list(
        value_list,
        delimiter=', ',
        quote_function: typing.Callable[[object], str] = single_quote_value,
        ) -> str:
    return delimiter.join([quote_function(v) for v in value_list])
