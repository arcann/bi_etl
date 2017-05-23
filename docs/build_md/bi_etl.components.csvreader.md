### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.components.data_analyzer.md "bi_etl.components.data_analyzer module") |
-   [previous](bi_etl.components.row.row_status.md "bi_etl.components.row.row_status module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.components package](bi_etl.components.md) »

<span id="bi-etl-components-csvreader-module"></span>
bi\_etl.components.csvreader module<a href="#module-bi_etl.components.csvreader" class="headerlink" title="Permalink to this headline">¶</a>
============================================================================================================================================

Created on Sep 17, 2014

@author: woodd

 *class* `bi_etl.components.csvreader.``CSVReader`<span class="sig-paren">(</span>*task: bi\_etl.scheduler.task.ETLTask, filedata: typing.Union\[typing.TextIO, str\], encoding: str = None, errors: str = 'strict', logical\_name: str = None, \*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/csvreader.md#CSVReader" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.csvreader.CSVReader" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="bi_etl.components.etlcomponent.md#bi_etl.components.etlcomponent.ETLComponent" class="reference internal" title="bi_etl.components.etlcomponent.ETLComponent"><code class="xref py py-class docutils literal">bi_etl.components.etlcomponent.ETLComponent</code></a>

CSVReader is similar to csv.DictReader However, instead of a dict it uses our <a href="bi_etl.components.row.row.md#bi_etl.components.row.row.Row" class="reference internal" title="bi_etl.components.row.row.Row"><code class="xref py py-class docutils literal">Row</code></a> class as it’s return type. It uses `csv.reader` (in <a href="https://docs.python.org/2/library/csv.md#module-csv" class="reference external" title="(in Python v2.7)"><code class="xref py py-mod docutils literal">csv</code></a>) to read the file.

Note optional, but important, parameter `delimiter`.

**Valid values for \`errors\` parameter:**

<table>
<colgroup>
<col width="25%" />
<col width="75%" />
</colgroup>
<thead>
<tr class="header">
<th>Value</th>
<th>Meaning</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>‘strict’</td>
<td>raise a ValueError error (or a subclass)</td>
</tr>
<tr class="even">
<td>‘ignore’</td>
<td>ignore the character and continue with the next</td>
</tr>
<tr class="odd">
<td>‘replace’</td>
<td>replace with a suitable replacement character; Python will use the official U+FFFD REPLACEMENT CHARACTER for the builtin Unicode codecs on decoding and ‘?’ on encoding.</td>
</tr>
<tr class="even">
<td>‘surrogateescape’</td>
<td>replace with private code points U+DCnn.</td>
</tr>
</tbody>
</table>

|             |                                                                                                                                                                       |
|-------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **task** – The instance to register in (if not None)                                                                                                              
  -   **filedata** – The file to parse as delimited. If str then it’s assumed to be a filename. Otherwise it’s assumed to be a file object.                              
  -   **encoding** – The encoding to use when opening the file, if it was a filename and not already opened. Default is None which becomes the Python default encoding   
  -   **errors** – The error handling to use when opening the file (if it was a filename and not already opened) Default is ‘strict’ See above for valid errors values.  
  -   **logical\_name** – The logical name of this source. Used for log messages.                                                                                        |

 `column_names`<a href="#bi_etl.components.csvreader.CSVReader.column_names" class="headerlink" title="Permalink to this definition">¶</a>  
list The names to use for columns

 `primary_key`<a href="#bi_etl.components.csvreader.CSVReader.primary_key" class="headerlink" title="Permalink to this definition">¶</a>  
str The name of the primary key column. Only impacts trace messages. Default=None.

 `dialect`<a href="#bi_etl.components.csvreader.CSVReader.dialect" class="headerlink" title="Permalink to this definition">¶</a>  
str or subclass of <a href="https://docs.python.org/2/library/csv.md#csv.Dialect" class="reference external" title="(in Python v2.7)"><code class="xref py py-class docutils literal">csv.Dialect</code></a> Default “excel”. The dialect value to pass to <a href="https://docs.python.org/2/library/csv.md#module-csv" class="reference external" title="(in Python v2.7)"><code class="xref py py-mod docutils literal">csv</code></a>

 `delimiter`<a href="#bi_etl.components.csvreader.CSVReader.delimiter" class="headerlink" title="Permalink to this definition">¶</a>  
str The delimiter used in the file. Default is ‘,’.

 `doublequote`<a href="#bi_etl.components.csvreader.CSVReader.doublequote" class="headerlink" title="Permalink to this definition">¶</a>  
boolean Controls how instances of quotechar appearing inside a column should themselves be quoted. When True, the character is doubled. When False, the escapechar is used as a prefix to the quotechar. It defaults to True.

 `escapechar`<a href="#bi_etl.components.csvreader.CSVReader.escapechar" class="headerlink" title="Permalink to this definition">¶</a>  
str A one-character string used by the writer to escape the delimiter if quoting is set to QUOTE\_NONE and the quotechar if doublequote is False. On reading, the escapechar removes any special meaning from the following character. It defaults to None, which disables escaping.

 `quotechar`<a href="#bi_etl.components.csvreader.CSVReader.quotechar" class="headerlink" title="Permalink to this definition">¶</a>  
str A one-character string used to quote columns containing special characters, such as the delimiter or quotechar, or which contain new-line characters. It defaults to ‘”’.

 `quoting`<a href="#bi_etl.components.csvreader.CSVReader.quoting" class="headerlink" title="Permalink to this definition">¶</a>  
Controls when quotes should be generated by the writer and recognised by the reader. Can be either of the constants defined in this module. \* QUOTE\_NONE \* QUOTE\_MINIMAL Defaults to QUOTE\_MINIMAL.

For more details see <a href="https://docs.python.org/3/library/csv.md#csv.QUOTE_ALL" class="uri" class="reference external">https://docs.python.org/3/library/csv.md#csv.QUOTE_ALL</a>

 `skipinitialspace`<a href="#bi_etl.components.csvreader.CSVReader.skipinitialspace" class="headerlink" title="Permalink to this definition">¶</a>  
boolean When True, whitespace immediately following the delimiter is ignored. The default is False.

 `strict`<a href="#bi_etl.components.csvreader.CSVReader.strict" class="headerlink" title="Permalink to this definition">¶</a>  
boolean When True, raise exception Error on bad CSV input. The default is False.

 `header_row`<a href="#bi_etl.components.csvreader.CSVReader.header_row" class="headerlink" title="Permalink to this definition">¶</a>  
int The row to parse for headers

 `start_row`<a href="#bi_etl.components.csvreader.CSVReader.start_row" class="headerlink" title="Permalink to this definition">¶</a>  
int The first row to parse for data

 `log_first_row`<a href="#bi_etl.components.csvreader.CSVReader.log_first_row" class="headerlink" title="Permalink to this definition">¶</a>  
boolean Should we log progress on the the first row read. *Only applies if Table is used as a source.* (inherited from ETLComponent)

 `max_rows`<a href="#bi_etl.components.csvreader.CSVReader.max_rows" class="headerlink" title="Permalink to this definition">¶</a>  
int, optional The maximum number of rows to read. *Only applies if Table is used as a source.* (inherited from ETLComponent)

 `primary_key`  
list The name of the primary key column(s). Only impacts trace messages. Default=None. (inherited from ETLComponent)

 `progress_frequency`<a href="#bi_etl.components.csvreader.CSVReader.progress_frequency" class="headerlink" title="Permalink to this definition">¶</a>  
int How often (in seconds) to output progress messages. None for no progress messages. (inherited from ETLComponent)

 `progress_message`<a href="#bi_etl.components.csvreader.CSVReader.progress_message" class="headerlink" title="Permalink to this definition">¶</a>  
str The progress message to print. Default is `"{logical_name} row # {row_number}"`. Note `logical_name` and `row_number` subs. (inherited from ETLComponent)

 `restkey`<a href="#bi_etl.components.csvreader.CSVReader.restkey" class="headerlink" title="Permalink to this definition">¶</a>  
str Column name to catch long rows (extra values).

 `restval`<a href="#bi_etl.components.csvreader.CSVReader.restval" class="headerlink" title="Permalink to this definition">¶</a>  
str The value to put in columns that are in the column\_names but not present in a given row (missing values).

 `large_field_support`<a href="#bi_etl.components.csvreader.CSVReader.large_field_support" class="headerlink" title="Permalink to this definition">¶</a>  
boolean Enable support for csv columns bigger than 131,072 default limit.

 `DEFAULT_PROGRESS_FREQUENCY` *= 10*<a href="#bi_etl.components.csvreader.CSVReader.DEFAULT_PROGRESS_FREQUENCY" class="headerlink" title="Permalink to this definition">¶</a>  

 `DEFAULT_PROGRESS_MESSAGE` *= '{logical\_name} current row \# {row\_number:,}'*<a href="#bi_etl.components.csvreader.CSVReader.DEFAULT_PROGRESS_MESSAGE" class="headerlink" title="Permalink to this definition">¶</a>  

 `Row`<span class="sig-paren">(</span>*data=None*, *logical\_name=None*, *iteration\_header=None*<span class="sig-paren">)</span><a href="#bi_etl.components.csvreader.CSVReader.Row" class="headerlink" title="Permalink to this definition">¶</a>  
Make a new empty row with this components structure.

 `add_stats_entry`<span class="sig-paren">(</span>*stats\_id*, *stats\_entry*, *parent\_stats=None*<span class="sig-paren">)</span><a href="#bi_etl.components.csvreader.CSVReader.add_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `check_row_limit`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.components.csvreader.CSVReader.check_row_limit" class="headerlink" title="Permalink to this definition">¶</a>  

 `clear_statistics`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.components.csvreader.CSVReader.clear_statistics" class="headerlink" title="Permalink to this definition">¶</a>  

 `close`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/csvreader.md#CSVReader.close" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.csvreader.CSVReader.close" class="headerlink" title="Permalink to this definition">¶</a>  
Close the file

 `column_names`  
Column names

 `debug_log`<span class="sig-paren">(</span>*state=True*<span class="sig-paren">)</span><a href="#bi_etl.components.csvreader.CSVReader.debug_log" class="headerlink" title="Permalink to this definition">¶</a>  

 `generate_iteration_header`<span class="sig-paren">(</span>*logical\_name=None*<span class="sig-paren">)</span><a href="#bi_etl.components.csvreader.CSVReader.generate_iteration_header" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_stats_entry`<span class="sig-paren">(</span>*stats\_id: str*, *parent\_stats: bi\_etl.statistics.Statistics = None*, *print\_start\_stop\_times: bool = None*<span class="sig-paren">)</span><a href="#bi_etl.components.csvreader.CSVReader.get_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_unique_stats_entry`<span class="sig-paren">(</span>*stats\_id*, *parent\_stats=None*, *print\_start\_stop\_times=None*<span class="sig-paren">)</span><a href="#bi_etl.components.csvreader.CSVReader.get_unique_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `iter_result`<span class="sig-paren">(</span>*result\_list: object*, *where\_dict: dict = None*, *progress\_frequency: int = None*, *stats\_id: str = None*, *parent\_stats: bi\_etl.statistics.Statistics = None*<span class="sig-paren">)</span> → typing.Iterable\[bi\_etl.components.row.row.Row\]<a href="#bi_etl.components.csvreader.CSVReader.iter_result" class="headerlink" title="Permalink to this definition">¶</a>  
|         |                            |
|---------|----------------------------|
| Yields: | **row** (`Row`) – next row |

 `line_num`<a href="#bi_etl.components.csvreader.CSVReader.line_num" class="headerlink" title="Permalink to this definition">¶</a>  
The current line number in the source file. line\_num differs from rows\_read in that rows\_read deals with rows that would be returned to the caller

 `log_progress`<span class="sig-paren">(</span>*row: bi\_etl.components.row.row.Row*, *stats*<span class="sig-paren">)</span><a href="#bi_etl.components.csvreader.CSVReader.log_progress" class="headerlink" title="Permalink to this definition">¶</a>  

 `primary_key`  

 `process_messages`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.components.csvreader.CSVReader.process_messages" class="headerlink" title="Permalink to this definition">¶</a>  
Processes messages for this components task. Should be called somewhere in any row looping. The standard iterator does this for you.

 `progress_frequency`  

 `reader`<a href="#bi_etl.components.csvreader.CSVReader.reader" class="headerlink" title="Permalink to this definition">¶</a>  
Build or get the csv.reader object.

 `row_name`<a href="#bi_etl.components.csvreader.CSVReader.row_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `rows_read`<a href="#bi_etl.components.csvreader.CSVReader.rows_read" class="headerlink" title="Permalink to this definition">¶</a>  
int The number of rows read and returned.

 `seek_row`<span class="sig-paren">(</span>*target\_row*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/csvreader.md#CSVReader.seek_row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.csvreader.CSVReader.seek_row" class="headerlink" title="Permalink to this definition">¶</a>  

 `set_kwattrs`<span class="sig-paren">(</span>*\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.components.csvreader.CSVReader.set_kwattrs" class="headerlink" title="Permalink to this definition">¶</a>  

 `statistics`<a href="#bi_etl.components.csvreader.CSVReader.statistics" class="headerlink" title="Permalink to this definition">¶</a>  

 `trace_data`<a href="#bi_etl.components.csvreader.CSVReader.trace_data" class="headerlink" title="Permalink to this definition">¶</a>  
boolean Should a debug message be printed with the parsed contents (as columns) of each row.

 `where`<span class="sig-paren">(</span>*criteria=None*, *order\_by=None*, *stats\_id=None*, *parent\_stats=None*<span class="sig-paren">)</span> → typing.Iterable\[bi\_etl.components.row.row.Row\]<a href="#bi_etl.components.csvreader.CSVReader.where" class="headerlink" title="Permalink to this definition">¶</a>  

#### Previous topic

[bi\_etl.components.row.row\_status module](bi_etl.components.row.row_status.md "previous chapter")

#### Next topic

[bi\_etl.components.data\_analyzer module](bi_etl.components.data_analyzer.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.components.data_analyzer.md "bi_etl.components.data_analyzer module") |
-   [previous](bi_etl.components.row.row_status.md "bi_etl.components.row.row_status module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.components package](bi_etl.components.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
