### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.memory_size.md "bi_etl.memory_size module") |
-   [previous](bi_etl.bi_config_parser.md "bi_etl.bi_config_parser module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »

<span id="bi-etl-conversions-module"></span>
bi\_etl.conversions module<a href="#module-bi_etl.conversions" class="headerlink" title="Permalink to this headline">¶</a>
==========================================================================================================================

Created on Nov 17, 2014

@author: woodd

 *class* `bi_etl.conversions.``Conversion`<span class="sig-paren">(</span>*function*, *\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#Conversion" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.Conversion" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="https://docs.python.org/2/library/functions.md#object" class="reference external" title="(in Python v2.7)"><code class="xref py py-class docutils literal">object</code></a>

<!-- -->

 *class* `bi_etl.conversions.``Transformation`<span class="sig-paren">(</span>*column*, *conversion*<span class="sig-paren">)</span><a href="#bi_etl.conversions.Transformation" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: `tuple`

 `column`<a href="#bi_etl.conversions.Transformation.column" class="headerlink" title="Permalink to this definition">¶</a>  
Alias for field number 0

 `conversion`<a href="#bi_etl.conversions.Transformation.conversion" class="headerlink" title="Permalink to this definition">¶</a>  
Alias for field number 1

 `count`<span class="sig-paren">(</span>*value*<span class="sig-paren">)</span> → integer -- return number of occurrences of value<a href="#bi_etl.conversions.Transformation.count" class="headerlink" title="Permalink to this definition">¶</a>  

 `index`<span class="sig-paren">(</span>*value*<span class="optional">\[</span>, *start*<span class="optional">\[</span>, *stop*<span class="optional">\]</span><span class="optional">\]</span><span class="sig-paren">)</span> → integer -- return first index of value.<a href="#bi_etl.conversions.Transformation.index" class="headerlink" title="Permalink to this definition">¶</a>  
Raises ValueError if the value is not present.

<!-- -->

 `bi_etl.conversions.``bytes2human`<span class="sig-paren">(</span>*n*, *format\_str='%(value).1f %(symbol)s'*, *symbols='customary'*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#bytes2human" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.bytes2human" class="headerlink" title="Permalink to this definition">¶</a>  
Convert n bytes into a human readable string based on format\_str. symbols can be either “customary”, “customary\_ext”, “iec” or “iec\_ext”, see: <a href="http://goo.gl/kTQMs" class="uri" class="reference external">http://goo.gl/kTQMs</a>

    >>> bytes2human(0)
    '0.0 B'
    >>> bytes2human(0.9)
    '0.0 B'
    >>> bytes2human(1)
    '1.0 B'
    >>> bytes2human(1.9)
    '1.0 B'
    >>> bytes2human(1024)
    '1.0 K'
    >>> bytes2human(1048576)
    '1.0 M'
    >>> bytes2human(1099511627776127398123789121)
    '909.5 Y'

    >>> bytes2human(9856, symbols="customary")
    '9.6 K'
    >>> bytes2human(9856, symbols="customary_ext")
    '9.6 kilo'
    >>> bytes2human(9856, symbols="iec")
    '9.6 Ki'
    >>> bytes2human(9856, symbols="iec_ext")
    '9.6 kibi'

    >>> bytes2human(10000, "%(value).1f %(symbol)s/sec")
    '9.8 K/sec'

    >>> # precision can be adjusted by playing with %f operator
    >>> bytes2human(10000, format_str="%(value).5f %(symbol)s")
    '9.76562 K'

<!-- -->

 `bi_etl.conversions.``change_tz`<span class="sig-paren">(</span>*source\_datetime*, *from\_tzone*, *to\_tzone*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#change_tz" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.change_tz" class="headerlink" title="Permalink to this definition">¶</a>  
Change time-zones in dates that have no time-zone info, or incorrect time-zone info

Example from\_tzone or to\_tzone values: ::  
import pytz

pytz.utc pytz.timezone(‘US/Eastern’)

<!-- -->

 `bi_etl.conversions.``defaultInvalid`<span class="sig-paren">(</span>*v*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#defaultInvalid" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.defaultInvalid" class="headerlink" title="Permalink to this definition">¶</a>  
Same as nvl(v, ‘Invalid’)

<!-- -->

 `bi_etl.conversions.``defaultMissing`<span class="sig-paren">(</span>*v*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#defaultMissing" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.defaultMissing" class="headerlink" title="Permalink to this definition">¶</a>  
Same as nvl(v, ‘Missing’)

<!-- -->

 `bi_etl.conversions.``defaultNines`<span class="sig-paren">(</span>*v*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#defaultNines" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.defaultNines" class="headerlink" title="Permalink to this definition">¶</a>  
Same as nvl(v, -9999)

<!-- -->

 `bi_etl.conversions.``defaultQuestionmark`<span class="sig-paren">(</span>*v*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#defaultQuestionmark" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.defaultQuestionmark" class="headerlink" title="Permalink to this definition">¶</a>  
Same as nvl(v, ‘?’)

<!-- -->

 `bi_etl.conversions.``ensure_datetime`<span class="sig-paren">(</span>*dt*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#ensure_datetime" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.ensure_datetime" class="headerlink" title="Permalink to this definition">¶</a>  
Takes a date or a datetime as input, outputs a datetime

<!-- -->

 `bi_etl.conversions.``human2bytes`<span class="sig-paren">(</span>*s*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#human2bytes" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.human2bytes" class="headerlink" title="Permalink to this definition">¶</a>  
Attempts to guess the string format based on default symbols set and return the corresponding bytes as an integer. When unable to recognize the format ValueError is raised.

    >>> human2bytes('0 B')
    0
    >>> human2bytes('1 K')
    1024
    >>> human2bytes('1 M')
    1048576
    >>> human2bytes('1 Gi')
    1073741824
    >>> human2bytes('1 tera')
    1099511627776

    >>> human2bytes('0.5kilo')
    512
    >>> human2bytes('0.1  byte')
    0
    >>> human2bytes('1 k')  # k is an alias for K
    1024
    >>> human2bytes('12 foo')
    Traceback (most recent call last):
        ...
    ValueError: can't interpret '12 foo'

<!-- -->

 `bi_etl.conversions.``nullif`<span class="sig-paren">(</span>*v*, *value\_to\_null*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#nullif" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.nullif" class="headerlink" title="Permalink to this definition">¶</a>  
Pass value through unchanged unless it is equal to provided value\_to\_null value. If v ==\`value\_to\_null\` value then return NULL (None)

<!-- -->

 `bi_etl.conversions.``nvl`<span class="sig-paren">(</span>*value*, *default*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#nvl" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.nvl" class="headerlink" title="Permalink to this definition">¶</a>  
Pass value through unchanged unless it is NULL (None). If it is NULL (None), then return provided default value.

<!-- -->

 `bi_etl.conversions.``replace_tilda`<span class="sig-paren">(</span>*e*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#replace_tilda" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.replace_tilda" class="headerlink" title="Permalink to this definition">¶</a>  
Used for unicode error to replace invalid ascii with ~

<!-- -->

 `bi_etl.conversions.``str2bytes_size`<span class="sig-paren">(</span>*str\_size*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#str2bytes_size" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.str2bytes_size" class="headerlink" title="Permalink to this definition">¶</a>  
Parses a string containing a size in bytes including KB, MB, GB, TB codes into an integer with the actual number of bytes (using 1 KB = 1024).

<!-- -->

 `bi_etl.conversions.``str2date`<span class="sig-paren">(</span>*s*, *dt\_format='%m/%d/%Y'*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#str2date" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.str2date" class="headerlink" title="Permalink to this definition">¶</a>  
Parse a date (no time) value stored in a string.

|             |                                                                                                                                                                                                                                                                                                                                                                                                         |
|-------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **s** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – String value to convert                                                                                                                                                                                                                               
  -   **dt\_format** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – For format options please see <a href="https://docs.python.org/3.5/library/datetime.md#strftime-strptime-behavior" class="uri" class="reference external">https://docs.python.org/3.5/library/datetime.md#strftime-strptime-behavior</a>  |

<!-- -->

 `bi_etl.conversions.``str2datetime`<span class="sig-paren">(</span>*s*, *dt\_format='%m/%d/%Y %H:%M:%S'*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#str2datetime" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.str2datetime" class="headerlink" title="Permalink to this definition">¶</a>  
Parse a date + time value stored in a string.

|             |                                                                                                                                                                                                                                                                                                                                                                                                         |
|-------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **s** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – String value to convert                                                                                                                                                                                                                               
  -   **dt\_format** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – For format options please see <a href="https://docs.python.org/3.5/library/datetime.md#strftime-strptime-behavior" class="uri" class="reference external">https://docs.python.org/3.5/library/datetime.md#strftime-strptime-behavior</a>  |

<!-- -->

 `bi_etl.conversions.``str2decimal`<span class="sig-paren">(</span>*s*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#str2decimal" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.str2decimal" class="headerlink" title="Permalink to this definition">¶</a>  
String to decimal (AKA numeric)

<!-- -->

 `bi_etl.conversions.``str2decimal_end_sign`<span class="sig-paren">(</span>*s*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#str2decimal_end_sign" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.str2decimal_end_sign" class="headerlink" title="Permalink to this definition">¶</a>  
String to decimal (AKA numeric). This version is almost 4 times faster than tr2decimal in handling signs at the end of the string.

<!-- -->

 `bi_etl.conversions.``str2float`<span class="sig-paren">(</span>*s*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#str2float" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.str2float" class="headerlink" title="Permalink to this definition">¶</a>  
String to floating point

<!-- -->

 `bi_etl.conversions.``str2float_end_sign`<span class="sig-paren">(</span>*s*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#str2float_end_sign" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.str2float_end_sign" class="headerlink" title="Permalink to this definition">¶</a>  
String to integer This version is almost 4 times faster than str2float in handling signs at the end of the string.

<!-- -->

 `bi_etl.conversions.``str2int`<span class="sig-paren">(</span>*s*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#str2int" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.str2int" class="headerlink" title="Permalink to this definition">¶</a>  
String to integer

<!-- -->

 `bi_etl.conversions.``str2time`<span class="sig-paren">(</span>*s*, *dt\_format='%H:%M:%S'*<span class="sig-paren">)</span><a href="_modules/bi_etl/conversions.md#str2time" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.conversions.str2time" class="headerlink" title="Permalink to this definition">¶</a>  
Parse a time of day value stored in a string.

|             |                                                                                                                                                                                                                                                                                                                                                                                                         |
|-------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **s** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – String value to convert                                                                                                                                                                                                                               
  -   **dt\_format** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – For format options please see <a href="https://docs.python.org/3.5/library/datetime.md#strftime-strptime-behavior" class="uri" class="reference external">https://docs.python.org/3.5/library/datetime.md#strftime-strptime-behavior</a>  |

#### Previous topic

[bi\_etl.bi\_config\_parser module](bi_etl.bi_config_parser.md "previous chapter")

#### Next topic

[bi\_etl.memory\_size module](bi_etl.memory_size.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.memory_size.md "bi_etl.memory_size module") |
-   [previous](bi_etl.bi_config_parser.md "bi_etl.bi_config_parser module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
