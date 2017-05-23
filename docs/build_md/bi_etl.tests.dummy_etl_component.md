### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.tests.mock_metadata.md "bi_etl.tests.mock_metadata module") |
-   [previous](bi_etl.tests.debug_sa_objects.md "bi_etl.tests.debug_sa_objects module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.tests package](bi_etl.tests.md) »

<span id="bi-etl-tests-dummy-etl-component-module"></span>
bi\_etl.tests.dummy\_etl\_component module<a href="#module-bi_etl.tests.dummy_etl_component" class="headerlink" title="Permalink to this headline">¶</a>
========================================================================================================================================================

Created on Jan 6, 2016

@author: woodd

 *class* `bi_etl.tests.dummy_etl_component.``DummyETLComponent`<span class="sig-paren">(</span>*task=None*, *logical\_name=None*, *primary\_key=None*, *data=None*, *iteration\_header=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/tests/dummy_etl_component.md#DummyETLComponent" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="bi_etl.components.etlcomponent.md#bi_etl.components.etlcomponent.ETLComponent" class="reference internal" title="bi_etl.components.etlcomponent.ETLComponent"><code class="xref py py-class docutils literal">bi_etl.components.etlcomponent.ETLComponent</code></a>

classdocs

 `DEFAULT_PROGRESS_FREQUENCY` *= 10*<a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.DEFAULT_PROGRESS_FREQUENCY" class="headerlink" title="Permalink to this definition">¶</a>  

 `DEFAULT_PROGRESS_MESSAGE` *= '{logical\_name} current row \# {row\_number:,}'*<a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.DEFAULT_PROGRESS_MESSAGE" class="headerlink" title="Permalink to this definition">¶</a>  

 `Row`<span class="sig-paren">(</span>*data=None*, *logical\_name=None*, *iteration\_header=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.Row" class="headerlink" title="Permalink to this definition">¶</a>  
Make a new empty row with this components structure.

 `add_stats_entry`<span class="sig-paren">(</span>*stats\_id*, *stats\_entry*, *parent\_stats=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.add_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `check_row_limit`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.check_row_limit" class="headerlink" title="Permalink to this definition">¶</a>  

 `clear_statistics`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.clear_statistics" class="headerlink" title="Permalink to this definition">¶</a>  

 `close`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.close" class="headerlink" title="Permalink to this definition">¶</a>  

 `column_names`<a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.column_names" class="headerlink" title="Permalink to this definition">¶</a>  
Column names

 `debug_log`<span class="sig-paren">(</span>*state=True*<span class="sig-paren">)</span><a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.debug_log" class="headerlink" title="Permalink to this definition">¶</a>  

 `generate_iteration_header`<span class="sig-paren">(</span>*logical\_name=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/tests/dummy_etl_component.md#DummyETLComponent.generate_iteration_header" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.generate_iteration_header" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_stats_entry`<span class="sig-paren">(</span>*stats\_id: str*, *parent\_stats: bi\_etl.statistics.Statistics = None*, *print\_start\_stop\_times: bool = None*<span class="sig-paren">)</span><a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.get_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_unique_stats_entry`<span class="sig-paren">(</span>*stats\_id*, *parent\_stats=None*, *print\_start\_stop\_times=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.get_unique_stats_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `iter_result`<span class="sig-paren">(</span>*result\_list: object*, *where\_dict: dict = None*, *progress\_frequency: int = None*, *stats\_id: str = None*, *parent\_stats: bi\_etl.statistics.Statistics = None*<span class="sig-paren">)</span> → typing.Iterable\[bi\_etl.components.row.row.Row\]<a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.iter_result" class="headerlink" title="Permalink to this definition">¶</a>  
|         |                            |
|---------|----------------------------|
| Yields: | **row** (`Row`) – next row |

 `log_progress`<span class="sig-paren">(</span>*row: bi\_etl.components.row.row.Row*, *stats*<span class="sig-paren">)</span><a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.log_progress" class="headerlink" title="Permalink to this definition">¶</a>  

 `primary_key`<a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.primary_key" class="headerlink" title="Permalink to this definition">¶</a>  

 `process_messages`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.process_messages" class="headerlink" title="Permalink to this definition">¶</a>  
Processes messages for this components task. Should be called somewhere in any row looping. The standard iterator does this for you.

 `progress_frequency`<a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.progress_frequency" class="headerlink" title="Permalink to this definition">¶</a>  

 `row_name`<a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.row_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `rows_read`<a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.rows_read" class="headerlink" title="Permalink to this definition">¶</a>  
int The number of rows read and returned.

 `set_kwattrs`<span class="sig-paren">(</span>*\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.set_kwattrs" class="headerlink" title="Permalink to this definition">¶</a>  

 `statistics`<a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.statistics" class="headerlink" title="Permalink to this definition">¶</a>  

 `trace_data`<a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.trace_data" class="headerlink" title="Permalink to this definition">¶</a>  
boolean Should a debug message be printed with the parsed contents (as columns) of each row.

 `where`<span class="sig-paren">(</span>*criteria=None*, *order\_by=None*, *stats\_id=None*, *parent\_stats=None*<span class="sig-paren">)</span> → typing.Iterable\[bi\_etl.components.row.row.Row\]<a href="#bi_etl.tests.dummy_etl_component.DummyETLComponent.where" class="headerlink" title="Permalink to this definition">¶</a>  

#### Previous topic

[bi\_etl.tests.debug\_sa\_objects module](bi_etl.tests.debug_sa_objects.md "previous chapter")

#### Next topic

[bi\_etl.tests.mock\_metadata module](bi_etl.tests.mock_metadata.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.tests.mock_metadata.md "bi_etl.tests.mock_metadata module") |
-   [previous](bi_etl.tests.debug_sa_objects.md "bi_etl.tests.debug_sa_objects module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.tests package](bi_etl.tests.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
