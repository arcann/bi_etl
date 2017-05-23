### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.scheduler.task.md "bi_etl.scheduler.task module") |
-   [previous](bi_etl.scheduler.special_tasks.md "bi_etl.scheduler.special_tasks module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.scheduler package](bi_etl.scheduler.md) »

<span id="bi-etl-scheduler-status-module"></span>
bi\_etl.scheduler.status module<a href="#module-bi_etl.scheduler.status" class="headerlink" title="Permalink to this headline">¶</a>
====================================================================================================================================

Created on Dec 23, 2015

@author: woodd

 *class* `bi_etl.scheduler.status.``Status`<a href="_modules/bi_etl/scheduler/status.md#Status" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.status.Status" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: `enum.IntEnum`

An enumeration.

 `ancestor_failed` *= -98*<a href="#bi_etl.scheduler.status.Status.ancestor_failed" class="headerlink" title="Permalink to this definition">¶</a>  

 `ancestors_running` *= 11*<a href="#bi_etl.scheduler.status.Status.ancestors_running" class="headerlink" title="Permalink to this definition">¶</a>  

 `cancelled` *= -5*<a href="#bi_etl.scheduler.status.Status.cancelled" class="headerlink" title="Permalink to this definition">¶</a>  

 `failed` *= -99*<a href="#bi_etl.scheduler.status.Status.failed" class="headerlink" title="Permalink to this definition">¶</a>  

 `kill_requested` *= 31*<a href="#bi_etl.scheduler.status.Status.kill_requested" class="headerlink" title="Permalink to this definition">¶</a>  

 `kill_signal_sent` *= 32*<a href="#bi_etl.scheduler.status.Status.kill_signal_sent" class="headerlink" title="Permalink to this definition">¶</a>  

 `killed` *= -30*<a href="#bi_etl.scheduler.status.Status.killed" class="headerlink" title="Permalink to this definition">¶</a>  

 `new` *= 0*<a href="#bi_etl.scheduler.status.Status.new" class="headerlink" title="Permalink to this definition">¶</a>  

 `running` *= 10*<a href="#bi_etl.scheduler.status.Status.running" class="headerlink" title="Permalink to this definition">¶</a>  

 `stop_requested` *= 21*<a href="#bi_etl.scheduler.status.Status.stop_requested" class="headerlink" title="Permalink to this definition">¶</a>  

 `stop_signal_sent` *= 22*<a href="#bi_etl.scheduler.status.Status.stop_signal_sent" class="headerlink" title="Permalink to this definition">¶</a>  

 `stopped` *= -20*<a href="#bi_etl.scheduler.status.Status.stopped" class="headerlink" title="Permalink to this definition">¶</a>  

 `succeeded` *= 100*<a href="#bi_etl.scheduler.status.Status.succeeded" class="headerlink" title="Permalink to this definition">¶</a>  

 `waiting_for_cpu` *= 1*<a href="#bi_etl.scheduler.status.Status.waiting_for_cpu" class="headerlink" title="Permalink to this definition">¶</a>  

 `waiting_for_dependencies` *= 2*<a href="#bi_etl.scheduler.status.Status.waiting_for_dependencies" class="headerlink" title="Permalink to this definition">¶</a>  

 `waiting_for_workflow` *= 3*<a href="#bi_etl.scheduler.status.Status.waiting_for_workflow" class="headerlink" title="Permalink to this definition">¶</a>  

#### Previous topic

[bi\_etl.scheduler.special\_tasks module](bi_etl.scheduler.special_tasks.md "previous chapter")

#### Next topic

[bi\_etl.scheduler.task module](bi_etl.scheduler.task.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.scheduler.task.md "bi_etl.scheduler.task module") |
-   [previous](bi_etl.scheduler.special_tasks.md "bi_etl.scheduler.special_tasks module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.scheduler package](bi_etl.scheduler.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
