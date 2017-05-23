### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.utility.ask.md "bi_etl.utility.ask module") |
-   [previous](bi_etl.tests.test_task.md "bi_etl.tests.test_task module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »

bi\_etl.utility package<a href="#bi-etl-utility-package" class="headerlink" title="Permalink to this headline">¶</a>
====================================================================================================================

Submodules<a href="#submodules" class="headerlink" title="Permalink to this headline">¶</a>
-------------------------------------------------------------------------------------------

-   <a href="bi_etl.utility.ask.md" class="reference internal">bi_etl.utility.ask module</a>

<span id="module-contents"></span>
Module contents<a href="#module-bi_etl.utility" class="headerlink" title="Permalink to this headline">¶</a>
-----------------------------------------------------------------------------------------------------------

Created on Nov 18, 2014

@author: woodd

 *class* `bi_etl.utility.``CaseInsensitiveDict`<span class="sig-paren">(</span>*data=None*, *\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/utility.md#CaseInsensitiveDict" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.utility.CaseInsensitiveDict" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: `collections.abc.MutableMapping`

A case-insensitive `dict`-like object. Implements all methods and operations of `collections.MutableMapping` as well as dict’s `copy`. Also provides `lower_items`. All keys are expected to be strings. The structure remembers the case of the last key to be set, and `iter(instance)`, `keys()`, `items()`, `iterkeys()`, and `iteritems()` will contain case-sensitive keys. However, querying and contains testing is case insensitive:

    cid = CaseInsensitiveDict()
    cid['Accept'] = 'application/json'
    cid['ACCEPT'] == 'application/json' # True
    list(cid) == ['Accept'] # True

For example, `headers['content-encoding']` will return the value of a `'Content-Encoding'` response header, regardless of how the header name was originally stored. If the constructor, `.update`, or equality comparison operations are given keys that have equal `.lower()`, the behavior is undefined.

 `clear`<span class="sig-paren">(</span><span class="sig-paren">)</span> → None. Remove all items from D.<a href="#bi_etl.utility.CaseInsensitiveDict.clear" class="headerlink" title="Permalink to this definition">¶</a>  

 `copy`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/utility.md#CaseInsensitiveDict.copy" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.utility.CaseInsensitiveDict.copy" class="headerlink" title="Permalink to this definition">¶</a>  

 `get`<span class="sig-paren">(</span>*k*<span class="optional">\[</span>, *d*<span class="optional">\]</span><span class="sig-paren">)</span> → D\[k\] if k in D, else d. d defaults to None.<a href="#bi_etl.utility.CaseInsensitiveDict.get" class="headerlink" title="Permalink to this definition">¶</a>  

 `items`<span class="sig-paren">(</span><span class="sig-paren">)</span> → a set-like object providing a view on D's items<a href="#bi_etl.utility.CaseInsensitiveDict.items" class="headerlink" title="Permalink to this definition">¶</a>  

 `keys`<span class="sig-paren">(</span><span class="sig-paren">)</span> → a set-like object providing a view on D's keys<a href="#bi_etl.utility.CaseInsensitiveDict.keys" class="headerlink" title="Permalink to this definition">¶</a>  

 `lower_items`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/utility.md#CaseInsensitiveDict.lower_items" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.utility.CaseInsensitiveDict.lower_items" class="headerlink" title="Permalink to this definition">¶</a>  
Like iteritems(), but with all lowercase keys.

 `pop`<span class="sig-paren">(</span>*k*<span class="optional">\[</span>, *d*<span class="optional">\]</span><span class="sig-paren">)</span> → v, remove specified key and return the corresponding value.<a href="#bi_etl.utility.CaseInsensitiveDict.pop" class="headerlink" title="Permalink to this definition">¶</a>  
If key is not found, d is returned if given, otherwise KeyError is raised.

 `popitem`<span class="sig-paren">(</span><span class="sig-paren">)</span> → (k, v), remove and return some (key, value) pair<a href="#bi_etl.utility.CaseInsensitiveDict.popitem" class="headerlink" title="Permalink to this definition">¶</a>  
as a 2-tuple; but raise KeyError if D is empty.

 `setdefault`<span class="sig-paren">(</span>*k*<span class="optional">\[</span>, *d*<span class="optional">\]</span><span class="sig-paren">)</span> → D.get(k,d), also set D\[k\]=d if k not in D<a href="#bi_etl.utility.CaseInsensitiveDict.setdefault" class="headerlink" title="Permalink to this definition">¶</a>  

 `update`<span class="sig-paren">(</span><span class="optional">\[</span>*E*, <span class="optional">\]</span>*\*\*F*<span class="sig-paren">)</span> → None. Update D from mapping/iterable E and F.<a href="#bi_etl.utility.CaseInsensitiveDict.update" class="headerlink" title="Permalink to this definition">¶</a>  
If E present and has a .keys() method, does: for k in E: D\[k\] = E\[k\] If E present and lacks .keys() method, does: for (k, v) in E: D\[k\] = v In either case, this is followed by: for k, v in F.items(): D\[k\] = v

 `values`<span class="sig-paren">(</span><span class="sig-paren">)</span> → an object providing a view on D's values<a href="#bi_etl.utility.CaseInsensitiveDict.values" class="headerlink" title="Permalink to this definition">¶</a>  

<!-- -->

 `bi_etl.utility.``dict_to_list`<span class="sig-paren">(</span>*obj*, *depth=0*, *\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/utility.md#dict_to_list" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.utility.dict_to_list" class="headerlink" title="Permalink to this definition">¶</a>  

<!-- -->

 `bi_etl.utility.``dict_to_pairs`<span class="sig-paren">(</span>*obj*, *prefix=None*, *delimit='.'*<span class="sig-paren">)</span><a href="_modules/bi_etl/utility.md#dict_to_pairs" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.utility.dict_to_pairs" class="headerlink" title="Permalink to this definition">¶</a>  

<!-- -->

 `bi_etl.utility.``dict_to_str`<span class="sig-paren">(</span>*obj*, *depth=0*, *\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/utility.md#dict_to_str" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.utility.dict_to_str" class="headerlink" title="Permalink to this definition">¶</a>  
Parameters: obj is the object to convert to a string format

entry\_name is the main title to put at the top (default blank)

depth is the starting depth (default 0)

indent\_per\_level is the number of spaces to indent per depth level (default 2)

depth\_limit is the limit on how many levels deep to recurse (default no limit)

item\_limit is the limit on how many items in a given container to output (default no limit)

show\_type is a boolean indicating if the type of each entry should be included (default True)

show\_list\_item\_number is a boolean indicating if the sequence number should be included for list entries (default True)

type\_formats is a dictionary mapping types to print format specifiers

<!-- -->

 `bi_etl.utility.``getIntegerPlaces`<span class="sig-paren">(</span>*theNumber*<span class="sig-paren">)</span><a href="_modules/bi_etl/utility.md#getIntegerPlaces" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.utility.getIntegerPlaces" class="headerlink" title="Permalink to this definition">¶</a>  

<!-- -->

 `bi_etl.utility.``log_logging_level`<span class="sig-paren">(</span>*log*<span class="sig-paren">)</span><a href="_modules/bi_etl/utility.md#log_logging_level" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.utility.log_logging_level" class="headerlink" title="Permalink to this definition">¶</a>  

### [Table Of Contents](index.md)

-   <a href="#" class="reference internal">bi_etl.utility package</a>
    -   <a href="#submodules" class="reference internal">Submodules</a>
    -   <a href="#module-bi_etl.utility" class="reference internal">Module contents</a>

#### Previous topic

[bi\_etl.tests.test\_task module](bi_etl.tests.test_task.md "previous chapter")

#### Next topic

[bi\_etl.utility.ask module](bi_etl.utility.ask.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.utility.ask.md "bi_etl.utility.ask module") |
-   [previous](bi_etl.tests.test_task.md "bi_etl.tests.test_task module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
