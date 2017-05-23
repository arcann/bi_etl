### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.lookups.range_lookup.md "bi_etl.lookups.range_lookup module") |
-   [previous](bi_etl.lookups.disk_range_lookup.md "bi_etl.lookups.disk_range_lookup module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.lookups package](bi_etl.lookups.md) »

<span id="bi-etl-lookups-lookup-module"></span>
bi\_etl.lookups.lookup module<a href="#module-bi_etl.lookups.lookup" class="headerlink" title="Permalink to this headline">¶</a>
================================================================================================================================

Created on Feb 26, 2015

@author: woodd

 *class* `bi_etl.lookups.lookup.``Lookup`<span class="sig-paren">(</span>*lookup\_name: str*, *lookup\_keys: list*, *parent\_component: bi\_etl.components.etlcomponent.ETLComponent*, *config: configparser.ConfigParser = None*, *\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/lookups/lookup.md#Lookup" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.lookup.Lookup" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="https://docs.python.org/2/library/functions.md#object" class="reference external" title="(in Python v2.7)"><code class="xref py py-class docutils literal">object</code></a>

 `COLLECTION_INDEX` *= 0*<a href="#bi_etl.lookups.lookup.Lookup.COLLECTION_INDEX" class="headerlink" title="Permalink to this definition">¶</a>  

 `add_size_to_stats`<span class="sig-paren">(</span><span class="sig-paren">)</span> → None<a href="_modules/bi_etl/lookups/lookup.md#Lookup.add_size_to_stats" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.lookup.Lookup.add_size_to_stats" class="headerlink" title="Permalink to this definition">¶</a>  

 `cache_row`<span class="sig-paren">(</span>*row: bi\_etl.components.row.row.Row*, *allow\_update: bool = True*<span class="sig-paren">)</span><a href="_modules/bi_etl/lookups/lookup.md#Lookup.cache_row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.lookup.Lookup.cache_row" class="headerlink" title="Permalink to this definition">¶</a>  
Adds the given row to the cache for this lookup.

|             |                                                                                                                                                                                                                     |
|-------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **row** (<a href="bi_etl.components.csvreader.md#bi_etl.components.csvreader.CSVReader.Row" class="reference internal" title="bi_etl.components.csvreader.CSVReader.Row"><em>Row</em></a>) – The row to cache 
  -   **allow\_update** (*boolean*) – Allow this method to update an existing row in the cache.                                                                                                                        |
| Raises:     | `ValueError` – If allow\_update is False and an already existing row (lookup key) is passed in.                                                                                                                     |

 `clear_cache`<span class="sig-paren">(</span><span class="sig-paren">)</span> → None<a href="_modules/bi_etl/lookups/lookup.md#Lookup.clear_cache" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.lookup.Lookup.clear_cache" class="headerlink" title="Permalink to this definition">¶</a>  
Removes cache and resets to un-cached state

 `commit`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/lookups/lookup.md#Lookup.commit" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.lookup.Lookup.commit" class="headerlink" title="Permalink to this definition">¶</a>  
Placeholder for other implementations that might need it

 `find_in_cache`<span class="sig-paren">(</span>*row*, *\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/lookups/lookup.md#Lookup.find_in_cache" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.lookup.Lookup.find_in_cache" class="headerlink" title="Permalink to this definition">¶</a>  
Find a matching row in the lookup based on the lookup index (keys)

 `find_in_remote_table`<span class="sig-paren">(</span>*row: bi\_etl.components.row.row.Row*<span class="sig-paren">)</span> → bi\_etl.components.row.row.Row<a href="_modules/bi_etl/lookups/lookup.md#Lookup.find_in_remote_table" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.lookup.Lookup.find_in_remote_table" class="headerlink" title="Permalink to this definition">¶</a>  
Find a matching row in the lookup based on the lookup index (keys)

Only works if parent\_component is based on bi\_etl.components.readonlytable

 `find_where`<span class="sig-paren">(</span>*key\_names: list*, *key\_values\_dict: dict*, *limit: int = None*<span class="sig-paren">)</span><a href="_modules/bi_etl/lookups/lookup.md#Lookup.find_where" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.lookup.Lookup.find_where" class="headerlink" title="Permalink to this definition">¶</a>  
Scan all cached rows (expensive) to find list of rows that match criteria.

 `get_disk_size`<span class="sig-paren">(</span><span class="sig-paren">)</span> → int<a href="_modules/bi_etl/lookups/lookup.md#Lookup.get_disk_size" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.lookup.Lookup.get_disk_size" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_hashable_combined_key`<span class="sig-paren">(</span>*row: bi\_etl.components.row.row.Row*<span class="sig-paren">)</span><a href="_modules/bi_etl/lookups/lookup.md#Lookup.get_hashable_combined_key" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.lookup.Lookup.get_hashable_combined_key" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_list_of_lookup_column_values`<span class="sig-paren">(</span>*row: bi\_etl.components.row.row.Row*<span class="sig-paren">)</span> → list<a href="_modules/bi_etl/lookups/lookup.md#Lookup.get_list_of_lookup_column_values" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.lookup.Lookup.get_list_of_lookup_column_values" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_memory_size`<span class="sig-paren">(</span><span class="sig-paren">)</span> → int<a href="_modules/bi_etl/lookups/lookup.md#Lookup.get_memory_size" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.lookup.Lookup.get_memory_size" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_versions_collection`<span class="sig-paren">(</span>*row*<span class="sig-paren">)</span> → dict<a href="_modules/bi_etl/lookups/lookup.md#Lookup.get_versions_collection" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.lookup.Lookup.get_versions_collection" class="headerlink" title="Permalink to this definition">¶</a>  
This method exists for compatibility with range caches

|              |                                           |
|--------------|-------------------------------------------|
| Parameters:  | **row** – The row with keys to search row |
| Returns:     |                                           |
| Return type: | A dict or SortedDict of rows              |

 `has_row`<span class="sig-paren">(</span>*row*<span class="sig-paren">)</span><a href="_modules/bi_etl/lookups/lookup.md#Lookup.has_row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.lookup.Lookup.has_row" class="headerlink" title="Permalink to this definition">¶</a>  
Does the row exist in the cache (for any date if it’s a date range cache)

|             |           |
|-------------|-----------|
| Parameters: | **row** – |

 `init_cache`<span class="sig-paren">(</span><span class="sig-paren">)</span> → None<a href="_modules/bi_etl/lookups/lookup.md#Lookup.init_cache" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.lookup.Lookup.init_cache" class="headerlink" title="Permalink to this definition">¶</a>  
Initializes the cache as empty.

 `uncache_row`<span class="sig-paren">(</span>*row: bi\_etl.components.row.row.Row*<span class="sig-paren">)</span><a href="_modules/bi_etl/lookups/lookup.md#Lookup.uncache_row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.lookup.Lookup.uncache_row" class="headerlink" title="Permalink to this definition">¶</a>  

 `uncache_where`<span class="sig-paren">(</span>*key\_names: list*, *key\_values\_dict: dict*<span class="sig-paren">)</span><a href="_modules/bi_etl/lookups/lookup.md#Lookup.uncache_where" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.lookup.Lookup.uncache_where" class="headerlink" title="Permalink to this definition">¶</a>  
Scan all cached rows (expensive) to find rows to remove.

#### Previous topic

[bi\_etl.lookups.disk\_range\_lookup module](bi_etl.lookups.disk_range_lookup.md "previous chapter")

#### Next topic

[bi\_etl.lookups.range\_lookup module](bi_etl.lookups.range_lookup.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.lookups.range_lookup.md "bi_etl.lookups.range_lookup module") |
-   [previous](bi_etl.lookups.disk_range_lookup.md "bi_etl.lookups.disk_range_lookup module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.lookups package](bi_etl.lookups.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
