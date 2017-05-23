### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.components.etlcomponent.md "bi_etl.components.etlcomponent module") |
-   [previous](bi_etl.components.csvreader.md "bi_etl.components.csvreader module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.components package](bi_etl.components.md) »

<span id="bi-etl-components-data-analyzer-module"></span>
bi\_etl.components.data\_analyzer module<a href="#module-bi_etl.components.data_analyzer" class="headerlink" title="Permalink to this headline">¶</a>
=====================================================================================================================================================

Created on Oct 9, 2015

@author: woodd

 *class* `bi_etl.components.data_analyzer.``DataAnalyzer`<span class="sig-paren">(</span>*task=None*, *logical\_name='DataAnalyzer'*, *\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/data_analyzer.md#DataAnalyzer" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.data_analyzer.DataAnalyzer" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="bi_etl.components.etlcomponent.md#bi_etl.components.etlcomponent.ETLComponent" class="reference internal" title="bi_etl.components.etlcomponent.ETLComponent"><code class="xref py py-class docutils literal">bi_etl.components.etlcomponent.ETLComponent</code></a>

Class that analyzes the data rows passed to it. \* Tracks distinct columns passed in \* Tracks datatype of each column \* Tracks valid values of each column

|             |                                                                                                                                                                                                                       |
|-------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **task** (<a href="bi_etl.scheduler.task.md#bi_etl.scheduler.task.ETLTask" class="reference internal" title="bi_etl.scheduler.task.ETLTask"><em>ETLTask</em></a>) – The instance to register in (if not None)   
  -   **logical\_name** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The logical name of this source. Used for log messages.  |

 `DEFAULT_FORMAT` *= '{col:30} type = {type:20} non\_null\_rows={non\_null\_rows:15,} cardinality={cardinality:15,}{msg}'*<a href="#bi_etl.components.data_analyzer.DataAnalyzer.DEFAULT_FORMAT" class="headerlink" title="Permalink to this definition">¶</a>  

 `DEFAULT_PROGRESS_FREQUENCY` *= 10*<a href="#bi_etl.components.data_analyzer.DataAnalyzer.DEFAULT_PROGRESS_FREQUENCY" class="headerlink" title="Permalink to this definition">¶</a>  

 `DEFAULT_PROGRESS_MESSAGE` *= '{logical\_name} current row \# {row\_number:,}'*<a href="#bi_etl.components.data_analyzer.DataAnalyzer.DEFAULT_PROGRESS_MESSAGE" class="headerlink" title="Permalink to this definition">¶</a>  

 *class* `DataType`<span class="sig-paren">(</span>*name*, *length=None*, *precision=None*, *fmt=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/data_analyzer.md#DataAnalyzer.DataType" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.data_analyzer.DataAnalyzer.DataType" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="https://docs.python.org/2/library/functions.md#object" class="reference external" title="(in Python v2.7)"><code class="xref py py-class docutils literal">object</code></a>

 `PIPE_FORMAT` *= '{col}|{type}|{present}|{not\_present\_on\_rows}|{non\_null\_rows}|{cardinality}|{most\_common\_value}|{msg}'*<a href="#bi_etl.components.data_analyzer.DataAnalyzer.PIPE_FORMAT" class="headerlink" title="Permalink to this definition">¶</a>  

 `Row`<span class="sig-paren">(</span>*data=None*, *logical\_name=None*, *iteration\_header=None*<span class="sig-paren">)</span><a href="#bi_etl.components.data_analyzer.DataAnalyzer.Row" class="headerlink" title="Permalink to this definition">¶</a>  
Make a new empty row with this components structure.

 `add_stats_entry`<span class="sig-paren">(</span>*stats\_id*, *stats\_entry*, *parent\_stats=None*<span class="sig-paren">)</span><a href="#bi_etl.components.data_analyzer.DataAnalyzer.add_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `analyze_column`<span class="sig-paren">(</span>*column\_name*, *column\_value*, *column\_number=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/data_analyzer.md#DataAnalyzer.analyze_column" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.data_analyzer.DataAnalyzer.analyze_column" class="headerlink" title="Permalink to this definition">¶</a>  

 `analyze_row`<span class="sig-paren">(</span>*row*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/data_analyzer.md#DataAnalyzer.analyze_row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.data_analyzer.DataAnalyzer.analyze_row" class="headerlink" title="Permalink to this definition">¶</a>  
Analyze the data row passed in. Call this for all the rows that should be analyzed.

 `check_row_limit`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.components.data_analyzer.DataAnalyzer.check_row_limit" class="headerlink" title="Permalink to this definition">¶</a>  

 `clear_statistics`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.components.data_analyzer.DataAnalyzer.clear_statistics" class="headerlink" title="Permalink to this definition">¶</a>  

 `close`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/data_analyzer.md#DataAnalyzer.close" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.data_analyzer.DataAnalyzer.close" class="headerlink" title="Permalink to this definition">¶</a>  

 `column_names`<a href="#bi_etl.components.data_analyzer.DataAnalyzer.column_names" class="headerlink" title="Permalink to this definition">¶</a>  
Column names

 `debug_log`<span class="sig-paren">(</span>*state=True*<span class="sig-paren">)</span><a href="#bi_etl.components.data_analyzer.DataAnalyzer.debug_log" class="headerlink" title="Permalink to this definition">¶</a>  

 `generate_iteration_header`<span class="sig-paren">(</span>*logical\_name=None*<span class="sig-paren">)</span><a href="#bi_etl.components.data_analyzer.DataAnalyzer.generate_iteration_header" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_stats_entry`<span class="sig-paren">(</span>*stats\_id: str*, *parent\_stats: bi\_etl.statistics.Statistics = None*, *print\_start\_stop\_times: bool = None*<span class="sig-paren">)</span><a href="#bi_etl.components.data_analyzer.DataAnalyzer.get_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_unique_stats_entry`<span class="sig-paren">(</span>*stats\_id*, *parent\_stats=None*, *print\_start\_stop\_times=None*<span class="sig-paren">)</span><a href="#bi_etl.components.data_analyzer.DataAnalyzer.get_unique_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `iter_result`<span class="sig-paren">(</span>*result\_list: object*, *where\_dict: dict = None*, *progress\_frequency: int = None*, *stats\_id: str = None*, *parent\_stats: bi\_etl.statistics.Statistics = None*<span class="sig-paren">)</span> → typing.Iterable\[bi\_etl.components.row.row.Row\]<a href="#bi_etl.components.data_analyzer.DataAnalyzer.iter_result" class="headerlink" title="Permalink to this definition">¶</a>  
|         |                            |
|---------|----------------------------|
| Yields: | **row** (`Row`) – next row |

 `log_progress`<span class="sig-paren">(</span>*row: bi\_etl.components.row.row.Row*, *stats*<span class="sig-paren">)</span><a href="#bi_etl.components.data_analyzer.DataAnalyzer.log_progress" class="headerlink" title="Permalink to this definition">¶</a>  

 `next_row`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/data_analyzer.md#DataAnalyzer.next_row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.data_analyzer.DataAnalyzer.next_row" class="headerlink" title="Permalink to this definition">¶</a>  

 `primary_key`<a href="#bi_etl.components.data_analyzer.DataAnalyzer.primary_key" class="headerlink" title="Permalink to this definition">¶</a>  

 `print_analysis`<span class="sig-paren">(</span>*out: io.TextIOBase = None*, *valid\_value\_limit: int = 10*, *out\_fmt: str = '{col:30} type = {type:20} non\_null\_rows={non\_null\_rows:15*, *} cardinality={cardinality:15*, *}{msg}'*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/data_analyzer.md#DataAnalyzer.print_analysis" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.data_analyzer.DataAnalyzer.print_analysis" class="headerlink" title="Permalink to this definition">¶</a>  
Print the data analysis results.

|             |                                                                                                                                            |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **out** – The File to write the results to. Default=\`\`stdout\`\` valid\_value\_limit (int): How many valid values should be printed. 
  -   **valid\_value\_limit** – The number of valid values to output                                                                          
  -   **out\_fmt** – The format to use for lines                                                                                              |

 `process_messages`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.components.data_analyzer.DataAnalyzer.process_messages" class="headerlink" title="Permalink to this definition">¶</a>  
Processes messages for this components task. Should be called somewhere in any row looping. The standard iterator does this for you.

 `progress_frequency`<a href="#bi_etl.components.data_analyzer.DataAnalyzer.progress_frequency" class="headerlink" title="Permalink to this definition">¶</a>  

 `row_name`<a href="#bi_etl.components.data_analyzer.DataAnalyzer.row_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `rows_read`<a href="#bi_etl.components.data_analyzer.DataAnalyzer.rows_read" class="headerlink" title="Permalink to this definition">¶</a>  
int The number of rows read and returned.

 `set_kwattrs`<span class="sig-paren">(</span>*\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.components.data_analyzer.DataAnalyzer.set_kwattrs" class="headerlink" title="Permalink to this definition">¶</a>  

 `statistics`<a href="#bi_etl.components.data_analyzer.DataAnalyzer.statistics" class="headerlink" title="Permalink to this definition">¶</a>  

 `trace_data`<a href="#bi_etl.components.data_analyzer.DataAnalyzer.trace_data" class="headerlink" title="Permalink to this definition">¶</a>  
boolean Should a debug message be printed with the parsed contents (as columns) of each row.

 `where`<span class="sig-paren">(</span>*criteria=None*, *order\_by=None*, *stats\_id=None*, *parent\_stats=None*<span class="sig-paren">)</span> → typing.Iterable\[bi\_etl.components.row.row.Row\]<a href="#bi_etl.components.data_analyzer.DataAnalyzer.where" class="headerlink" title="Permalink to this definition">¶</a>  

#### Previous topic

[bi\_etl.components.csvreader module](bi_etl.components.csvreader.md "previous chapter")

#### Next topic

[bi\_etl.components.etlcomponent module](bi_etl.components.etlcomponent.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.components.etlcomponent.md "bi_etl.components.etlcomponent module") |
-   [previous](bi_etl.components.csvreader.md "bi_etl.components.csvreader module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.components package](bi_etl.components.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
