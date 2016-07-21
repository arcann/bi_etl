'''
Created on Apr 1, 2015

@author: woodd
'''
import unittest
from bi_etl.utility import dict_to_str
from datetime import datetime
from collections import OrderedDict


class Test(unittest.TestCase):
    _multiprocess_can_split_ = True
    
    def assertRegexMsg(self, actual, expectedRe):
        msg="---\nexpected:\n{}\n---\ngot:\n{}\n---\n".format(expectedRe.replace('\n','\\n\n'), 
                                                              actual.replace('\n','\\n\n')
                                                             )
        self.assertRegex(actual, expectedRe, msg)

    def test_list_no_type(self):
        l = ['Val1',[1,2,3],1.5]
        s = dict_to_str(l, show_type=False)
        #print(s)
        expectedRe = "length = 3\s*\n"
        expectedRe += "\s*list item 1: length = 4 Val1\s*\n"
        expectedRe += "\s*list item 2: length = 3\s*\n"
        expectedRe += "\s*list item 1: 1\s*\n"
        expectedRe += "\s*list item 2: 2\s*\n"
        expectedRe += "\s*list item 3: 3\s*\n"
        expectedRe += "\s*list item 3: 1.5\s*"
        self.assertRegexMsg(s, expectedRe)

    def test_nested_list_with_type(self):
        l = ['Val1',[1,2,3],1.5]
        s = dict_to_str(l, show_type=True)
        #print(s)        
        expectedRe = "length = 3\s* <(type|class) 'list'>\s*\n"
        expectedRe += "  list item 1: length = 4\s+Val1\s+<(type|class) 'str'>\s*\n"
        expectedRe += "  list item 2: length = 3\s+<class 'list'>\s*\n"
        expectedRe += "    list item 1: 1\s+<(type|class) 'int'>\s*\n"
        expectedRe += "    list item 2: 2\s+<(type|class) 'int'>\s*\n"
        expectedRe += "    list item 3: 3\s+<(type|class) 'int'>\s*\n"
        expectedRe += "  list item 3: 1.5\s+<(type|class) 'float'>"
        self.assertRegexMsg(s, expectedRe)
        
    def test_nested_dicts_no_type(self):
        ## We need to use OrderedDict so that the entries come out in a guaranteed order
        d = OrderedDict()
        d['Val1'] = 1
        d['Val2'] = OrderedDict()
        d['Val2']['Release'] = datetime(1997,12,13)
        d['Val2']['Version'] = 1.5
        d['Val3'] = 1 
        s = dict_to_str(d, 
                        show_type=False,
                        show_list_item_number=False,
                        type_formats = {datetime: '%Y-%m-%d'},
                        indent_per_level=1,                        
                        )
        #print(s)
        expectedRe = "length = 3\s*\n"
        expectedRe += " Val1: 1\s*\n"
        expectedRe += " Val2: length = 2\s*\n"
        expectedRe += "  Release: 1997-12-13\s*\n"
        expectedRe += "  Version: 1.5\s*\n"
        expectedRe += " Val3: 1\s*"
        self.assertRegexMsg(s, expectedRe)

    def test_nested_dicts_no_type_with_len(self):
        ## We need to use OrderedDict so that the entries come out in a guaranteed order
        d = OrderedDict()
        d['Val1'] = 1
        d['Val2'] = OrderedDict()
        d['Val2']['Release'] = datetime(1997,12,13)
        d['Val2']['Version'] = 1.5
        d['Val3'] = 1 
        s = dict_to_str(d, 
                        show_type=False,
                        show_list_item_number=True,
                        type_formats = {datetime: '%Y-%m-%d'},
                        indent_per_level=1,                        
                        )
        #print(s)
        expectedRe = "length = 3\s*\n"
        expectedRe += " Val1: 1\s*\n"
        expectedRe += " Val2: length = 2\s*\n"
        expectedRe += "  Release: 1997-12-13\s*\n"
        expectedRe += "  Version: 1.5\s*\n"
        expectedRe += " Val3: 1"
        self.assertRegexMsg(s, expectedRe)


    def test_nested_dicts_with_type(self):
        ## We need to use OrderedDict so that the entries come out in a guaranteed order
        d = OrderedDict()
        d['Val1'] = 1
        d['Val2'] = OrderedDict()
        d['Val2']['Release'] = datetime(1997,12,13)
        d['Val2']['Version'] = 1.5
        d['Val3'] = 1 
        s = dict_to_str(d, 
                        type_formats = {datetime: '%Y-%m-%d'},
                        indent_per_level=1,                        
                        )
        #print(s)
        expectedRe = "length = 3\s* <class 'collections.OrderedDict'>\s*\n"
        expectedRe += " Val1: 1 <(type|class) 'int'>\n"
        expectedRe += " Val2: length = 2\s* <class 'collections.OrderedDict'>\s*\n"
        expectedRe += "  Release: 1997-12-13 <(type|class) 'datetime.datetime'>\s*\n"
        expectedRe += "  Version: 1.5 <(type|class) 'float'>\s*\n"
        expectedRe += " Val3: 1 <(type|class) 'int'>"
        self.assertRegexMsg(s, expectedRe)
        
    def test_nested_list_dict_no_type(self):
        ## We need to use OrderedDict so that the entries come out in a guaranteed order
        l = list()
        d = OrderedDict()
        l.append(d)
        d['Release'] = datetime(1997,12,13)
        d['Version'] = 1.5
        
        d2 = OrderedDict()
        d2['Title'] = 'Robot Dreams'
        d2['Author'] = 'Isaac Asimov'
        l.append(d2)
         
        s = dict_to_str(l, 
                        type_formats = {datetime: '%Y-%m-%d'},
                        show_type=False,
                        show_list_item_number=False,
                        indent_per_level=1,                        
                        )
        #print(s)
        expectedRe = "length = 2\s*\n"
        expectedRe += " length = 2\s*\n"
        expectedRe += "  Release: 1997-12-13\s*\n"
        expectedRe += "  Version: 1.5\s*\n"
        expectedRe += " length = 2\s*\n"
        expectedRe += "  Title: length = 12 Robot Dreams\s*\n"
        expectedRe += "  Author: length = 12 Isaac Asimov\s*"
        self.assertRegexMsg(s, expectedRe)

    def test_nested_list_dict_with_type(self):
        ## We need to use OrderedDict so that the entries come out in a guaranteed order
        l = list()
        d = OrderedDict()
        l.append(d)
        d['Release'] = datetime(1997,12,13)
        d['Version'] = 1.5
        
        d2 = OrderedDict()
        d2['Title'] = 'Robot Dreams'
        d2['Author'] = 'Isaac Asimov'
        l.append(d2)
         
        s = dict_to_str(l, 
                        type_formats = {datetime: '%Y-%m-%d'},
                        show_type=True,
                        show_list_item_number=False,
                        indent_per_level=1,                        
                        )
        #print(s)
        expectedRe = "length = 2\s+<(type|class) 'list'>\s*\n"
        expectedRe += " length =\s+2\s+<(type|class) 'collections.OrderedDict'>\s*\n"
        expectedRe += "  Release: 1997-12-13 <(type|class) 'datetime.datetime'>\s*\n"
        expectedRe += "  Version: 1.5 <(type|class) 'float'>\s*\n"
        expectedRe += " length = 2\s* <(type|class) 'collections.OrderedDict'>\s*\n"
        expectedRe += "  Title: length = 12 Robot Dreams <(type|class) 'str'>\s*\n"
        expectedRe += "  Author: length = 12 Isaac Asimov <(type|class) 'str'>\s*"
        self.assertRegexMsg(s, expectedRe)
    
    def test_nested_list_dict_no_type_no_length(self):
        ## We need to use OrderedDict so that the entries come out in a guaranteed order
        l = list()
        d = OrderedDict()
        l.append(d)
        d['Release'] = datetime(1997,12,13)
        d['Version'] = 1.5
        
        d2 = OrderedDict()
        d2['Title'] = 'Robot Dreams'
        d2['Author'] = 'Isaac Asimov'
        l.append(d2)
         
        s = dict_to_str(l, 
                        type_formats = {datetime: '%Y-%m-%d'},
                        show_type=False,
                        show_list_item_number=False,
                        show_length= False,
                        indent_per_level=1,                        
                        )
        #print(s)
        expectedRe = "  Release: 1997-12-13\s*\n"
        expectedRe += "  Version: 1.5\s*\n"
        expectedRe += "  Title: Robot Dreams\s*\n"
        expectedRe += "  Author: Isaac Asimov\s*"
        self.assertRegexMsg(s, expectedRe)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_list']
    unittest.main()