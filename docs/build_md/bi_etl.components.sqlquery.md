### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.components.table.md "bi_etl.components.table module") |
-   [previous](bi_etl.components.readonlytable.md "bi_etl.components.readonlytable module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.components package](bi_etl.components.md) »

<span id="bi-etl-components-sqlquery-module"></span>
bi\_etl.components.sqlquery module<a href="#module-bi_etl.components.sqlquery" class="headerlink" title="Permalink to this headline">¶</a>
==========================================================================================================================================

Created on Sep 17, 2014

@author: woodd

 *class* `bi_etl.components.sqlquery.``SQLQuery`<span class="sig-paren">(</span>*task*, *database*, *sql*, *logical\_name=None*, *\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/sqlquery.md#SQLQuery" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.sqlquery.SQLQuery" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="bi_etl.components.etlcomponent.md#bi_etl.components.etlcomponent.ETLComponent" class="reference internal" title="bi_etl.components.etlcomponent.ETLComponent"><code class="xref py py-class docutils literal">bi_etl.components.etlcomponent.ETLComponent</code></a>

A class for reading an arbitrary SQL statement. Consider using sqlalchemy.sql.text to wrap the SQL. <a href="http://docs.sqlalchemy.org/en/latest/core/tutorial.md#using-text" class="uri" class="reference external">http://docs.sqlalchemy.org/en/latest/core/tutorial.md#using-text</a>

 `DEFAULT_PROGRESS_FREQUENCY` *= 10*<a href="#bi_etl.components.sqlquery.SQLQuery.DEFAULT_PROGRESS_FREQUENCY" class="headerlink" title="Permalink to this definition">¶</a>  

 `DEFAULT_PROGRESS_MESSAGE` *= '{logical\_name} current row \# {row\_number:,}'*<a href="#bi_etl.components.sqlquery.SQLQuery.DEFAULT_PROGRESS_MESSAGE" class="headerlink" title="Permalink to this definition">¶</a>  

 `Row`<span class="sig-paren">(</span>*data=None*, *logical\_name=None*, *iteration\_header=None*<span class="sig-paren">)</span><a href="#bi_etl.components.sqlquery.SQLQuery.Row" class="headerlink" title="Permalink to this definition">¶</a>  
Make a new empty row with this components structure.

 `add_stats_entry`<span class="sig-paren">(</span>*stats\_id*, *stats\_entry*, *parent\_stats=None*<span class="sig-paren">)</span><a href="#bi_etl.components.sqlquery.SQLQuery.add_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `check_row_limit`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.components.sqlquery.SQLQuery.check_row_limit" class="headerlink" title="Permalink to this definition">¶</a>  

 `clear_statistics`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.components.sqlquery.SQLQuery.clear_statistics" class="headerlink" title="Permalink to this definition">¶</a>  

 `close`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.components.sqlquery.SQLQuery.close" class="headerlink" title="Permalink to this definition">¶</a>  

 `column_names`<a href="#bi_etl.components.sqlquery.SQLQuery.column_names" class="headerlink" title="Permalink to this definition">¶</a>  
Column names

 `debug_log`<span class="sig-paren">(</span>*state=True*<span class="sig-paren">)</span><a href="#bi_etl.components.sqlquery.SQLQuery.debug_log" class="headerlink" title="Permalink to this definition">¶</a>  

 `generate_iteration_header`<span class="sig-paren">(</span>*logical\_name=None*<span class="sig-paren">)</span><a href="#bi_etl.components.sqlquery.SQLQuery.generate_iteration_header" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_stats_entry`<span class="sig-paren">(</span>*stats\_id: str*, *parent\_stats: bi\_etl.statistics.Statistics = None*, *print\_start\_stop\_times: bool = None*<span class="sig-paren">)</span><a href="#bi_etl.components.sqlquery.SQLQuery.get_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_unique_stats_entry`<span class="sig-paren">(</span>*stats\_id*, *parent\_stats=None*, *print\_start\_stop\_times=None*<span class="sig-paren">)</span><a href="#bi_etl.components.sqlquery.SQLQuery.get_unique_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `iter_result`<span class="sig-paren">(</span>*result\_list: object*, *where\_dict: dict = None*, *progress\_frequency: int = None*, *stats\_id: str = None*, *parent\_stats: bi\_etl.statistics.Statistics = None*<span class="sig-paren">)</span> → typing.Iterable\[bi\_etl.components.row.row.Row\]<a href="#bi_etl.components.sqlquery.SQLQuery.iter_result" class="headerlink" title="Permalink to this definition">¶</a>  
|         |                            |
|---------|----------------------------|
| Yields: | **row** (`Row`) – next row |

 `log_progress`<span class="sig-paren">(</span>*row: bi\_etl.components.row.row.Row*, *stats*<span class="sig-paren">)</span><a href="#bi_etl.components.sqlquery.SQLQuery.log_progress" class="headerlink" title="Permalink to this definition">¶</a>  

 `primary_key`<a href="#bi_etl.components.sqlquery.SQLQuery.primary_key" class="headerlink" title="Permalink to this definition">¶</a>  

 `process_messages`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.components.sqlquery.SQLQuery.process_messages" class="headerlink" title="Permalink to this definition">¶</a>  
Processes messages for this components task. Should be called somewhere in any row looping. The standard iterator does this for you.

 `progress_frequency`<a href="#bi_etl.components.sqlquery.SQLQuery.progress_frequency" class="headerlink" title="Permalink to this definition">¶</a>  

 `row_name`<a href="#bi_etl.components.sqlquery.SQLQuery.row_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `rows_read`<a href="#bi_etl.components.sqlquery.SQLQuery.rows_read" class="headerlink" title="Permalink to this definition">¶</a>  
int The number of rows read and returned.

 `run_parameters`<span class="sig-paren">(</span>*\*\*parameters*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/sqlquery.md#SQLQuery.run_parameters" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.sqlquery.SQLQuery.run_parameters" class="headerlink" title="Permalink to this definition">¶</a>  
Run the SQL providing optional bind parameters. (:param in the SQL)

 `run_substitute`<span class="sig-paren">(</span>*\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/sqlquery.md#SQLQuery.run_substitute" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.sqlquery.SQLQuery.run_substitute" class="headerlink" title="Permalink to this definition">¶</a>  
Uses Python string formatting like {} or {name} to build a SQL string. Can be used to dynamically change the structure of the SQL, compared to bind variables which are more limited but faster.

 `set_kwattrs`<span class="sig-paren">(</span>*\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.components.sqlquery.SQLQuery.set_kwattrs" class="headerlink" title="Permalink to this definition">¶</a>  

 `statistics`<a href="#bi_etl.components.sqlquery.SQLQuery.statistics" class="headerlink" title="Permalink to this definition">¶</a>  

 `trace_data`<a href="#bi_etl.components.sqlquery.SQLQuery.trace_data" class="headerlink" title="Permalink to this definition">¶</a>  
boolean Should a debug message be printed with the parsed contents (as columns) of each row.

 `where`<span class="sig-paren">(</span>*criteria=None*, *order\_by=None*, *stats\_id=None*, *parent\_stats=None*<span class="sig-paren">)</span> → typing.Iterable\[bi\_etl.components.row.row.Row\]<a href="#bi_etl.components.sqlquery.SQLQuery.where" class="headerlink" title="Permalink to this definition">¶</a>  

#### Previous topic

[bi\_etl.components.readonlytable module](bi_etl.components.readonlytable.md "previous chapter")

#### Next topic

[bi\_etl.components.table module](bi_etl.components.table.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.components.table.md "bi_etl.components.table module") |
-   [previous](bi_etl.components.readonlytable.md "bi_etl.components.readonlytable module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.components package](bi_etl.components.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
