### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.components.row_package.md "bi_etl.components.row package") |
-   [previous](bi_etl.components.hst_table.md "bi_etl.components.hst_table module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.components package](bi_etl.components.md) »

<span id="bi-etl-components-readonlytable-module"></span>
bi\_etl.components.readonlytable module<a href="#module-bi_etl.components.readonlytable" class="headerlink" title="Permalink to this headline">¶</a>
====================================================================================================================================================

Created on Sep 17, 2014

@author: woodd

 *class* `bi_etl.components.readonlytable.``ReadOnlyTable`<span class="sig-paren">(</span>*task*, *database*, *table\_name*, *table\_name\_case\_sensitive=False*, *exclude\_columns=None*, *include\_only\_columns=None*, *\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="bi_etl.components.etlcomponent.md#bi_etl.components.etlcomponent.ETLComponent" class="reference internal" title="bi_etl.components.etlcomponent.ETLComponent"><code class="xref py py-class docutils literal">bi_etl.components.etlcomponent.ETLComponent</code></a>

Reads all columns from a database table or view. Rows can be filtered using the <a href="#bi_etl.components.readonlytable.ReadOnlyTable.where" class="reference internal" title="bi_etl.components.readonlytable.ReadOnlyTable.where"><code class="xref py py-meth docutils literal">where()</code></a> method.

|             |                                                                                                                                                                                                                     |
|-------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **task** (<a href="bi_etl.scheduler.task.md#bi_etl.scheduler.task.ETLTask" class="reference internal" title="bi_etl.scheduler.task.ETLTask"><em>ETLTask</em></a>) – The instance to register in (if not None) 
  -   **database** (*bi\_etl.scheduler.task.Database*) – The database to find the table/view in.                                                                                                                       
  -   **table\_name** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The name of the table/view.                              
  -   **include\_only\_columns** (*list,* *optional*) – Optional. A list of specific columns to include when reading the table/view. All other columns are excluded.                                                   
  -   **exclude\_columns** (*list,* *optional*) – Optional. A list of columns to exclude when reading the table/view.                                                                                                  |

 `delete_flag`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.delete_flag" class="headerlink" title="Permalink to this definition">¶</a>  
*str, optional* – The name of the delete\_flag column, if any.

 `delete_flag_yes`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.delete_flag_yes" class="headerlink" title="Permalink to this definition">¶</a>  
*str, optional* – The value of delete\_flag for deleted rows.

 `delete_flag_no`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.delete_flag_no" class="headerlink" title="Permalink to this definition">¶</a>  
*str, optional* – The value of delete\_flag for *not* deleted rows.

 `special_values_descriptive_columns`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.special_values_descriptive_columns" class="headerlink" title="Permalink to this definition">¶</a>  
*list, optional* – A list of columns that should get longer descriptive text (e.g. ‘Missing’ instead of ‘?’) in <a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_missing_row" class="reference internal" title="bi_etl.components.readonlytable.ReadOnlyTable.get_missing_row"><code class="xref py py-meth docutils literal">get_missing_row()</code></a>, <a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_invalid_row" class="reference internal" title="bi_etl.components.readonlytable.ReadOnlyTable.get_invalid_row"><code class="xref py py-meth docutils literal">get_invalid_row()</code></a>, <a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_not_applicable_row" class="reference internal" title="bi_etl.components.readonlytable.ReadOnlyTable.get_not_applicable_row"><code class="xref py py-meth docutils literal">get_not_applicable_row()</code></a>, <a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_various_row" class="reference internal" title="bi_etl.components.readonlytable.ReadOnlyTable.get_various_row"><code class="xref py py-meth docutils literal">get_various_row()</code></a>

 `log_first_row`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.log_first_row" class="headerlink" title="Permalink to this definition">¶</a>  
*boolean* – Should we log progress on the the first row read. *Only applies if Table is used as a source.* (inherited from ETLComponent)

 `max_rows`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.max_rows" class="headerlink" title="Permalink to this definition">¶</a>  
*int, optional* – The maximum number of rows to read. *Only applies if Table is used as a source.* (inherited from ETLComponent)

 `maintain_cache_during_load`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.maintain_cache_during_load" class="headerlink" title="Permalink to this definition">¶</a>  
*boolean* – Default = True. Should we maintain the lookup caches as we load records. Can safely be set to False for sources that will never use a key combination twice during a single load. Setting it to False should improve performance.

 `primary_key`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.primary_key" class="headerlink" title="Permalink to this definition">¶</a>  
*list* – The name of the primary key column(s). Only impacts trace messages. Default=None. If not passed in, will use the database value, if any. (inherited from ETLComponent)

 `natural_key`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.natural_key" class="headerlink" title="Permalink to this definition">¶</a>  
*list* – The list of natural key columns (as Column objects). Default is None

 `progress_frequency`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.progress_frequency" class="headerlink" title="Permalink to this definition">¶</a>  
*int* – How often (in seconds) to output progress messages. None for no progress messages. (inherited from ETLComponent)

 `progress_message`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.progress_message" class="headerlink" title="Permalink to this definition">¶</a>  
*str* – The progress message to print. Default is `"{logical_name} row # {row_number}"`. Note `logical_name` and `row_number` subs. (inherited from ETLComponent)

 `DEFAULT_PROGRESS_FREQUENCY` *= 10*<a href="#bi_etl.components.readonlytable.ReadOnlyTable.DEFAULT_PROGRESS_FREQUENCY" class="headerlink" title="Permalink to this definition">¶</a>  

 `DEFAULT_PROGRESS_MESSAGE` *= '{logical\_name} current row \# {row\_number:,}'*<a href="#bi_etl.components.readonlytable.ReadOnlyTable.DEFAULT_PROGRESS_MESSAGE" class="headerlink" title="Permalink to this definition">¶</a>  

 `NK_LOOKUP` *= 'NK'*<a href="#bi_etl.components.readonlytable.ReadOnlyTable.NK_LOOKUP" class="headerlink" title="Permalink to this definition">¶</a>  

 `PK_LOOKUP` *= 'PK'*<a href="#bi_etl.components.readonlytable.ReadOnlyTable.PK_LOOKUP" class="headerlink" title="Permalink to this definition">¶</a>  

 `Row`<span class="sig-paren">(</span>*data=None*, *logical\_name=None*, *iteration\_header=None*<span class="sig-paren">)</span><a href="#bi_etl.components.readonlytable.ReadOnlyTable.Row" class="headerlink" title="Permalink to this definition">¶</a>  
Make a new empty row with this components structure.

 `add_stats_entry`<span class="sig-paren">(</span>*stats\_id*, *stats\_entry*, *parent\_stats=None*<span class="sig-paren">)</span><a href="#bi_etl.components.readonlytable.ReadOnlyTable.add_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `cache_commit`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.cache_commit" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.cache_commit" class="headerlink" title="Permalink to this definition">¶</a>  

 `cache_row`<span class="sig-paren">(</span>*row*, *allow\_update=False*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.cache_row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.cache_row" class="headerlink" title="Permalink to this definition">¶</a>  

 `check_row_limit`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.components.readonlytable.ReadOnlyTable.check_row_limit" class="headerlink" title="Permalink to this definition">¶</a>  

 `clear_cache`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.clear_cache" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.clear_cache" class="headerlink" title="Permalink to this definition">¶</a>  
Clear all lookup caches. Sets to un-cached state (unknown state v.s. empty state which is what init\_cache gives)

 `clear_statistics`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.components.readonlytable.ReadOnlyTable.clear_statistics" class="headerlink" title="Permalink to this definition">¶</a>  

 `close`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.close" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.close" class="headerlink" title="Permalink to this definition">¶</a>  

 `column_names`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.column_names" class="headerlink" title="Permalink to this definition">¶</a>  
Column names

 `columns`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.columns" class="headerlink" title="Permalink to this definition">¶</a>  
A named-based collection of `sqlalchemy.sql.expression.ColumnElement` objects in this table/view.

 `connection`<span class="sig-paren">(</span><span class="sig-paren">)</span> → sqlalchemy.engine.base.Connection<a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.connection" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.connection" class="headerlink" title="Permalink to this definition">¶</a>  

 `debug_log`<span class="sig-paren">(</span>*state=True*<span class="sig-paren">)</span><a href="#bi_etl.components.readonlytable.ReadOnlyTable.debug_log" class="headerlink" title="Permalink to this definition">¶</a>  

 `define_lookup`<span class="sig-paren">(</span>*lookup\_name: str*, *lookup\_keys: list*, *lookup\_class=None*, *lookup\_class\_kwargs=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.define_lookup" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.define_lookup" class="headerlink" title="Permalink to this definition">¶</a>  
Define a new lookup.

|             |                                                                                                                                                                                                                                                                      |
|-------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **lookup\_name** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – Name for the lookup. Used to refer to it later.                                                         
  -   **lookup\_keys** (*list*) – list of lookup key columns                                                                                                                                                                                                            
  -   **lookup\_class** (*Class*) – Optional python class to use for the lookup. Defaults to value of default\_lookup\_class attribute.                                                                                                                                 
  -   **lookup\_class\_kwargs** (<a href="https://docs.python.org/2/library/stdtypes.md#dict" class="reference external" title="(in Python v2.7)"><em>dict</em></a>) – Optional dict of additional parameters to pass to lookup constructor. Defaults to empty dict.  |

 `delete_flag`  

 `ensure_nk_lookup`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.ensure_nk_lookup" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.ensure_nk_lookup" class="headerlink" title="Permalink to this definition">¶</a>  

 `exclude_columns`<span class="sig-paren">(</span>*columns\_to\_exclude*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.exclude_columns" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.exclude_columns" class="headerlink" title="Permalink to this definition">¶</a>  
Exclude columns from the table. Removes them from all SQL statements.

columns\_to\_exclude <span class="classifier-delimiter">:</span> <span class="classifier">list</span>  
A list of columns to exclude when reading the table/view.

 `execute`<span class="sig-paren">(</span>*statement*, *\*multiparams*, *\*\*params*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.execute" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.execute" class="headerlink" title="Permalink to this definition">¶</a>  

 `fill_cache`<span class="sig-paren">(</span>*progress\_frequency: float = 10*, *progress\_message='{table} fill\_cache current row \# {row\_number:*, *}'*, *criteria=None*, *column\_list=None*, *exclude\_cols=None*, *order\_by=None*, *assume\_lookup\_complete=None*, *row\_limit=None*, *parent\_stats=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.fill_cache" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.fill_cache" class="headerlink" title="Permalink to this definition">¶</a>  
Fill all lookup caches from the table.

|             |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
|-------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **progress\_frequency** (<a href="https://docs.python.org/2/library/functions.md#int" class="reference external" title="(in Python v2.7)"><em>int</em></a>*,* *optional*) – How often (in seconds) to output progress messages. Default 10. None for no progress messages.                                                                                                                                                                                                                                                        
  -   **progress\_message** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>*,* *optional*) – The progress message to print. Default is `"{table} fill_cache current row # {row_number:,}"`. Note `logical_name` and `row_number` substitutions applied via <a href="https://docs.python.org/2/library/functions.md#format" class="reference external" title="(in Python v2.7)"><code class="xref py py-func docutils literal">format()</code></a>.  
  -   **criteria** (<a href="https://docs.python.org/2/library/string.md#module-string" class="reference external" title="(in Python v2.7)"><em>string</em></a> *or* *list of strings*) – Each string value will be passed to `sqlalchemy.sql.expression.Select.where()`. <a href="https://goo.gl/JlY9us" class="uri" class="reference external">https://goo.gl/JlY9us</a>                                                                                                                                                               
  -   **column\_list** (*list*) – Optional. Specific columns to include when filling the cache.                                                                                                                                                                                                                                                                                                                                                                                                                                            
  -   **exclude\_cols** (*list*) – Optional. Columns to exclude when filling the cache                                                                                                                                                                                                                                                                                                                                                                                                                                                     
  -   **order\_by** (*list*) – list of columns to sort by when filling the cache (helps range caches)                                                                                                                                                                                                                                                                                                                                                                                                                                      
  -   **assume\_lookup\_complete** (*boolean*) – Should later lookup calls assume the cache is complete? If so, lookups will raise an Exception if a key combination is not found. Default to False if filtering criteria was used, otherwise defaults to True.                                                                                                                                                                                                                                                                            
  -   **row\_limit** (<a href="https://docs.python.org/2/library/functions.md#int" class="reference external" title="(in Python v2.7)"><em>int</em></a>) – limit on number of rows to cache.                                                                                                                                                                                                                                                                                                                                             
  -   **parent\_stats** (<a href="bi_etl.statistics.md#bi_etl.statistics.Statistics" class="reference internal" title="bi_etl.statistics.Statistics"><em>bi_etl.statistics.Statistics</em></a>) – Optional Statistics object to nest this steps statistics in. Default is to place statistics in the ETLTask level statistics.                                                                                                                                                                                                           |

 `generate_iteration_header`<span class="sig-paren">(</span>*logical\_name=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.generate_iteration_header" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.generate_iteration_header" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_by_key`<span class="sig-paren">(</span>*source\_row: bi\_etl.components.row.row.Row*, *stats\_id: str = 'get\_by\_key'*, *parent\_stats: bi\_etl.statistics.Statistics = None*<span class="sig-paren">)</span> → bi\_etl.components.row.row.Row<a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_by_key" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_by_key" class="headerlink" title="Permalink to this definition">¶</a>  
Get by the primary key.

 `get_by_lookup`<span class="sig-paren">(</span>*lookup\_name: str*, *source\_row: bi\_etl.components.row.row.Row*, *stats\_id: str = 'get\_by\_lookup'*, *parent\_stats: typing.Union\[bi\_etl.statistics.Statistics*, *NoneType\] = None*<span class="sig-paren">)</span> → bi\_etl.components.row.row.Row<a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_by_lookup" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_by_lookup" class="headerlink" title="Permalink to this definition">¶</a>  
Get by an alternate key. Returns a `Row`

Throws:  
NoResultFound

 `get_column`<span class="sig-paren">(</span>*column: typing.Union\[str, sqlalchemy.sql.schema.Column\]*<span class="sig-paren">)</span> → sqlalchemy.sql.schema.Column<a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_column" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_column" class="headerlink" title="Permalink to this definition">¶</a>  
Get the `sqlalchemy.sql.expression.ColumnElement` object for a given column name.

 `get_column_name`<span class="sig-paren">(</span>*column*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_column_name" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_column_name" class="headerlink" title="Permalink to this definition">¶</a>  
Get the column name given a possible `sqlalchemy.sql.expression.ColumnElement` object.

 `get_invalid_row`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_invalid_row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_invalid_row" class="headerlink" title="Permalink to this definition">¶</a>  
Get a `Row` with the Invalid special values filled in for all columns.

<table>
<colgroup>
<col width="55%" />
<col width="45%" />
</colgroup>
<thead>
<tr class="header">
<th>Type</th>
<th>Value</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>Integer</td>
<td>-8888</td>
</tr>
<tr class="even">
<td>Short Text</td>
<td>‘!’</td>
</tr>
<tr class="odd">
<td>Long Text</td>
<td>‘Invalid’</td>
</tr>
<tr class="even">
<td>Date</td>
<td>9999-8-1</td>
</tr>
</tbody>
</table>

 `get_lookup`<span class="sig-paren">(</span>*lookup\_name*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_lookup" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_lookup" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_lookup_keys`<span class="sig-paren">(</span>*lookup\_name*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_lookup_keys" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_lookup_keys" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_lookup_tuple`<span class="sig-paren">(</span>*lookup\_name*, *row*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_lookup_tuple" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_lookup_tuple" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_missing_row`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_missing_row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_missing_row" class="headerlink" title="Permalink to this definition">¶</a>  
Get a `Row` with the Missing special values filled in for all columns.

<table>
<colgroup>
<col width="55%" />
<col width="45%" />
</colgroup>
<thead>
<tr class="header">
<th>Type</th>
<th>Value</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>Integer</td>
<td>-9999</td>
</tr>
<tr class="even">
<td>Short Text</td>
<td>‘?’</td>
</tr>
<tr class="odd">
<td>Long Text</td>
<td>‘Missing’</td>
</tr>
<tr class="even">
<td>Date</td>
<td>9999-9-1</td>
</tr>
</tbody>
</table>

 `get_natural_key_tuple`<span class="sig-paren">(</span>*row*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_natural_key_tuple" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_natural_key_tuple" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_natural_key_value_list`<span class="sig-paren">(</span>*row*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_natural_key_value_list" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_natural_key_value_list" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_nk_lookup`<span class="sig-paren">(</span><span class="sig-paren">)</span> → bi\_etl.lookups.lookup.Lookup<a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_nk_lookup" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_nk_lookup" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_nk_lookup_name`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_nk_lookup_name" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_nk_lookup_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_not_applicable_row`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_not_applicable_row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_not_applicable_row" class="headerlink" title="Permalink to this definition">¶</a>  
Get a `Row` with the Not Applicable special values filled in for all columns.

<table>
<colgroup>
<col width="41%" />
<col width="59%" />
</colgroup>
<thead>
<tr class="header">
<th>Type</th>
<th>Value</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>Integer</td>
<td>-7777</td>
</tr>
<tr class="even">
<td>Short Text</td>
<td>‘~’</td>
</tr>
<tr class="odd">
<td>Long Text</td>
<td>‘Not Applicable’</td>
</tr>
<tr class="even">
<td>Date</td>
<td>9999-7-1</td>
</tr>
</tbody>
</table>

 `get_one`<span class="sig-paren">(</span>*statement=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_one" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_one" class="headerlink" title="Permalink to this definition">¶</a>  
Gets one row from the statement.

|              |                                                              |
|--------------|--------------------------------------------------------------|
| Returns:     | **row** – The row returned                                   |
| Return type: | `Row`                                                        |
| Raises:      | -   `NoResultFound` – No rows returned.                      
  -   `MultipleResultsFound` – More than one row was returned.  |

 `get_pk_lookup`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_pk_lookup" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_pk_lookup" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_primary_key_value_list`<span class="sig-paren">(</span>*row*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_primary_key_value_list" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_primary_key_value_list" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_primary_key_value_tuple`<span class="sig-paren">(</span>*row*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_primary_key_value_tuple" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_primary_key_value_tuple" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_special_row`<span class="sig-paren">(</span>*short\_char*, *long\_char*, *int\_value*, *date\_value*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_special_row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_special_row" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_stats_entry`<span class="sig-paren">(</span>*stats\_id: str*, *parent\_stats: bi\_etl.statistics.Statistics = None*, *print\_start\_stop\_times: bool = None*<span class="sig-paren">)</span><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_unique_stats_entry`<span class="sig-paren">(</span>*stats\_id*, *parent\_stats=None*, *print\_start\_stop\_times=None*<span class="sig-paren">)</span><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_unique_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_various_row`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.get_various_row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.get_various_row" class="headerlink" title="Permalink to this definition">¶</a>  
Get a `Row` with the Various special values filled in for all columns.

<table>
<colgroup>
<col width="55%" />
<col width="45%" />
</colgroup>
<thead>
<tr class="header">
<th>Type</th>
<th>Value</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>Integer</td>
<td>-6666</td>
</tr>
<tr class="even">
<td>Short Text</td>
<td>‘*’</td>
</tr>
<tr class="odd">
<td>Long Text</td>
<td>‘Various’</td>
</tr>
<tr class="even">
<td>Date</td>
<td>9999-6-1</td>
</tr>
</tbody>
</table>

 `include_only_columns`<span class="sig-paren">(</span>*columns\_to\_include*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.include_only_columns" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.include_only_columns" class="headerlink" title="Permalink to this definition">¶</a>  
Include only specified columns in the table defintion. Columns that are non included are removed them from all SQL statements.

columns\_to\_include <span class="classifier-delimiter">:</span> <span class="classifier">list</span>  
A list of columns to include when reading the table/view.

 `init_cache`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.init_cache" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.init_cache" class="headerlink" title="Permalink to this definition">¶</a>  
Initialize all lookup caches as empty.

 `is_connected`<span class="sig-paren">(</span><span class="sig-paren">)</span> → bool<a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.is_connected" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.is_connected" class="headerlink" title="Permalink to this definition">¶</a>  

 `iter_result`<span class="sig-paren">(</span>*result\_list: object*, *where\_dict: dict = None*, *progress\_frequency: int = None*, *stats\_id: str = None*, *parent\_stats: bi\_etl.statistics.Statistics = None*<span class="sig-paren">)</span> → typing.Iterable\[bi\_etl.components.row.row.Row\]<a href="#bi_etl.components.readonlytable.ReadOnlyTable.iter_result" class="headerlink" title="Permalink to this definition">¶</a>  
|         |                            |
|---------|----------------------------|
| Yields: | **row** (`Row`) – next row |

 `log_progress`<span class="sig-paren">(</span>*row: bi\_etl.components.row.row.Row*, *stats*<span class="sig-paren">)</span><a href="#bi_etl.components.readonlytable.ReadOnlyTable.log_progress" class="headerlink" title="Permalink to this definition">¶</a>  

 `lookups`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.lookups" class="headerlink" title="Permalink to this definition">¶</a>  

 `max`<span class="sig-paren">(</span>*column*, *where=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.max" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.max" class="headerlink" title="Permalink to this definition">¶</a>  
Query the table/view to get the maximum value of a given column.

|              |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
|--------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters:  | -   **column** (str or `sqlalchemy.sql.expression.ColumnElement`.) – The column to get the max value of                                                                                                                                                                                                                                                                                                                                                                                                                                                        
  -   **where** (<a href="https://docs.python.org/2/library/string.md#module-string" class="reference external" title="(in Python v2.7)"><em>string</em></a> *or* *list of strings*) – Each string value will be passed to `sqlalchemy.sql.expression.Select.where()` <a href="http://docs.sqlalchemy.org/en/rel_1_0/core/selectable.md?highlight=where#sqlalchemy.sql.expression.Select.where" class="uri" class="reference external">http://docs.sqlalchemy.org/en/rel_1_0/core/selectable.md?highlight=where#sqlalchemy.sql.expression.Select.where</a>  |
| Returns:     | **max**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Return type: | depends on column datatype                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |

 `natural_key`  
Get this tables natural key

 `order_by`<span class="sig-paren">(</span>*order\_by*, *stats\_id=None*, *parent\_stats=None*<span class="sig-paren">)</span> → typing.Iterable\[bi\_etl.components.row.row.Row\]<a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.order_by" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.order_by" class="headerlink" title="Permalink to this definition">¶</a>  
Iterate over rows matching `criteria`

|             |                                                                                                                                                                                                                                                                                                                                |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **order\_by** (<a href="https://docs.python.org/2/library/string.md#module-string" class="reference external" title="(in Python v2.7)"><em>string</em></a> *or* *list of strings*) – Each value should represent a column to order by.                                                                                   
  -   **stats\_id** (<a href="https://docs.python.org/2/library/string.md#module-string" class="reference external" title="(in Python v2.7)"><em>string</em></a>) – Name of this step for the ETLTask statistics.                                                                                                               
  -   **parent\_stats** (<a href="bi_etl.statistics.md#bi_etl.statistics.Statistics" class="reference internal" title="bi_etl.statistics.Statistics"><em>bi_etl.statistics.Statistics</em></a>) – Optional Statistics object to nest this steps statistics in. Default is to place statistics in the ETLTask level statistics.  |
| Yields:     | **row** (`Row`) – `Row` object with contents of a table/view row                                                                                                                                                                                                                                                               |

 `primary_key`  

 `process_messages`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.components.readonlytable.ReadOnlyTable.process_messages" class="headerlink" title="Permalink to this definition">¶</a>  
Processes messages for this components task. Should be called somewhere in any row looping. The standard iterator does this for you.

 `progress_frequency`  

 `row_name`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.row_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `rows_read`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.rows_read" class="headerlink" title="Permalink to this definition">¶</a>  
int The number of rows read and returned.

 `select`<span class="sig-paren">(</span>*column\_list: typing.Union\[list*, *NoneType\] = None*, *exclude\_cols: typing.Union\[set*, *NoneType\] = None*<span class="sig-paren">)</span> → sqlalchemy.sql.selectable.Select<a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.select" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.select" class="headerlink" title="Permalink to this definition">¶</a>  
Builds a select statement for this table.

|              |           |
|--------------|-----------|
| Returns:     |           |
| Return type: | statement |

 `set_kwattrs`<span class="sig-paren">(</span>*\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.components.readonlytable.ReadOnlyTable.set_kwattrs" class="headerlink" title="Permalink to this definition">¶</a>  

 `statistics`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.statistics" class="headerlink" title="Permalink to this definition">¶</a>  

 `table`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.table" class="headerlink" title="Permalink to this definition">¶</a>  

 `table_name`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.table_name" class="headerlink" title="Permalink to this definition">¶</a>  
The table name

 `trace_data`<a href="#bi_etl.components.readonlytable.ReadOnlyTable.trace_data" class="headerlink" title="Permalink to this definition">¶</a>  
boolean Should a debug message be printed with the parsed contents (as columns) of each row.

 `uncache_row`<span class="sig-paren">(</span>*row*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.uncache_row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.uncache_row" class="headerlink" title="Permalink to this definition">¶</a>  

 `uncache_where`<span class="sig-paren">(</span>*key\_names*, *key\_values\_dict*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.uncache_where" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.uncache_where" class="headerlink" title="Permalink to this definition">¶</a>  

 `where`<span class="sig-paren">(</span>*criteria=None*, *order\_by=None*, *column\_list=None*, *exclude\_cols=None*, *use\_cache\_as\_source=None*, *progress\_frequency: int = None*, *stats\_id=None*, *parent\_stats=None*<span class="sig-paren">)</span> → typing.Iterable\[bi\_etl.components.row.row.Row\]<a href="_modules/bi_etl/components/readonlytable.md#ReadOnlyTable.where" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.readonlytable.ReadOnlyTable.where" class="headerlink" title="Permalink to this definition">¶</a>  

#### Previous topic

[bi\_etl.components.hst\_table module](bi_etl.components.hst_table.md "previous chapter")

#### Next topic

[bi\_etl.components.row package](bi_etl.components.row_package.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.components.row_package.md "bi_etl.components.row package") |
-   [previous](bi_etl.components.hst_table.md "bi_etl.components.hst_table module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.components package](bi_etl.components.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
