### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.statistics.md "bi_etl.statistics module") |
-   [previous](bi_etl.memory_size.md "bi_etl.memory_size module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »

<span id="bi-etl-statement-queue-module"></span>
bi\_etl.statement\_queue module<a href="#module-bi_etl.statement_queue" class="headerlink" title="Permalink to this headline">¶</a>
===================================================================================================================================

Created on Mar 2, 2015

@author: woodd

 *class* `bi_etl.statement_queue.``StatementQueue`<a href="_modules/bi_etl/statement_queue.md#StatementQueue" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.statement_queue.StatementQueue" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="https://docs.python.org/2/library/functions.md#object" class="reference external" title="(in Python v2.7)"><code class="xref py py-class docutils literal">object</code></a>

A queue of pending SQLAlchemyy statements

 `add_statement`<span class="sig-paren">(</span>*key*, *stmt*<span class="sig-paren">)</span><a href="_modules/bi_etl/statement_queue.md#StatementQueue.add_statement" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.statement_queue.StatementQueue.add_statement" class="headerlink" title="Permalink to this definition">¶</a>  

 `append_values_by_key`<span class="sig-paren">(</span>*key*, *values*<span class="sig-paren">)</span><a href="_modules/bi_etl/statement_queue.md#StatementQueue.append_values_by_key" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.statement_queue.StatementQueue.append_values_by_key" class="headerlink" title="Permalink to this definition">¶</a>  

 `execute`<span class="sig-paren">(</span>*connection*<span class="sig-paren">)</span><a href="_modules/bi_etl/statement_queue.md#StatementQueue.execute" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.statement_queue.StatementQueue.execute" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_statement_by_key`<span class="sig-paren">(</span>*key*<span class="sig-paren">)</span><a href="_modules/bi_etl/statement_queue.md#StatementQueue.get_statement_by_key" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.statement_queue.StatementQueue.get_statement_by_key" class="headerlink" title="Permalink to this definition">¶</a>  

 `iter_single_statements`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/statement_queue.md#StatementQueue.iter_single_statements" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.statement_queue.StatementQueue.iter_single_statements" class="headerlink" title="Permalink to this definition">¶</a>  

#### Previous topic

[bi\_etl.memory\_size module](bi_etl.memory_size.md "previous chapter")

#### Next topic

[bi\_etl.statistics module](bi_etl.statistics.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.statistics.md "bi_etl.statistics module") |
-   [previous](bi_etl.memory_size.md "bi_etl.memory_size module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
