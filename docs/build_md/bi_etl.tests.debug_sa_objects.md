### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.tests.dummy_etl_component.md "bi_etl.tests.dummy_etl_component module") |
-   [previous](bi_etl.tests.etl_jobs.etl_test_task_base.md "bi_etl.tests.etl_jobs.etl_test_task_base module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.tests package](bi_etl.tests.md) »

<span id="bi-etl-tests-debug-sa-objects-module"></span>
bi\_etl.tests.debug\_sa\_objects module<a href="#module-bi_etl.tests.debug_sa_objects" class="headerlink" title="Permalink to this headline">¶</a>
==================================================================================================================================================

Created on Mar 27, 2015

@author: woodd

 *class* `bi_etl.tests.debug_sa_objects.``BaseRowProxy`<span class="sig-paren">(</span>*parent*, *row*, *processors*, *keymap*<span class="sig-paren">)</span><a href="_modules/bi_etl/tests/debug_sa_objects.md#BaseRowProxy" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.debug_sa_objects.BaseRowProxy" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="https://docs.python.org/2/library/functions.md#object" class="reference external" title="(in Python v2.7)"><code class="xref py py-class docutils literal">object</code></a>

 `values`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/debug_sa_objects.md#BaseRowProxy.values" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.debug_sa_objects.BaseRowProxy.values" class="headerlink" title="Permalink to this definition">¶</a>  
Return the values represented by this RowProxy as a list.

<!-- -->

 *class* `bi_etl.tests.debug_sa_objects.``RowProxy`<span class="sig-paren">(</span>*parent*, *row*, *processors*, *keymap*<span class="sig-paren">)</span><a href="_modules/bi_etl/tests/debug_sa_objects.md#RowProxy" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.debug_sa_objects.RowProxy" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="#bi_etl.tests.debug_sa_objects.BaseRowProxy" class="reference internal" title="bi_etl.tests.debug_sa_objects.BaseRowProxy"><code class="xref py py-class docutils literal">bi_etl.tests.debug_sa_objects.BaseRowProxy</code></a>

Proxy values from a single cursor row.

Mostly follows “ordered dictionary” behavior, mapping result values to the string-based column name, the integer position of the result in the row, as well as Column instances which can be mapped to the original Columns that produced this result set (for results that correspond to constructed SQL expressions).

 `has_key`<span class="sig-paren">(</span>*key*<span class="sig-paren">)</span><a href="_modules/bi_etl/tests/debug_sa_objects.md#RowProxy.has_key" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.debug_sa_objects.RowProxy.has_key" class="headerlink" title="Permalink to this definition">¶</a>  
Return True if this RowProxy contains the given key.

 `items`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/debug_sa_objects.md#RowProxy.items" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.debug_sa_objects.RowProxy.items" class="headerlink" title="Permalink to this definition">¶</a>  
Return a list of tuples, each tuple containing a key/value pair.

 `keys`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/debug_sa_objects.md#RowProxy.keys" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.debug_sa_objects.RowProxy.keys" class="headerlink" title="Permalink to this definition">¶</a>  
Return the list of keys as strings represented by this RowProxy.

 `values`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.debug_sa_objects.RowProxy.values" class="headerlink" title="Permalink to this definition">¶</a>  
Return the values represented by this RowProxy as a list.

<!-- -->

 `bi_etl.tests.debug_sa_objects.``mock_engine`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/debug_sa_objects.md#mock_engine" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.debug_sa_objects.mock_engine" class="headerlink" title="Permalink to this definition">¶</a>  

<!-- -->

 `bi_etl.tests.debug_sa_objects.``rowproxy_reconstructor`<span class="sig-paren">(</span>*cls*, *state*<span class="sig-paren">)</span><a href="_modules/bi_etl/tests/debug_sa_objects.md#rowproxy_reconstructor" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.debug_sa_objects.rowproxy_reconstructor" class="headerlink" title="Permalink to this definition">¶</a>  

#### Previous topic

[bi\_etl.tests.etl\_jobs.etl\_test\_task\_base module](bi_etl.tests.etl_jobs.etl_test_task_base.md "previous chapter")

#### Next topic

[bi\_etl.tests.dummy\_etl\_component module](bi_etl.tests.dummy_etl_component.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.tests.dummy_etl_component.md "bi_etl.tests.dummy_etl_component module") |
-   [previous](bi_etl.tests.etl_jobs.etl_test_task_base.md "bi_etl.tests.etl_jobs.etl_test_task_base module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.tests package](bi_etl.tests.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
