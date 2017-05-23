### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.lookups.sqlite_lookup.md "bi_etl.lookups.sqlite_lookup module") |
-   [previous](bi_etl.lookups.lookup.md "bi_etl.lookups.lookup module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.lookups package](bi_etl.lookups.md) »

<span id="bi-etl-lookups-range-lookup-module"></span>
bi\_etl.lookups.range\_lookup module<a href="#module-bi_etl.lookups.range_lookup" class="headerlink" title="Permalink to this headline">¶</a>
=============================================================================================================================================

Created on Feb 27, 2015

@author: woodd

 *class* `bi_etl.lookups.range_lookup.``RangeLookup`<span class="sig-paren">(</span>*lookup\_name*, *lookup\_keys*, *parent\_component*, *begin\_date*, *end\_date*, *config=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/lookups/range_lookup.md#RangeLookup" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.range_lookup.RangeLookup" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="bi_etl.lookups.lookup.md#bi_etl.lookups.lookup.Lookup" class="reference internal" title="bi_etl.lookups.lookup.Lookup"><code class="xref py py-class docutils literal">bi_etl.lookups.lookup.Lookup</code></a>

 `COLLECTION_INDEX` *= 0*<a href="#bi_etl.lookups.range_lookup.RangeLookup.COLLECTION_INDEX" class="headerlink" title="Permalink to this definition">¶</a>  

 `add_size_to_stats`<span class="sig-paren">(</span><span class="sig-paren">)</span> → None<a href="#bi_etl.lookups.range_lookup.RangeLookup.add_size_to_stats" class="headerlink" title="Permalink to this definition">¶</a>  

 `cache_row`<span class="sig-paren">(</span>*row: bi\_etl.components.row.row.Row*, *allow\_update: bool = True*<span class="sig-paren">)</span><a href="_modules/bi_etl/lookups/range_lookup.md#RangeLookup.cache_row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.range_lookup.RangeLookup.cache_row" class="headerlink" title="Permalink to this definition">¶</a>  

 `clear_cache`<span class="sig-paren">(</span><span class="sig-paren">)</span> → None<a href="#bi_etl.lookups.range_lookup.RangeLookup.clear_cache" class="headerlink" title="Permalink to this definition">¶</a>  
Removes cache and resets to un-cached state

 `commit`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.lookups.range_lookup.RangeLookup.commit" class="headerlink" title="Permalink to this definition">¶</a>  
Placeholder for other implementations that might need it

 `find_in_cache`<span class="sig-paren">(</span>*row*, *\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/lookups/range_lookup.md#RangeLookup.find_in_cache" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.range_lookup.RangeLookup.find_in_cache" class="headerlink" title="Permalink to this definition">¶</a>  
Find an existing row in the cache effective on the date provided. Can raise ValueError if the cache is not setup. Can raise NoResultFound if the key is not in the cache. Can raise BeforeAllExisting is the effective date provided is before all existing records.

 `find_in_remote_table`<span class="sig-paren">(</span>*row*, *effective\_date=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/lookups/range_lookup.md#RangeLookup.find_in_remote_table" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.range_lookup.RangeLookup.find_in_remote_table" class="headerlink" title="Permalink to this definition">¶</a>  
Find a matching row in the lookup based on the lookup index (keys)

Only works if parent\_component is based on bi\_etl.components.readonlytable

 `find_where`<span class="sig-paren">(</span>*key\_names: list*, *key\_values\_dict: dict*, *limit: int = None*<span class="sig-paren">)</span><a href="#bi_etl.lookups.range_lookup.RangeLookup.find_where" class="headerlink" title="Permalink to this definition">¶</a>  
Scan all cached rows (expensive) to find list of rows that match criteria.

 `get_disk_size`<span class="sig-paren">(</span><span class="sig-paren">)</span> → int<a href="#bi_etl.lookups.range_lookup.RangeLookup.get_disk_size" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_hashable_combined_key`<span class="sig-paren">(</span>*row: bi\_etl.components.row.row.Row*<span class="sig-paren">)</span><a href="#bi_etl.lookups.range_lookup.RangeLookup.get_hashable_combined_key" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_list_of_lookup_column_values`<span class="sig-paren">(</span>*row: bi\_etl.components.row.row.Row*<span class="sig-paren">)</span> → list<a href="#bi_etl.lookups.range_lookup.RangeLookup.get_list_of_lookup_column_values" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_memory_size`<span class="sig-paren">(</span><span class="sig-paren">)</span> → int<a href="#bi_etl.lookups.range_lookup.RangeLookup.get_memory_size" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_versions_collection`<span class="sig-paren">(</span>*row*<span class="sig-paren">)</span> → dict<a href="_modules/bi_etl/lookups/range_lookup.md#RangeLookup.get_versions_collection" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.range_lookup.RangeLookup.get_versions_collection" class="headerlink" title="Permalink to this definition">¶</a>  
This method exists for compatibility with range caches

|              |                                           |
|--------------|-------------------------------------------|
| Parameters:  | **row** – The row with keys to search row |
| Returns:     |                                           |
| Return type: | A dict or SortedDict of rows              |

 `has_row`<span class="sig-paren">(</span>*row*<span class="sig-paren">)</span><a href="#bi_etl.lookups.range_lookup.RangeLookup.has_row" class="headerlink" title="Permalink to this definition">¶</a>  
Does the row exist in the cache (for any date if it’s a date range cache)

|             |           |
|-------------|-----------|
| Parameters: | **row** – |

 `init_cache`<span class="sig-paren">(</span><span class="sig-paren">)</span> → None<a href="#bi_etl.lookups.range_lookup.RangeLookup.init_cache" class="headerlink" title="Permalink to this definition">¶</a>  
Initializes the cache as empty.

 `uncache_row`<span class="sig-paren">(</span>*row*<span class="sig-paren">)</span><a href="_modules/bi_etl/lookups/range_lookup.md#RangeLookup.uncache_row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.range_lookup.RangeLookup.uncache_row" class="headerlink" title="Permalink to this definition">¶</a>  

 `uncache_where`<span class="sig-paren">(</span>*key\_names: list*, *key\_values\_dict: dict*<span class="sig-paren">)</span><a href="#bi_etl.lookups.range_lookup.RangeLookup.uncache_where" class="headerlink" title="Permalink to this definition">¶</a>  
Scan all cached rows (expensive) to find rows to remove.

#### Previous topic

[bi\_etl.lookups.lookup module](bi_etl.lookups.lookup.md "previous chapter")

#### Next topic

[bi\_etl.lookups.sqlite\_lookup module](bi_etl.lookups.sqlite_lookup.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.lookups.sqlite_lookup.md "bi_etl.lookups.sqlite_lookup module") |
-   [previous](bi_etl.lookups.lookup.md "bi_etl.lookups.lookup module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.lookups package](bi_etl.lookups.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
