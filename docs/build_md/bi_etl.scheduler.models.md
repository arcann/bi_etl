### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.scheduler.queue_io.md "bi_etl.scheduler.queue_io module") |
-   [previous](bi_etl.scheduler.messages.md "bi_etl.scheduler.messages module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.scheduler package](bi_etl.scheduler.md) »

<span id="bi-etl-scheduler-models-module"></span>
bi\_etl.scheduler.models module<a href="#module-bi_etl.scheduler.models" class="headerlink" title="Permalink to this headline">¶</a>
====================================================================================================================================

 *class* `bi_etl.scheduler.models.``ETL_Class`<span class="sig-paren">(</span>*\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/models.md#ETL_Class" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.models.ETL_Class" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: `sqlalchemy.ext.declarative.api.Base`

 `class_name`<a href="#bi_etl.scheduler.models.ETL_Class.class_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `etl_class_id`<a href="#bi_etl.scheduler.models.ETL_Class.etl_class_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `metadata` *= MetaData(bind=None)*<a href="#bi_etl.scheduler.models.ETL_Class.metadata" class="headerlink" title="Permalink to this definition">¶</a>  

 `module_name`<a href="#bi_etl.scheduler.models.ETL_Class.module_name" class="headerlink" title="Permalink to this definition">¶</a>  

<!-- -->

 *class* `bi_etl.scheduler.models.``ETL_Class_Dependency`<span class="sig-paren">(</span>*etl\_class*, *dependent\_on\_etl\_task*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/models.md#ETL_Class_Dependency" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.models.ETL_Class_Dependency" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: `sqlalchemy.ext.declarative.api.Base`

 `dependent_on_etl_class_id`<a href="#bi_etl.scheduler.models.ETL_Class_Dependency.dependent_on_etl_class_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `dependent_on_etl_task`<a href="#bi_etl.scheduler.models.ETL_Class_Dependency.dependent_on_etl_task" class="headerlink" title="Permalink to this definition">¶</a>  

 `etl_class`<a href="#bi_etl.scheduler.models.ETL_Class_Dependency.etl_class" class="headerlink" title="Permalink to this definition">¶</a>  

 `etl_class_id`<a href="#bi_etl.scheduler.models.ETL_Class_Dependency.etl_class_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `metadata` *= MetaData(bind=None)*<a href="#bi_etl.scheduler.models.ETL_Class_Dependency.metadata" class="headerlink" title="Permalink to this definition">¶</a>  

<!-- -->

 *class* `bi_etl.scheduler.models.``ETL_Scheduler`<span class="sig-paren">(</span>*\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/models.md#ETL_Scheduler" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.models.ETL_Scheduler" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: `sqlalchemy.ext.declarative.api.Base`

 `host_name`<a href="#bi_etl.scheduler.models.ETL_Scheduler.host_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `last_heartbeat`<a href="#bi_etl.scheduler.models.ETL_Scheduler.last_heartbeat" class="headerlink" title="Permalink to this definition">¶</a>  

 `metadata` *= MetaData(bind=None)*<a href="#bi_etl.scheduler.models.ETL_Scheduler.metadata" class="headerlink" title="Permalink to this definition">¶</a>  

 `qualified_host_name`<a href="#bi_etl.scheduler.models.ETL_Scheduler.qualified_host_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `scheduler_id`<a href="#bi_etl.scheduler.models.ETL_Scheduler.scheduler_id" class="headerlink" title="Permalink to this definition">¶</a>  

<!-- -->

 *class* `bi_etl.scheduler.models.``ETL_Task_Dependency`<span class="sig-paren">(</span>*task*, *dependent\_on\_task*, *dependent\_reason*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/models.md#ETL_Task_Dependency" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.models.ETL_Task_Dependency" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: `sqlalchemy.ext.declarative.api.Base`

 `current_blocking_flag`<a href="#bi_etl.scheduler.models.ETL_Task_Dependency.current_blocking_flag" class="headerlink" title="Permalink to this definition">¶</a>  

 `dependent_on_task`<a href="#bi_etl.scheduler.models.ETL_Task_Dependency.dependent_on_task" class="headerlink" title="Permalink to this definition">¶</a>  

 `dependent_on_task_id`<a href="#bi_etl.scheduler.models.ETL_Task_Dependency.dependent_on_task_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `dependent_reason`<a href="#bi_etl.scheduler.models.ETL_Task_Dependency.dependent_reason" class="headerlink" title="Permalink to this definition">¶</a>  

 `metadata` *= MetaData(bind=None)*<a href="#bi_etl.scheduler.models.ETL_Task_Dependency.metadata" class="headerlink" title="Permalink to this definition">¶</a>  

 `task`<a href="#bi_etl.scheduler.models.ETL_Task_Dependency.task" class="headerlink" title="Permalink to this definition">¶</a>  

 `task_id`<a href="#bi_etl.scheduler.models.ETL_Task_Dependency.task_id" class="headerlink" title="Permalink to this definition">¶</a>  

<!-- -->

 *class* `bi_etl.scheduler.models.``ETL_Task_Log`<span class="sig-paren">(</span>*\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/models.md#ETL_Task_Log" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.models.ETL_Task_Log" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: `sqlalchemy.ext.declarative.api.Base`

 `log_entry`<a href="#bi_etl.scheduler.models.ETL_Task_Log.log_entry" class="headerlink" title="Permalink to this definition">¶</a>  

 `log_entry_ts`<a href="#bi_etl.scheduler.models.ETL_Task_Log.log_entry_ts" class="headerlink" title="Permalink to this definition">¶</a>  

 `metadata` *= MetaData(bind=None)*<a href="#bi_etl.scheduler.models.ETL_Task_Log.metadata" class="headerlink" title="Permalink to this definition">¶</a>  

 `task_id`<a href="#bi_etl.scheduler.models.ETL_Task_Log.task_id" class="headerlink" title="Permalink to this definition">¶</a>  

<!-- -->

 *class* `bi_etl.scheduler.models.``ETL_Task_Params`<span class="sig-paren">(</span>*param\_name*, *param\_value*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/models.md#ETL_Task_Params" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.models.ETL_Task_Params" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: `sqlalchemy.ext.declarative.api.Base`

 `metadata` *= MetaData(bind=None)*<a href="#bi_etl.scheduler.models.ETL_Task_Params.metadata" class="headerlink" title="Permalink to this definition">¶</a>  

 `param_name`<a href="#bi_etl.scheduler.models.ETL_Task_Params.param_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `param_value`<a href="#bi_etl.scheduler.models.ETL_Task_Params.param_value" class="headerlink" title="Permalink to this definition">¶</a>  

 `task_id`<a href="#bi_etl.scheduler.models.ETL_Task_Params.task_id" class="headerlink" title="Permalink to this definition">¶</a>  

<!-- -->

 *class* `bi_etl.scheduler.models.``ETL_Task_Stats`<span class="sig-paren">(</span>*stat\_name*, *stat\_value*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/models.md#ETL_Task_Stats" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.models.ETL_Task_Stats" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: `sqlalchemy.ext.declarative.api.Base`

 `is_int`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/models.md#ETL_Task_Stats.is_int" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.models.ETL_Task_Stats.is_int" class="headerlink" title="Permalink to this definition">¶</a>  

 `is_row_count`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/models.md#ETL_Task_Stats.is_row_count" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.models.ETL_Task_Stats.is_row_count" class="headerlink" title="Permalink to this definition">¶</a>  

 `metadata` *= MetaData(bind=None)*<a href="#bi_etl.scheduler.models.ETL_Task_Stats.metadata" class="headerlink" title="Permalink to this definition">¶</a>  

 `stat_name`<a href="#bi_etl.scheduler.models.ETL_Task_Stats.stat_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `stat_value`<a href="#bi_etl.scheduler.models.ETL_Task_Stats.stat_value" class="headerlink" title="Permalink to this definition">¶</a>  

 `task_id`<a href="#bi_etl.scheduler.models.ETL_Task_Stats.task_id" class="headerlink" title="Permalink to this definition">¶</a>  

<!-- -->

 *class* `bi_etl.scheduler.models.``ETL_Task_Status_CD`<span class="sig-paren">(</span>*\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/models.md#ETL_Task_Status_CD" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.models.ETL_Task_Status_CD" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: `sqlalchemy.ext.declarative.api.Base`

 `metadata` *= MetaData(bind=None)*<a href="#bi_etl.scheduler.models.ETL_Task_Status_CD.metadata" class="headerlink" title="Permalink to this definition">¶</a>  

 `status_id`<a href="#bi_etl.scheduler.models.ETL_Task_Status_CD.status_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `status_name`<a href="#bi_etl.scheduler.models.ETL_Task_Status_CD.status_name" class="headerlink" title="Permalink to this definition">¶</a>  

<!-- -->

 *class* `bi_etl.scheduler.models.``ETL_Tasks`<span class="sig-paren">(</span>*\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/models.md#ETL_Tasks" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.models.ETL_Tasks" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: `sqlalchemy.ext.declarative.api.Base`

 `Status`<a href="#bi_etl.scheduler.models.ETL_Tasks.Status" class="headerlink" title="Permalink to this definition">¶</a>  

 `ancestors`<a href="#bi_etl.scheduler.models.ETL_Tasks.ancestors" class="headerlink" title="Permalink to this definition">¶</a>  

 `children`<a href="#bi_etl.scheduler.models.ETL_Tasks.children" class="headerlink" title="Permalink to this definition">¶</a>  

 `children_id_list`<a href="#bi_etl.scheduler.models.ETL_Tasks.children_id_list" class="headerlink" title="Permalink to this definition">¶</a>  

 `classname`<a href="#bi_etl.scheduler.models.ETL_Tasks.classname" class="headerlink" title="Permalink to this definition">¶</a>  

 `display_name`<a href="#bi_etl.scheduler.models.ETL_Tasks.display_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `errors`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/models.md#ETL_Tasks.errors" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.models.ETL_Tasks.errors" class="headerlink" title="Permalink to this definition">¶</a>  

 `finished_date`<a href="#bi_etl.scheduler.models.ETL_Tasks.finished_date" class="headerlink" title="Permalink to this definition">¶</a>  

 *static* `get_next_task_id`<span class="sig-paren">(</span>*session*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/models.md#ETL_Tasks.get_next_task_id" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.models.ETL_Tasks.get_next_task_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `log_entries`<a href="#bi_etl.scheduler.models.ETL_Tasks.log_entries" class="headerlink" title="Permalink to this definition">¶</a>  

 `metadata` *= MetaData(bind=None)*<a href="#bi_etl.scheduler.models.ETL_Tasks.metadata" class="headerlink" title="Permalink to this definition">¶</a>  

 `modulename`<a href="#bi_etl.scheduler.models.ETL_Tasks.modulename" class="headerlink" title="Permalink to this definition">¶</a>  

 `parameters`<a href="#bi_etl.scheduler.models.ETL_Tasks.parameters" class="headerlink" title="Permalink to this definition">¶</a>  

 `parent_task_id`<a href="#bi_etl.scheduler.models.ETL_Tasks.parent_task_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `pid`<a href="#bi_etl.scheduler.models.ETL_Tasks.pid" class="headerlink" title="Permalink to this definition">¶</a>  

 `root_task_id`<a href="#bi_etl.scheduler.models.ETL_Tasks.root_task_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `scheduler`<a href="#bi_etl.scheduler.models.ETL_Tasks.scheduler" class="headerlink" title="Permalink to this definition">¶</a>  

 `scheduler_id`<a href="#bi_etl.scheduler.models.ETL_Tasks.scheduler_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `started_date`<a href="#bi_etl.scheduler.models.ETL_Tasks.started_date" class="headerlink" title="Permalink to this definition">¶</a>  

 `stats`<a href="#bi_etl.scheduler.models.ETL_Tasks.stats" class="headerlink" title="Permalink to this definition">¶</a>  

 `status_cd`<a href="#bi_etl.scheduler.models.ETL_Tasks.status_cd" class="headerlink" title="Permalink to this definition">¶</a>  

 `status_id`<a href="#bi_etl.scheduler.models.ETL_Tasks.status_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `submit_by_user_id`<a href="#bi_etl.scheduler.models.ETL_Tasks.submit_by_user_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `submitted_date`<a href="#bi_etl.scheduler.models.ETL_Tasks.submitted_date" class="headerlink" title="Permalink to this definition">¶</a>  

 `summary_message`<a href="#bi_etl.scheduler.models.ETL_Tasks.summary_message" class="headerlink" title="Permalink to this definition">¶</a>  

 `task_id`<a href="#bi_etl.scheduler.models.ETL_Tasks.task_id" class="headerlink" title="Permalink to this definition">¶</a>  

<!-- -->

 `bi_etl.scheduler.models.``ping_connection`<span class="sig-paren">(</span>*dbapi\_connection*, *connection\_record*, *connection\_proxy*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/models.md#ping_connection" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.models.ping_connection" class="headerlink" title="Permalink to this definition">¶</a>  
Test connections before they are used (finds disconnected sessions)

|             |                              |
|-------------|------------------------------|
| Parameters: | -   **dbapi\_connection** –  
  -   **connection\_record** –  
  -   **connection\_proxy** –   |

#### Previous topic

[bi\_etl.scheduler.messages module](bi_etl.scheduler.messages.md "previous chapter")

#### Next topic

[bi\_etl.scheduler.queue\_io module](bi_etl.scheduler.queue_io.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.scheduler.queue_io.md "bi_etl.scheduler.queue_io module") |
-   [previous](bi_etl.scheduler.messages.md "bi_etl.scheduler.messages module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.scheduler package](bi_etl.scheduler.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
