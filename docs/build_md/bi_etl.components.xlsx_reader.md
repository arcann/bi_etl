### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.database.md "bi_etl.database package") |
-   [previous](bi_etl.components.table.md "bi_etl.components.table module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.components package](bi_etl.components.md) »

<span id="bi-etl-components-xlsx-reader-module"></span>
bi\_etl.components.xlsx\_reader module<a href="#module-bi_etl.components.xlsx_reader" class="headerlink" title="Permalink to this headline">¶</a>
=================================================================================================================================================

Created on Apr 2, 2015

@author: woodd

 *class* `bi_etl.components.xlsx_reader.``XLSXReader`<span class="sig-paren">(</span>*task*, *file\_name*, *logical\_name=None*, *\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/xlsx_reader.md#XLSXReader" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.xlsx_reader.XLSXReader" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="bi_etl.components.etlcomponent.md#bi_etl.components.etlcomponent.ETLComponent" class="reference internal" title="bi_etl.components.etlcomponent.ETLComponent"><code class="xref py py-class docutils literal">bi_etl.components.etlcomponent.ETLComponent</code></a>

XLSXReader will read rows from an Microsoft Excel XLSX formatted sheet.

|             |                                                                                                                                                                                                                       |
|-------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **task** (<a href="bi_etl.scheduler.task.md#bi_etl.scheduler.task.ETLTask" class="reference internal" title="bi_etl.scheduler.task.ETLTask"><em>ETLTask</em></a>) – The instance to register in (if not None)   
  -   **file\_name** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The file\_name to parse as xlsx.                            
  -   **logical\_name** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The logical name of this source. Used for log messages.  |

 `column_names`<a href="#bi_etl.components.xlsx_reader.XLSXReader.column_names" class="headerlink" title="Permalink to this definition">¶</a>  
*list* – The names to use for columns

 `header_row`<a href="#bi_etl.components.xlsx_reader.XLSXReader.header_row" class="headerlink" title="Permalink to this definition">¶</a>  
*int* – The sheet row to read headers from. Default = 1.

 `start_row`<a href="#bi_etl.components.xlsx_reader.XLSXReader.start_row" class="headerlink" title="Permalink to this definition">¶</a>  
*int* – The first row to parse for data. Default = header\_row + 1

 `workbook`<a href="#bi_etl.components.xlsx_reader.XLSXReader.workbook" class="headerlink" title="Permalink to this definition">¶</a>  
`openpyxl.workbook.workbook.Workbook` – The workbook that was opened.

 `log_first_row`<a href="#bi_etl.components.xlsx_reader.XLSXReader.log_first_row" class="headerlink" title="Permalink to this definition">¶</a>  
*boolean* – Should we log progress on the the first row read. *Only applies if Table is used as a source.* (inherited from ETLComponent)

 `max_rows`<a href="#bi_etl.components.xlsx_reader.XLSXReader.max_rows" class="headerlink" title="Permalink to this definition">¶</a>  
*int, optional* – The maximum number of rows to read. *Only applies if Table is used as a source.* (inherited from ETLComponent)

 `primary_key`<a href="#bi_etl.components.xlsx_reader.XLSXReader.primary_key" class="headerlink" title="Permalink to this definition">¶</a>  
*list* – The name of the primary key column(s). Only impacts trace messages. Default=None. (inherited from ETLComponent)

 `progress_frequency`<a href="#bi_etl.components.xlsx_reader.XLSXReader.progress_frequency" class="headerlink" title="Permalink to this definition">¶</a>  
*int* – How often (in seconds) to output progress messages. None for no progress messages. (inherited from ETLComponent)

 `progress_message`<a href="#bi_etl.components.xlsx_reader.XLSXReader.progress_message" class="headerlink" title="Permalink to this definition">¶</a>  
*str* – The progress message to print. Default is `"{logical_name} row # {row_number}"`. Note `logical_name` and `row_number` subs. (inherited from ETLComponent)

 `restkey`<a href="#bi_etl.components.xlsx_reader.XLSXReader.restkey" class="headerlink" title="Permalink to this definition">¶</a>  
*str* – Column name to catch long rows (extra values).

 `restval`<a href="#bi_etl.components.xlsx_reader.XLSXReader.restval" class="headerlink" title="Permalink to this definition">¶</a>  
*str* – The value to put in columns that are in the column\_names but not present in a given row (missing values).

 `DEFAULT_PROGRESS_FREQUENCY` *= 10*<a href="#bi_etl.components.xlsx_reader.XLSXReader.DEFAULT_PROGRESS_FREQUENCY" class="headerlink" title="Permalink to this definition">¶</a>  

 `DEFAULT_PROGRESS_MESSAGE` *= '{logical\_name} current row \# {row\_number:,}'*<a href="#bi_etl.components.xlsx_reader.XLSXReader.DEFAULT_PROGRESS_MESSAGE" class="headerlink" title="Permalink to this definition">¶</a>  

 `Row`<span class="sig-paren">(</span>*data=None*, *logical\_name=None*, *iteration\_header=None*<span class="sig-paren">)</span><a href="#bi_etl.components.xlsx_reader.XLSXReader.Row" class="headerlink" title="Permalink to this definition">¶</a>  
Make a new empty row with this components structure.

 `active_worksheet`<a href="#bi_etl.components.xlsx_reader.XLSXReader.active_worksheet" class="headerlink" title="Permalink to this definition">¶</a>  

 `add_stats_entry`<span class="sig-paren">(</span>*stats\_id*, *stats\_entry*, *parent\_stats=None*<span class="sig-paren">)</span><a href="#bi_etl.components.xlsx_reader.XLSXReader.add_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `check_row_limit`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.components.xlsx_reader.XLSXReader.check_row_limit" class="headerlink" title="Permalink to this definition">¶</a>  

 `clear_statistics`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.components.xlsx_reader.XLSXReader.clear_statistics" class="headerlink" title="Permalink to this definition">¶</a>  

 `close`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/xlsx_reader.md#XLSXReader.close" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.xlsx_reader.XLSXReader.close" class="headerlink" title="Permalink to this definition">¶</a>  

 `column_names`  
Column names

 `debug_log`<span class="sig-paren">(</span>*state=True*<span class="sig-paren">)</span><a href="#bi_etl.components.xlsx_reader.XLSXReader.debug_log" class="headerlink" title="Permalink to this definition">¶</a>  

 `generate_iteration_header`<span class="sig-paren">(</span>*logical\_name=None*<span class="sig-paren">)</span><a href="#bi_etl.components.xlsx_reader.XLSXReader.generate_iteration_header" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_sheet_by_name`<span class="sig-paren">(</span>*name*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/xlsx_reader.md#XLSXReader.get_sheet_by_name" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.xlsx_reader.XLSXReader.get_sheet_by_name" class="headerlink" title="Permalink to this definition">¶</a>  
Returns a worksheet by its name.

|              |                                                                                                                                                                                        |
|--------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters:  | **name** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The name of the worksheet to look for |
| Returns:     | Worksheet object, or None if no worksheet has the name specified.                                                                                                                      |
| Return type: | openpyxl.worksheet.worksheet.Worksheet                                                                                                                                                 |

 `get_sheet_names`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/xlsx_reader.md#XLSXReader.get_sheet_names" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.xlsx_reader.XLSXReader.get_sheet_names" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_stats_entry`<span class="sig-paren">(</span>*stats\_id: str*, *parent\_stats: bi\_etl.statistics.Statistics = None*, *print\_start\_stop\_times: bool = None*<span class="sig-paren">)</span><a href="#bi_etl.components.xlsx_reader.XLSXReader.get_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_unique_stats_entry`<span class="sig-paren">(</span>*stats\_id*, *parent\_stats=None*, *print\_start\_stop\_times=None*<span class="sig-paren">)</span><a href="#bi_etl.components.xlsx_reader.XLSXReader.get_unique_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `header_row`  
int The sheet row to read headers from. Default = 1.

 `iter_result`<span class="sig-paren">(</span>*result\_list: object*, *where\_dict: dict = None*, *progress\_frequency: int = None*, *stats\_id: str = None*, *parent\_stats: bi\_etl.statistics.Statistics = None*<span class="sig-paren">)</span> → typing.Iterable\[bi\_etl.components.row.row.Row\]<a href="#bi_etl.components.xlsx_reader.XLSXReader.iter_result" class="headerlink" title="Permalink to this definition">¶</a>  
|         |                            |
|---------|----------------------------|
| Yields: | **row** (`Row`) – next row |

 `line_num`<a href="#bi_etl.components.xlsx_reader.XLSXReader.line_num" class="headerlink" title="Permalink to this definition">¶</a>  
The current line number in the source file. line\_num differs from rows\_read in that rows\_read deals with rows that would be returned to the caller

 `log_progress`<span class="sig-paren">(</span>*row: bi\_etl.components.row.row.Row*, *stats*<span class="sig-paren">)</span><a href="#bi_etl.components.xlsx_reader.XLSXReader.log_progress" class="headerlink" title="Permalink to this definition">¶</a>  

 `primary_key`  

 `process_messages`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.components.xlsx_reader.XLSXReader.process_messages" class="headerlink" title="Permalink to this definition">¶</a>  
Processes messages for this components task. Should be called somewhere in any row looping. The standard iterator does this for you.

 `progress_frequency`  

 `read_header_row`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/xlsx_reader.md#XLSXReader.read_header_row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.xlsx_reader.XLSXReader.read_header_row" class="headerlink" title="Permalink to this definition">¶</a>  

 `row_name`<a href="#bi_etl.components.xlsx_reader.XLSXReader.row_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `rows_read`<a href="#bi_etl.components.xlsx_reader.XLSXReader.rows_read" class="headerlink" title="Permalink to this definition">¶</a>  
int The number of rows read and returned.

 `set_active_worksheet_by_name`<span class="sig-paren">(</span>*sheet\_name*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/xlsx_reader.md#XLSXReader.set_active_worksheet_by_name" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.xlsx_reader.XLSXReader.set_active_worksheet_by_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `set_active_worksheet_by_number`<span class="sig-paren">(</span>*sheet\_number*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/xlsx_reader.md#XLSXReader.set_active_worksheet_by_number" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.xlsx_reader.XLSXReader.set_active_worksheet_by_number" class="headerlink" title="Permalink to this definition">¶</a>  

 `set_kwattrs`<span class="sig-paren">(</span>*\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.components.xlsx_reader.XLSXReader.set_kwattrs" class="headerlink" title="Permalink to this definition">¶</a>  

 `start_row`  
int The sheet row to start reading data from. Default = header\_row + 1

 `statistics`<a href="#bi_etl.components.xlsx_reader.XLSXReader.statistics" class="headerlink" title="Permalink to this definition">¶</a>  

 `trace_data`<a href="#bi_etl.components.xlsx_reader.XLSXReader.trace_data" class="headerlink" title="Permalink to this definition">¶</a>  
boolean Should a debug message be printed with the parsed contents (as columns) of each row.

 `where`<span class="sig-paren">(</span>*criteria=None*, *order\_by=None*, *stats\_id=None*, *parent\_stats=None*<span class="sig-paren">)</span> → typing.Iterable\[bi\_etl.components.row.row.Row\]<a href="#bi_etl.components.xlsx_reader.XLSXReader.where" class="headerlink" title="Permalink to this definition">¶</a>  

 `workbook`  

#### Previous topic

[bi\_etl.components.table module](bi_etl.components.table.md "previous chapter")

#### Next topic

[bi\_etl.database package](bi_etl.database.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.database.md "bi_etl.database package") |
-   [previous](bi_etl.components.table.md "bi_etl.components.table module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.components package](bi_etl.components.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
