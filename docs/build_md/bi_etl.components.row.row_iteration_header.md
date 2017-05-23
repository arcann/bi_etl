### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.components.row.row_status.md "bi_etl.components.row.row_status module") |
-   [previous](bi_etl.components.row.row_case_insensitive.md "bi_etl.components.row.row_case_insensitive module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.components package](bi_etl.components.md) »
-   [bi\_etl.components.row package](bi_etl.components.row.md) »

bi\_etl.components.row.row\_iteration\_header module<a href="#bi-etl-components-row-row-iteration-header-module" class="headerlink" title="Permalink to this headline">¶</a>
============================================================================================================================================================================

<span id="module-bi_etl.components.row.row_iteration_header" class="target"></span>
Created on May 26, 2015

@author: woodd

 *class* `bi_etl.components.row.row_iteration_header.``RowIterationHeader`<a href="_modules/bi_etl/components/row/row_iteration_header.md#RowIterationHeader" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row_iteration_header.RowIterationHeader" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="https://docs.python.org/2/library/functions.md#object" class="reference external" title="(in Python v2.7)"><code class="xref py py-class docutils literal">object</code></a>

Stores the headers of a set of rows for a given iteration

 `add_row`<span class="sig-paren">(</span>*row*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row_iteration_header.md#RowIterationHeader.add_row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row_iteration_header.RowIterationHeader.add_row" class="headerlink" title="Permalink to this definition">¶</a>  

 `column_count`<span class="sig-paren">(</span><span class="sig-paren">)</span> → int<a href="_modules/bi_etl/components/row/row_iteration_header.md#RowIterationHeader.column_count" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row_iteration_header.RowIterationHeader.column_count" class="headerlink" title="Permalink to this definition">¶</a>  

 `column_set`<a href="#bi_etl.components.row.row_iteration_header.RowIterationHeader.column_set" class="headerlink" title="Permalink to this definition">¶</a>  
An ImmutableSet of the the columns of this row. Used to store different row configurations in a dictionary or set.

WARNING: The resulting set is not ordered. Do not use if the column order affects the operation. See positioned\_column\_set instead.

 `columns_in_order`<a href="#bi_etl.components.row.row_iteration_header.RowIterationHeader.columns_in_order" class="headerlink" title="Permalink to this definition">¶</a>  
A list of the columns of this row in the order they were defined.

 *static* `get_by_id`<span class="sig-paren">(</span>*iteration\_id*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row_iteration_header.md#RowIterationHeader.get_by_id" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row_iteration_header.RowIterationHeader.get_by_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_column_position`<a href="_modules/bi_etl/components/row/row_iteration_header.md#RowIterationHeader.get_column_position" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row_iteration_header.RowIterationHeader.get_column_position" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_next_header`<span class="sig-paren">(</span>*action: typing.Union\[str, tuple\], start\_empty: bool = False*<span class="sig-paren">)</span> → bi\_etl.components.row.row\_iteration\_header.RowIterationHeader<a href="_modules/bi_etl/components/row/row_iteration_header.md#RowIterationHeader.get_next_header" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row_iteration_header.RowIterationHeader.get_next_header" class="headerlink" title="Permalink to this definition">¶</a>  
Get the next header after performing a manipulation on the set of columns.

|             |                                                                                        |
|-------------|----------------------------------------------------------------------------------------|
| Parameters: | -   **action** – A hashable action ID                                                  
  -   **start\_empty** – Should the new header start empty (vs transferring the columns)  |

 `has_column`<span class="sig-paren">(</span>*column\_name*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row_iteration_header.md#RowIterationHeader.has_column" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row_iteration_header.RowIterationHeader.has_column" class="headerlink" title="Permalink to this definition">¶</a>  

 `instance_dict` *= {}*<a href="#bi_etl.components.row.row_iteration_header.RowIterationHeader.instance_dict" class="headerlink" title="Permalink to this definition">¶</a>  

 `next_iteration_id` *= 0*<a href="#bi_etl.components.row.row_iteration_header.RowIterationHeader.next_iteration_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `positioned_column_set`<a href="#bi_etl.components.row.row_iteration_header.RowIterationHeader.positioned_column_set" class="headerlink" title="Permalink to this definition">¶</a>  
An ImmutableSet of the the tuples (column, position) for this row. Used to store different row configurations in a dictionary or set.

Note: column\_set would not always work here because the set is not ordered even though the columns are.

 `primary_key`<a href="#bi_etl.components.row.row_iteration_header.RowIterationHeader.primary_key" class="headerlink" title="Permalink to this definition">¶</a>  

 `remove_row`<span class="sig-paren">(</span>*row*<span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row_iteration_header.md#RowIterationHeader.remove_row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row_iteration_header.RowIterationHeader.remove_row" class="headerlink" title="Permalink to this definition">¶</a>  

 `rename_column`<span class="sig-paren">(</span>*old\_name: str*, *new\_name: str*, *ignore\_missing: bool = False*, *no\_new\_header: bool = False*<span class="sig-paren">)</span> → bi\_etl.components.row.row\_iteration\_header.RowIterationHeader<a href="_modules/bi_etl/components/row/row_iteration_header.md#RowIterationHeader.rename_column" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row_iteration_header.RowIterationHeader.rename_column" class="headerlink" title="Permalink to this definition">¶</a>  
Rename a column

|             |                                                                                                                                      |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **old\_name** – str The name of the column to find and rename.                                                                   
  -   **new\_name** – str The new name to give the column.                                                                              
  -   **ignore\_missing** – boolean Ignore (don’t raise error) if we don’t have a column with the name in old\_name. Defaults to False  
  -   **no\_new\_header** –                                                                                                             
                                                                                                                                        
      Skip creating a new row header, modify in place.                                                                                  
                                                                                                                                        
      \*\* BE CAREFUL USING THIS! \*\*                                                                                                  
                                                                                                                                        
      All new rows created with this header will immediately get the new name, in which case you won’t want to call this method again.  |

 `rename_columns`<span class="sig-paren">(</span>*rename\_map: typing.Union\[dict, typing.List\[tuple\]\], ignore\_missing: bool = False, no\_new\_header: bool = False*<span class="sig-paren">)</span> → bi\_etl.components.row.row\_iteration\_header.RowIterationHeader<a href="_modules/bi_etl/components/row/row_iteration_header.md#RowIterationHeader.rename_columns" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row_iteration_header.RowIterationHeader.rename_columns" class="headerlink" title="Permalink to this definition">¶</a>  
Rename many columns at once.

|             |                                                                                                                                                                    |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **rename\_map** – A dict or list of tuples to use to rename columns. Note: a list of tuples is better to use if the renames need to happen in a certain order. 
  -   **ignore\_missing** – Ignore (don’t raise error) if we don’t have a column with the name in old\_name. Defaults to False                                        
  -   **no\_new\_header** –                                                                                                                                           
                                                                                                                                                                      
      Skip creating a new row header, modify in place.                                                                                                                
                                                                                                                                                                      
      \*\* BE CAREFUL USING THIS! \*\*                                                                                                                                
                                                                                                                                                                      
      All new rows created with this header will immediately get the new name, in which case you won’t want to call this method again.                                |

 `row_remove_column`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row_iteration_header.md#RowIterationHeader.row_remove_column" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row_iteration_header.RowIterationHeader.row_remove_column" class="headerlink" title="Permalink to this definition">¶</a>  

 `row_set_item`<span class="sig-paren">(</span>*column\_name: str*, *value*, *row*<span class="sig-paren">)</span> → bi\_etl.components.row.row\_iteration\_header.RowIterationHeader<a href="_modules/bi_etl/components/row/row_iteration_header.md#RowIterationHeader.row_set_item" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row_iteration_header.RowIterationHeader.row_set_item" class="headerlink" title="Permalink to this definition">¶</a>  
Set a column in a row and return a new row header (it might have changed if the column was new).

|             |                                                                                                                                                                                                                          |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **column\_name** – column to set                                                                                                                                                                                     
  -   **value** – new value                                                                                                                                                                                                 
  -   **row** (<a href="bi_etl.components.row.row.md#bi_etl.components.row.row.Row" class="reference internal" title="bi_etl.components.row.row.Row"><em>bi_etl.components.row.row.Row</em></a>) – row to find column on  |
| Returns:    | Modified row header                                                                                                                                                                                                      |

 `row_subset`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/components/row/row_iteration_header.md#RowIterationHeader.row_subset" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.components.row.row_iteration_header.RowIterationHeader.row_subset" class="headerlink" title="Permalink to this definition">¶</a>  
Return a new row instance with a subset of the columns. Original row is not modified Excludes are done first, then renames and finally keep\_only.

|             |                                                                                                                                                                       |
|-------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **exclude** – A list of column names (before renames) to exclude from the subset. Optional. Defaults to no excludes.                                              
  -   **rename\_map** – A dict to use to rename columns. Optional. Defaults to no renames.                                                                               
  -   **keep\_only** – A list of column names (after renames) of columns to keep. Optional. Defaults to keep all.                                                        |
| Returns:    |                                                                                                                                                                       
                                                                                                                                                                         
  -   *a list with the position mapping of new to old items.*                                                                                                            
  -   *So* – The first item in the list will be the index of that item in the old list. The second item in the list will be the index of that item in the old list. etc  |

#### Previous topic

[bi\_etl.components.row.row\_case\_insensitive module](bi_etl.components.row.row_case_insensitive.md "previous chapter")

#### Next topic

[bi\_etl.components.row.row\_status module](bi_etl.components.row.row_status.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.components.row.row_status.md "bi_etl.components.row.row_status module") |
-   [previous](bi_etl.components.row.row_case_insensitive.md "bi_etl.components.row.row_case_insensitive module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.components package](bi_etl.components.md) »
-   [bi\_etl.components.row package](bi_etl.components.row.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
