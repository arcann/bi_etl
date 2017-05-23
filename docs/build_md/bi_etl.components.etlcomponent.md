### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.components.hst_table.md "bi_etl.components.hst_table module") |
-   [previous](bi_etl.components.data_analyzer.md "bi_etl.components.data_analyzer module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.components package](bi_etl.components.md) »

<span id="bi-etl-components-etlcomponent-module"></span>
bi\_etl.components.etlcomponent module<a href="#module-bi_etl.components.etlcomponent" class="headerlink" title="Permalink to this headline">¶</a>
==================================================================================================================================================

Created on Sep 25, 2014

@author: woodd

 *class* `bi_etl.components.etlcomponent.``ETLComponent`<span class="sig-paren">(</span>*task: bi\_etl.scheduler.task.ETLTask*, *logical\_name=None*, *\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/etlcomponent.md#ETLComponent" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.etlcomponent.ETLComponent" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: `typing.Iterable`

Base class for ETLComponents (readers, writers, etc)

|             |                                                                                                                                                                                                                       |
|-------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **task** (<a href="bi_etl.scheduler.task.md#bi_etl.scheduler.task.ETLTask" class="reference internal" title="bi_etl.scheduler.task.ETLTask"><em>ETLTask</em></a>) – The instance to register in (if not None)   
  -   **logical\_name** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The logical name of this source. Used for log messages.  |

 `log_first_row`<a href="#bi_etl.components.etlcomponent.ETLComponent.log_first_row" class="headerlink" title="Permalink to this definition">¶</a>  
*boolean* – Should we log progress on the the first row read. *Only applies if Table is used as a source.*

 `max_rows`<a href="#bi_etl.components.etlcomponent.ETLComponent.max_rows" class="headerlink" title="Permalink to this definition">¶</a>  
*int, optional* – The maximum number of rows to read. *Only applies if Table is used as a source.*

 `primary_key`<a href="#bi_etl.components.etlcomponent.ETLComponent.primary_key" class="headerlink" title="Permalink to this definition">¶</a>  
*list* – The name of the primary key column(s). Only impacts trace messages. Default=None.

 `progress_frequency`<a href="#bi_etl.components.etlcomponent.ETLComponent.progress_frequency" class="headerlink" title="Permalink to this definition">¶</a>  
*int* – How often (in seconds) to output progress messages. None for no progress messages.

 `progress_message`<a href="#bi_etl.components.etlcomponent.ETLComponent.progress_message" class="headerlink" title="Permalink to this definition">¶</a>  
*str* – The progress message to print. Default is `"{logical_name} row # {row_number}"`. Note `logical_name` and `row_number` subs.

 `DEFAULT_PROGRESS_FREQUENCY` *= 10*<a href="#bi_etl.components.etlcomponent.ETLComponent.DEFAULT_PROGRESS_FREQUENCY" class="headerlink" title="Permalink to this definition">¶</a>  

 `DEFAULT_PROGRESS_MESSAGE` *= '{logical\_name} current row \# {row\_number:,}'*<a href="#bi_etl.components.etlcomponent.ETLComponent.DEFAULT_PROGRESS_MESSAGE" class="headerlink" title="Permalink to this definition">¶</a>  

 `Row`<span class="sig-paren">(</span>*data=None*, *logical\_name=None*, *iteration\_header=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/etlcomponent.md#ETLComponent.Row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.etlcomponent.ETLComponent.Row" class="headerlink" title="Permalink to this definition">¶</a>  
Make a new empty row with this components structure.

 `add_stats_entry`<span class="sig-paren">(</span>*stats\_id*, *stats\_entry*, *parent\_stats=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/etlcomponent.md#ETLComponent.add_stats_entry" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.etlcomponent.ETLComponent.add_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `check_row_limit`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/etlcomponent.md#ETLComponent.check_row_limit" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.etlcomponent.ETLComponent.check_row_limit" class="headerlink" title="Permalink to this definition">¶</a>  

 `clear_statistics`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/etlcomponent.md#ETLComponent.clear_statistics" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.etlcomponent.ETLComponent.clear_statistics" class="headerlink" title="Permalink to this definition">¶</a>  

 `close`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/etlcomponent.md#ETLComponent.close" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.etlcomponent.ETLComponent.close" class="headerlink" title="Permalink to this definition">¶</a>  

 `column_names`<a href="#bi_etl.components.etlcomponent.ETLComponent.column_names" class="headerlink" title="Permalink to this definition">¶</a>  
Column names

 `debug_log`<span class="sig-paren">(</span>*state=True*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/etlcomponent.md#ETLComponent.debug_log" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.etlcomponent.ETLComponent.debug_log" class="headerlink" title="Permalink to this definition">¶</a>  

 `generate_iteration_header`<span class="sig-paren">(</span>*logical\_name=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/etlcomponent.md#ETLComponent.generate_iteration_header" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.etlcomponent.ETLComponent.generate_iteration_header" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_stats_entry`<span class="sig-paren">(</span>*stats\_id: str*, *parent\_stats: bi\_etl.statistics.Statistics = None*, *print\_start\_stop\_times: bool = None*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/etlcomponent.md#ETLComponent.get_stats_entry" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.etlcomponent.ETLComponent.get_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_unique_stats_entry`<span class="sig-paren">(</span>*stats\_id*, *parent\_stats=None*, *print\_start\_stop\_times=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/etlcomponent.md#ETLComponent.get_unique_stats_entry" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.etlcomponent.ETLComponent.get_unique_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `iter_result`<span class="sig-paren">(</span>*result\_list: object*, *where\_dict: dict = None*, *progress\_frequency: int = None*, *stats\_id: str = None*, *parent\_stats: bi\_etl.statistics.Statistics = None*<span class="sig-paren">)</span> → typing.Iterable\[bi\_etl.components.row.row.Row\]<a href="_modules/bi_etl/components/etlcomponent.md#ETLComponent.iter_result" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.etlcomponent.ETLComponent.iter_result" class="headerlink" title="Permalink to this definition">¶</a>  
|         |                            |
|---------|----------------------------|
| Yields: | **row** (`Row`) – next row |

 `log_progress`<span class="sig-paren">(</span>*row: bi\_etl.components.row.row.Row*, *stats*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/etlcomponent.md#ETLComponent.log_progress" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.etlcomponent.ETLComponent.log_progress" class="headerlink" title="Permalink to this definition">¶</a>  

 `primary_key`  

 `process_messages`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/etlcomponent.md#ETLComponent.process_messages" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.etlcomponent.ETLComponent.process_messages" class="headerlink" title="Permalink to this definition">¶</a>  
Processes messages for this components task. Should be called somewhere in any row looping. The standard iterator does this for you.

 `progress_frequency`  

 `row_name`<a href="#bi_etl.components.etlcomponent.ETLComponent.row_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `rows_read`<a href="#bi_etl.components.etlcomponent.ETLComponent.rows_read" class="headerlink" title="Permalink to this definition">¶</a>  
int The number of rows read and returned.

 `set_kwattrs`<span class="sig-paren">(</span>*\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/etlcomponent.md#ETLComponent.set_kwattrs" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.etlcomponent.ETLComponent.set_kwattrs" class="headerlink" title="Permalink to this definition">¶</a>  

 `statistics`<a href="#bi_etl.components.etlcomponent.ETLComponent.statistics" class="headerlink" title="Permalink to this definition">¶</a>  

 `trace_data`<a href="#bi_etl.components.etlcomponent.ETLComponent.trace_data" class="headerlink" title="Permalink to this definition">¶</a>  
boolean Should a debug message be printed with the parsed contents (as columns) of each row.

 `where`<span class="sig-paren">(</span>*criteria=None*, *order\_by=None*, *stats\_id=None*, *parent\_stats=None*<span class="sig-paren">)</span> → typing.Iterable\[bi\_etl.components.row.row.Row\]<a href="_modules/bi_etl/components/etlcomponent.md#ETLComponent.where" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.etlcomponent.ETLComponent.where" class="headerlink" title="Permalink to this definition">¶</a>  

#### Previous topic

[bi\_etl.components.data\_analyzer module](bi_etl.components.data_analyzer.md "previous chapter")

#### Next topic

[bi\_etl.components.hst\_table module](bi_etl.components.hst_table.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.components.hst_table.md "bi_etl.components.hst_table module") |
-   [previous](bi_etl.components.data_analyzer.md "bi_etl.components.data_analyzer module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.components package](bi_etl.components.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
