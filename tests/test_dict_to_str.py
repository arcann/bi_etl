"""
Created on Apr 1, 2015

@author: Derek Wood
"""
import sys
import unittest
from collections import OrderedDict
from datetime import datetime

from bi_etl.utility import dict_to_str

OrderedDict = dict if sys.version_info >= (3, 6) else OrderedDict


class TestDictToStr(unittest.TestCase):
    _multiprocess_can_split_ = True
    
    def assertRegexMsg(self, actual, expected_re):
        msg = "---\nexpected:\n{}\n---\ngot:\n{}\n---\n".format(
            expected_re.replace('\n', '\\n\n'),
            actual.replace('\n', '\\n\n')
        )
        self.assertRegex(actual, expected_re, msg)

    def test_list_no_type(self):
        lst = ['Val1', [1, 2, 3], 1.5]
        s = dict_to_str(lst, show_type=False)
        expected_re = (
            r"length = 3\s*\n"
            r"\s*list item 1: length = 4 Val1\s*\n"
            r"\s*list item 2: length = 3\s*\n"
            r"\s*list item 1: 1\s*\n"
            r"\s*list item 2: 2\s*\n"
            r"\s*list item 3: 3\s*\n"
            r"\s*list item 3: 1.5\s*")
        self.assertRegexMsg(s, expected_re)

    def test_nested_list_with_type(self):
        lst = ['Val1', [1, 2, 3], 1.5]
        s = dict_to_str(lst, show_type=True)
        expected_re = (
            r"length = 3\s* <(type|class) 'list'>\s*\n"
            r"  list item 1: length = 4\s+Val1\s+<(type|class) 'str'>\s*\n"
            r"  list item 2: length = 3\s+<class 'list'>\s*\n"
            r"    list item 1: 1\s+<(type|class) 'int'>\s*\n"
            r"    list item 2: 2\s+<(type|class) 'int'>\s*\n"
            r"    list item 3: 3\s+<(type|class) 'int'>\s*\n"
            r"  list item 3: 1.5\s+<(type|class) 'float'>"
        )
        self.assertRegexMsg(s, expected_re)
        
    def test_nested_dicts_no_type(self):
        # We need to use OrderedDict so that the entries come out in a guaranteed order
        d = OrderedDict()
        d['Val1'] = 1
        d['Val2'] = OrderedDict()
        d['Val2']['Release'] = datetime(1997, 12, 13)
        d['Val2']['Version'] = 1.5
        d['Val3'] = 1 
        s = dict_to_str(d, 
                        show_type=False,
                        show_list_item_number=False,
                        type_formats={datetime: '%Y-%m-%d'},
                        indent_per_level=1,                        
                        )
        expected_re = (
            r"length = 3\s*\n"
            r" Val1: 1\s*\n"
            r" Val2: length = 2\s*\n"
            r"  Release: 1997-12-13\s*\n"
            r"  Version: 1.5\s*\n"
            r" Val3: 1\s*"
        )
        self.assertRegexMsg(s, expected_re)

    def test_nested_dicts_no_type_with_len(self):
        # We need to use OrderedDict so that the entries come out in a guaranteed order
        d = OrderedDict()
        d['Val1'] = 1
        d['Val2'] = OrderedDict()
        d['Val2']['Release'] = datetime(1997, 12, 13)
        d['Val2']['Version'] = 1.5
        d['Val3'] = 1 
        s = dict_to_str(d, 
                        show_type=False,
                        show_list_item_number=True,
                        type_formats={datetime: '%Y-%m-%d'},
                        indent_per_level=1,                        
                        )
        expected_re = (
            r"length = 3\s*\n"
            r" Val1: 1\s*\n"
            r" Val2: length = 2\s*\n"
            r"  Release: 1997-12-13\s*\n"
            r"  Version: 1.5\s*\n"
            r" Val3: 1"
        )
        self.assertRegexMsg(s, expected_re)

    def test_nested_dicts_with_type(self):
        # We need to use OrderedDict so that the entries come out in a guaranteed order
        d = OrderedDict()
        d['Val1'] = 1
        d['Val2'] = OrderedDict()
        d['Val2']['Release'] = datetime(1997, 12, 13)
        d['Val2']['Version'] = 1.5
        d['Val3'] = 1 
        s = dict_to_str(d, 
                        type_formats={datetime: '%Y-%m-%d'},
                        indent_per_level=1,                        
                        )
        expected_re = (
            r"length = 3\s* <class '(collections.OrderedDict|dict)'>\s*\n"
            r" Val1: 1 <(type|class) 'int'>\n"
            r" Val2: length = 2\s* <class '(collections.OrderedDict|dict)'>\s*\n"
            r"  Release: 1997-12-13 <(type|class) 'datetime.datetime'>\s*\n"
            r"  Version: 1.5 <(type|class) 'float'>\s*\n"
            r" Val3: 1 <(type|class) 'int'>"
        )
        self.assertRegexMsg(s, expected_re)
        
    def test_nested_list_dict_no_type(self):
        # We need to use OrderedDict so that the entries come out in a guaranteed order
        lst = list()
        d = OrderedDict()
        lst.append(d)
        d['Release'] = datetime(1997, 12, 13)
        d['Version'] = 1.5
        
        d2 = OrderedDict()
        d2['Title'] = 'Robot Dreams'
        d2['Author'] = 'Isaac Asimov'
        lst.append(d2)
         
        s = dict_to_str(lst,
                        type_formats={datetime: '%Y-%m-%d'},
                        show_type=False,
                        show_list_item_number=False,
                        indent_per_level=1,                        
                        )
        expected_re = (
            r"length = 2\s*\n"
            r" length = 2\s*\n"
            r"  Release: 1997-12-13\s*\n"
            r"  Version: 1.5\s*\n"
            r" length = 2\s*\n"
            r"  Title: length = 12 Robot Dreams\s*\n"
            r"  Author: length = 12 Isaac Asimov\s*"
        )
        self.assertRegexMsg(s, expected_re)

    def test_nested_list_dict_with_type(self):
        # We need to use OrderedDict so that the entries come out in a guaranteed order
        lst = list()
        d = OrderedDict()
        lst.append(d)
        d['Release'] = datetime(1997, 12, 13)
        d['Version'] = 1.5
        
        d2 = OrderedDict()
        d2['Title'] = 'Robot Dreams'
        d2['Author'] = 'Isaac Asimov'
        lst.append(d2)
         
        s = dict_to_str(lst,
                        type_formats={datetime: '%Y-%m-%d'},
                        show_type=True,
                        show_list_item_number=False,
                        indent_per_level=1,                        
                        )
        expected_re = (
            r"length = 2\s+<(type|class) 'list'>\s*\n"
            r" length =\s+2\s+<(type|class) '(collections.OrderedDict|dict)'>\s*\n"
            r"  Release: 1997-12-13 <(type|class) 'datetime.datetime'>\s*\n"
            r"  Version: 1.5 <(type|class) 'float'>\s*\n"
            r" length = 2\s* <(type|class) '(collections.OrderedDict|dict)'>\s*\n"
            r"  Title: length = 12 Robot Dreams <(type|class) 'str'>\s*\n"
            r"  Author: length = 12 Isaac Asimov <(type|class) 'str'>\s*"
        )
        self.assertRegexMsg(s, expected_re)
    
    def test_nested_list_dict_no_type_no_length(self):
        # We need to use OrderedDict so that the entries come out in a guaranteed order
        lst = list()
        d = OrderedDict()
        lst.append(d)
        d['Release'] = datetime(1997, 12, 13)
        d['Version'] = 1.5
        
        d2 = OrderedDict()
        d2['Title'] = 'Robot Dreams'
        d2['Author'] = 'Isaac Asimov'
        lst.append(d2)
         
        s = dict_to_str(lst,
                        type_formats={datetime: '%Y-%m-%d'},
                        show_type=False,
                        show_list_item_number=False,
                        show_length=False,
                        indent_per_level=1,                        
                        )
        expected_re = (
            r"  Release: 1997-12-13\s*\n"
            r"  Version: 1.5\s*\n"
            r"  Title: Robot Dreams\s*\n"
            r"  Author: Isaac Asimov\s*"
        )
        self.assertRegexMsg(s, expected_re)


if __name__ == "__main__":
    unittest.main()
