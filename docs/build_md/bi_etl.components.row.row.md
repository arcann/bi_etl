### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.components.row.row_case_insensitive.md "bi_etl.components.row.row_case_insensitive module") |
-   [previous](bi_etl.components.row.column_difference.md "bi_etl.components.row.column_difference module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.components package](bi_etl.components.md) »
-   [bi\_etl.components.row package](bi_etl.components.row.md) »

<span id="bi-etl-components-row-row-module"></span>
bi\_etl.components.row.row module<a href="#module-bi_etl.components.row.row" class="headerlink" title="Permalink to this headline">¶</a>
========================================================================================================================================

Created on Sep 17, 2014

@author: woodd

 *class* `bi_etl.components.row.row.``Row`<span class="sig-paren">(</span>*iteration\_header: bi\_etl.components.row.row\_iteration\_header.RowIterationHeader*, *data=None*, *status: bi\_etl.components.row.row\_status.RowStatus = None*, *allocate\_space=True*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="https://docs.python.org/2/library/functions.md#object" class="reference external" title="(in Python v2.7)"><code class="xref py py-class docutils literal">object</code></a>

Replacement for core SQL Alchemy, CSV or other dictionary based rows. Handles column names that are SQL Alchemy column objects. Keeps order of the columns (see columns\_in\_order)

 `NUMERIC_TYPES` *= \[&lt;class 'int'&gt;, &lt;class 'float'&gt;, &lt;class 'decimal.Decimal'&gt;\]*<a href="#bi_etl.components.row.row.Row.NUMERIC_TYPES" class="headerlink" title="Permalink to this definition">¶</a>  

 `as_dict`<a href="#bi_etl.components.row.row.Row.as_dict" class="headerlink" title="Permalink to this definition">¶</a>  

 `clone`<span class="sig-paren">(</span><span class="sig-paren">)</span> → bi\_etl.components.row.row.Row<a href="_modules/bi_etl/components/row/row.md#Row.clone" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.clone" class="headerlink" title="Permalink to this definition">¶</a>  
Create a clone of this row.

 `column_count`<a href="#bi_etl.components.row.row.Row.column_count" class="headerlink" title="Permalink to this definition">¶</a>  

 `column_position`<span class="sig-paren">(</span>*column\_name*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.column_position" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.column_position" class="headerlink" title="Permalink to this definition">¶</a>  
Get the column position given a column name.

|             |                                                                                                                                                                                                  |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | **column\_name** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The column name to find the position of |

 `column_set`<a href="#bi_etl.components.row.row.Row.column_set" class="headerlink" title="Permalink to this definition">¶</a>  
An ImmutableSet of the the columns of this row. Used to store different row configurations in a dictionary or set.

WARNING: The resulting set is not ordered. Do not use if the column order affects the operation. See positioned\_column\_set instead.

 `columns`<a href="#bi_etl.components.row.row.Row.columns" class="headerlink" title="Permalink to this definition">¶</a>  
A list of the columns of this row (order not guaranteed in child instances).

 `columns_in_order`<a href="#bi_etl.components.row.row.Row.columns_in_order" class="headerlink" title="Permalink to this definition">¶</a>  
A list of the columns of this row in the order they were defined.

Note: If the Row was created using a dict or dict like source, there was no order for the Row to work with.

 `compare_to`<span class="sig-paren">(</span>*other\_row: bi\_etl.components.row.row.Row*, *exclude: list = None*, *compare\_only: list = None*, *coerce\_types: bool = True*<span class="sig-paren">)</span> → list<a href="_modules/bi_etl/components/row/row.md#Row.compare_to" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.compare_to" class="headerlink" title="Permalink to this definition">¶</a>  
Compare one RowCaseInsensitive to another. Returns a list of differences.

|              |                         |
|--------------|-------------------------|
| Parameters:  | -   **other\_row** –    
  -   **exclude** –        
  -   **compare\_only** –  
  -   **coerce\_types** –  |
| Returns:     |                         |
| Return type: | List of differences     |

 `get`<span class="sig-paren">(</span>*column\_specifier*, *default\_value=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.get" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.get" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_by_position`<span class="sig-paren">(</span>*position*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.get_by_position" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.get_by_position" class="headerlink" title="Permalink to this definition">¶</a>  
Get the column value by position. Note: The first column position is 1 (not 0 like a python list).

 `get_column_name`<span class="sig-paren">(</span>*column\_specifier*, *raise\_on\_not\_exist=True*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.get_column_name" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.get_column_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_column_position`<span class="sig-paren">(</span>*column\_specifier*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.get_column_position" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.get_column_position" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_name_by_position`<span class="sig-paren">(</span>*position*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.get_name_by_position" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.get_name_by_position" class="headerlink" title="Permalink to this definition">¶</a>  
Get the column name in a given position. Note: The first column position is 1 (not 0 like a python list).

 `items`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.items" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.items" class="headerlink" title="Permalink to this definition">¶</a>  

 `keys`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.keys" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.keys" class="headerlink" title="Permalink to this definition">¶</a>  

 `name`<a href="#bi_etl.components.row.row.Row.name" class="headerlink" title="Permalink to this definition">¶</a>  

 `positioned_column_set`<a href="#bi_etl.components.row.row.Row.positioned_column_set" class="headerlink" title="Permalink to this definition">¶</a>  
An ImmutableSet of the the tuples (column, position) for this row. Used to store different row configurations in a dictionary or set.

Note: column\_set would not always work here because the set is not ordered even though the columns are.

 `primary_key`<a href="#bi_etl.components.row.row.Row.primary_key" class="headerlink" title="Permalink to this definition">¶</a>  

 `remove_columns`<span class="sig-paren">(</span>*remove\_list*, *ignore\_missing=False*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.remove_columns" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.remove_columns" class="headerlink" title="Permalink to this definition">¶</a>  
Remove columns from this row instance.

|             |                                                                                                                    |
|-------------|--------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **remove\_list** – A list of column names to remove                                                            
  -   **ignore\_missing** – Ignore (don’t raise error) if we don’t have a column with a given name Defaults to False  |

 `rename_column`<span class="sig-paren">(</span>*old\_name*, *new\_name*, *ignore\_missing=False*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.rename_column" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.rename_column" class="headerlink" title="Permalink to this definition">¶</a>  
Rename a column

|             |                                                                                                                                                                                                      |
|-------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **old\_name** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The name of the column to find and rename. 
  -   **new\_name** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The new name to give the column.            
  -   **ignore\_missing** (*boolean*) – Ignore (don’t raise error) if we don’t have a column with the name in old\_name. Defaults to False                                                              |

 `rename_columns`<span class="sig-paren">(</span>*rename\_map: typing.Union\[dict, typing.List\[tuple\]\], ignore\_missing: bool = False*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.rename_columns" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.rename_columns" class="headerlink" title="Permalink to this definition">¶</a>  
Rename many columns at once.

|             |                                                                                                                                                                    |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **rename\_map** – A dict or list of tuples to use to rename columns. Note: a list of tuples is better to use if the renames need to happen in a certain order. 
  -   **ignore\_missing** – Ignore (don’t raise error) if we don’t have a column with the name in old\_name. Defaults to False                                        |

 `set_by_position`<span class="sig-paren">(</span>*position*, *value*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.set_by_position" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.set_by_position" class="headerlink" title="Permalink to this definition">¶</a>  
Set the column value by position. Note: The first column position is 1 (not 0 like a python list).

 `set_by_zposition`<span class="sig-paren">(</span>*zposition*, *value*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.set_by_zposition" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.set_by_zposition" class="headerlink" title="Permalink to this definition">¶</a>  
Set the column value by zposition (zero based) Note: The first column position is 0 for this method

 `str_formatted`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.str_formatted" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.str_formatted" class="headerlink" title="Permalink to this definition">¶</a>  

 `subset`<span class="sig-paren">(</span>*exclude: typing.Iterable = None*, *rename\_map: typing.Union\[dict*, *typing.List\[tuple\]\] = None*, *keep\_only: typing.Iterable = None*<span class="sig-paren">)</span> → bi\_etl.components.row.row.Row<a href="_modules/bi_etl/components/row/row.md#Row.subset" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.subset" class="headerlink" title="Permalink to this definition">¶</a>  
Return a new row instance with a subset of the columns. Original row is not modified Excludes are done first, then renames and finally keep\_only.

|             |                                                                                                                          |
|-------------|--------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **exclude** – A list of column names (before renames) to exclude from the subset. Optional. Defaults to no excludes. 
  -   **rename\_map** – A dict to use to rename columns. Optional. Defaults to no renames.                                  
  -   **keep\_only** – A list of column names (after renames) of columns to keep. Optional. Defaults to keep all.           |

 `transform`<span class="sig-paren">(</span>*column\_specifier*, *transform\_function*, *raise\_on\_not\_exist: bool = True*, *\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.transform" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.transform" class="headerlink" title="Permalink to this definition">¶</a>  
Apply a transformation to a column. The transformation function must take the value to be transformed as it’s first argument.

|             |                                                                                                                                                                                                                |
|-------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **column\_specifier** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The column name in the row to be transformed 
  -   **transform\_function** (*func*) – The transformation function to use. It must take the value to be transformed as it’s first argument.                                                                     
  -   **raise\_on\_not\_exist** – Should this function raise an error if the column\_specifier doesn’t match an existing column. Defaults to True                                                                 
  -   **args** (<a href="https://docs.python.org/2/library/functions.md#list" class="reference external" title="(in Python v2.7)"><em>list</em></a>) – Positional arguments to pass to transform\_function      
  -   **kwargs** (<a href="https://docs.python.org/2/library/stdtypes.md#dict" class="reference external" title="(in Python v2.7)"><em>dict</em></a>) – Keyword arguments to pass to transform\_function        |

 `update`<span class="sig-paren">(</span>*\*args*, *\*\*key\_word\_arguments*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.update" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.update" class="headerlink" title="Permalink to this definition">¶</a>  

 `update_from_dict`<span class="sig-paren">(</span>*source\_dict*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.update_from_dict" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.update_from_dict" class="headerlink" title="Permalink to this definition">¶</a>  

 `update_from_row_proxy`<span class="sig-paren">(</span>*source\_row*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.update_from_row_proxy" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.update_from_row_proxy" class="headerlink" title="Permalink to this definition">¶</a>  

 `update_from_tuples`<span class="sig-paren">(</span>*tuples\_list*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.update_from_tuples" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.update_from_tuples" class="headerlink" title="Permalink to this definition">¶</a>  

 `update_from_values`<span class="sig-paren">(</span>*values\_list*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.update_from_values" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.update_from_values" class="headerlink" title="Permalink to this definition">¶</a>  

 `values`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.values" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.values" class="headerlink" title="Permalink to this definition">¶</a>  

 `values_in_order`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#Row.values_in_order" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.Row.values_in_order" class="headerlink" title="Permalink to this definition">¶</a>  

<!-- -->

 `bi_etl.components.row.row.``main`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row.md#main" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row.main" class="headerlink" title="Permalink to this definition">¶</a>  

#### Previous topic

[bi\_etl.components.row.column\_difference module](bi_etl.components.row.column_difference.md "previous chapter")

#### Next topic

[bi\_etl.components.row.row\_case\_insensitive module](bi_etl.components.row.row_case_insensitive.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.components.row.row_case_insensitive.md "bi_etl.components.row.row_case_insensitive module") |
-   [previous](bi_etl.components.row.column_difference.md "bi_etl.components.row.column_difference module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.components package](bi_etl.components.md) »
-   [bi\_etl.components.row package](bi_etl.components.row.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
