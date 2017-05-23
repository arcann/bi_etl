### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.lookups.disk_lookup.md "bi_etl.lookups.disk_lookup module") |
-   [previous](bi_etl.lookups.autodisk_lookup.md "bi_etl.lookups.autodisk_lookup module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.lookups package](bi_etl.lookups.md) »

<span id="bi-etl-lookups-autodisk-range-lookup-module"></span>
bi\_etl.lookups.autodisk\_range\_lookup module<a href="#module-bi_etl.lookups.autodisk_range_lookup" class="headerlink" title="Permalink to this headline">¶</a>
================================================================================================================================================================

Created on Jan 5, 2016

@author: woodd

 *class* `bi_etl.lookups.autodisk_range_lookup.``AutoDiskRangeLookup`<span class="sig-paren">(</span>*lookup\_name*, *lookup\_keys*, *parent\_component*, *begin\_date*, *end\_date*, *config=None*, *path=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/lookups/autodisk_range_lookup.md#AutoDiskRangeLookup" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: `bi_etl.lookups.autodisk_lookup.AutoDiskLookup`, <a href="bi_etl.lookups.range_lookup.md#bi_etl.lookups.range_lookup.RangeLookup" class="reference internal" title="bi_etl.lookups.range_lookup.RangeLookup"><code class="xref py py-class docutils literal">bi_etl.lookups.range_lookup.RangeLookup</code></a>

Automatic memory / disk lookup cache.

This version divides the cache into N chunks (default is 10). If RAM usage gets beyond limits, it starts moving chunks to disk. Once a chunk is on disk, it stays there.

TODO: For use cases where the lookup will be used in a mostly sequential fashion, it would be useful to have a version that uses ranges instead of a hash function. Then when find\_in\_cache is called on a disk segment, we could swap a different segment out and bring that segment in. That’s a lot more complicated. We’d also want to maintain a last used date for each segment so that if we add rows to the cache, we can choose the best segment to swap to disk.

Also worth considering is that if we bring a segment in from disk, it would best to keep the disk version. At that point any additions to that segment would need to go to both places.

 `COLLECTION_INDEX` *= 0*<a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.COLLECTION_INDEX" class="headerlink" title="Permalink to this definition">¶</a>  

 `add_size_to_stats`<span class="sig-paren">(</span><span class="sig-paren">)</span> → None<a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.add_size_to_stats" class="headerlink" title="Permalink to this definition">¶</a>  

 `cache_row`<span class="sig-paren">(</span>*row*, *allow\_update=True*<span class="sig-paren">)</span><a href="_modules/bi_etl/lookups/autodisk_range_lookup.md#AutoDiskRangeLookup.cache_row" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.cache_row" class="headerlink" title="Permalink to this definition">¶</a>  

 `clear_cache`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.clear_cache" class="headerlink" title="Permalink to this definition">¶</a>  

 `commit`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.commit" class="headerlink" title="Permalink to this definition">¶</a>  
Placeholder for other implementations that might need it

 `find_in_cache`<span class="sig-paren">(</span>*row*, *\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/lookups/autodisk_range_lookup.md#AutoDiskRangeLookup.find_in_cache" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.find_in_cache" class="headerlink" title="Permalink to this definition">¶</a>  

 `find_in_remote_table`<span class="sig-paren">(</span>*row*, *effective\_date=None*<span class="sig-paren">)</span><a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.find_in_remote_table" class="headerlink" title="Permalink to this definition">¶</a>  
Find a matching row in the lookup based on the lookup index (keys)

Only works if parent\_component is based on bi\_etl.components.readonlytable

 `find_where`<span class="sig-paren">(</span>*key\_names: list*, *key\_values\_dict: dict*, *limit: int = None*<span class="sig-paren">)</span><a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.find_where" class="headerlink" title="Permalink to this definition">¶</a>  
Scan all cached rows (expensive) to find list of rows that match criteria.

 `flush_to_disk`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.flush_to_disk" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_disk_size`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.get_disk_size" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_hashable_combined_key`<span class="sig-paren">(</span>*row: bi\_etl.components.row.row.Row*<span class="sig-paren">)</span><a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.get_hashable_combined_key" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_list_of_lookup_column_values`<span class="sig-paren">(</span>*row: bi\_etl.components.row.row.Row*<span class="sig-paren">)</span> → list<a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.get_list_of_lookup_column_values" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_memory_size`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.get_memory_size" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_unique_stats_entry`<span class="sig-paren">(</span>*stats\_id*, *parent\_stats=None*, *print\_start\_stop\_times=None*<span class="sig-paren">)</span><a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.get_unique_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_versions_collection`<span class="sig-paren">(</span>*row*<span class="sig-paren">)</span> → dict<a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.get_versions_collection" class="headerlink" title="Permalink to this definition">¶</a>  
This method exists for compatibility with range caches

|              |                                           |
|--------------|-------------------------------------------|
| Parameters:  | **row** – The row with keys to search row |
| Returns:     |                                           |
| Return type: | A dict or SortedDict of rows              |

 `has_row`<span class="sig-paren">(</span>*row*<span class="sig-paren">)</span><a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.has_row" class="headerlink" title="Permalink to this definition">¶</a>  
Does the row exist in the cache (for any date if it’s a date range cache)

|             |           |
|-------------|-----------|
| Parameters: | **row** – |

 `init_cache`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.init_cache" class="headerlink" title="Permalink to this definition">¶</a>  

 `init_disk_cache`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.init_disk_cache" class="headerlink" title="Permalink to this definition">¶</a>  

 `memory_limit_reached`<span class="sig-paren">(</span><span class="sig-paren">)</span> → bool<a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.memory_limit_reached" class="headerlink" title="Permalink to this definition">¶</a>  

 `uncache_row`<span class="sig-paren">(</span>*row*<span class="sig-paren">)</span><a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.uncache_row" class="headerlink" title="Permalink to this definition">¶</a>  

 `uncache_where`<span class="sig-paren">(</span>*key\_names: list*, *key\_values\_dict: dict*<span class="sig-paren">)</span><a href="#bi_etl.lookups.autodisk_range_lookup.AutoDiskRangeLookup.uncache_where" class="headerlink" title="Permalink to this definition">¶</a>  
Scan all cached rows (expensive) to find rows to remove.

#### Previous topic

[bi\_etl.lookups.autodisk\_lookup module](bi_etl.lookups.autodisk_lookup.md "previous chapter")

#### Next topic

[bi\_etl.lookups.disk\_lookup module](bi_etl.lookups.disk_lookup.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.lookups.disk_lookup.md "bi_etl.lookups.disk_lookup module") |
-   [previous](bi_etl.lookups.autodisk_lookup.md "bi_etl.lookups.autodisk_lookup module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.lookups package](bi_etl.lookups.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
