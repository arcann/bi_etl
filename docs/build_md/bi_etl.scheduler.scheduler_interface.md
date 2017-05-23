### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.scheduler.sdtout_queue.md "bi_etl.scheduler.sdtout_queue module") |
-   [previous](bi_etl.scheduler.scheduler.md "bi_etl.scheduler.scheduler module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.scheduler package](bi_etl.scheduler.md) »

<span id="bi-etl-scheduler-scheduler-interface-module"></span>
bi\_etl.scheduler.scheduler\_interface module<a href="#module-bi_etl.scheduler.scheduler_interface" class="headerlink" title="Permalink to this headline">¶</a>
===============================================================================================================================================================

Created on May 20, 2015

@author: woodd

 *class* `bi_etl.scheduler.scheduler_interface.``SchedulerInterface`<span class="sig-paren">(</span>*session=None*, *config: configparser.ConfigParser = None*, *log=None*, *log\_name=None*, *scheduler\_id=None*, *allow\_create=False*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="https://docs.python.org/2/library/functions.md#object" class="reference external" title="(in Python v2.7)"><code class="xref py py-class docutils literal">object</code></a>

Light scheduler interface that only interacts with the database.

 `CLASS_VERSION` *= 1.0*<a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.CLASS_VERSION" class="headerlink" title="Permalink to this definition">¶</a>  

 `CONFIG_SECTION` *= 'Scheduler'*<a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.CONFIG_SECTION" class="headerlink" title="Permalink to this definition">¶</a>  

 `ETL_Task_Log`<a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.ETL_Task_Log" class="headerlink" title="Permalink to this definition">¶</a>  

 `ETL_Task_Params`<a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.ETL_Task_Params" class="headerlink" title="Permalink to this definition">¶</a>  

 `ETL_Task_Stats`<a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.ETL_Task_Stats" class="headerlink" title="Permalink to this definition">¶</a>  

 `ETL_Task_Status_CD`<a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.ETL_Task_Status_CD" class="headerlink" title="Permalink to this definition">¶</a>  

 `ETL_Tasks`<a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.ETL_Tasks" class="headerlink" title="Permalink to this definition">¶</a>  

 `SCHEDULER_ETL_JOBS_PACKAGE` *= 'bi\_etl.scheduler.scheduler\_etl\_jobs'*<a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.SCHEDULER_ETL_JOBS_PACKAGE" class="headerlink" title="Permalink to this definition">¶</a>  

 `SHARED_etl_task_classes` *= {}*<a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.SHARED_etl_task_classes" class="headerlink" title="Permalink to this definition">¶</a>  

 `add_task_by_class`<span class="sig-paren">(</span>*etl\_task\_class\_type*, *display\_name=None*, *parent\_task\_id=None*, *root\_task\_id=None*, *scheduler\_id=None*, *parameters=None*, *submit\_by\_user\_id=None*, *commit=True*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.add_task_by_class" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.add_task_by_class" class="headerlink" title="Permalink to this definition">¶</a>  
Add a task to the scheduler using an instance of the task class type.

|              |                                                                                                                            |
|--------------|----------------------------------------------------------------------------------------------------------------------------|
| Returns:     | **task\_id**                                                                                                               |
| Return type: | <a href="https://docs.python.org/2/library/functions.md#int" class="reference external" title="(in Python v2.7)">int</a> |

 `add_task_by_exact_name`<span class="sig-paren">(</span>*module\_name*, *class\_name=None*, *display\_name=None*, *parent\_task\_id=None*, *root\_task\_id=None*, *scheduler\_id=None*, *parameters=None*, *submit\_by\_user\_id=None*, *commit=True*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.add_task_by_exact_name" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.add_task_by_exact_name" class="headerlink" title="Permalink to this definition">¶</a>  
Add a task to the scheduler using a module name

 `add_task_by_partial_name`<span class="sig-paren">(</span>*partial\_module\_name*, *display\_name=None*, *parent\_task\_id=None*, *root\_task\_id=None*, *scheduler\_id=None*, *parameters=None*, *submit\_by\_user\_id=None*, *commit=True*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.add_task_by_partial_name" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.add_task_by_partial_name" class="headerlink" title="Permalink to this definition">¶</a>  
Add a task to the scheduler using the module\_name (partial) and optionally class\_name

|              |                                                                                                                            |
|--------------|----------------------------------------------------------------------------------------------------------------------------|
| Returns:     | **task\_id**                                                                                                               |
| Return type: | <a href="https://docs.python.org/2/library/functions.md#int" class="reference external" title="(in Python v2.7)">int</a> |

 `add_task_paramter`<span class="sig-paren">(</span>*task*, *parameter\_name*, *parameter\_value*, *commit=True*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.add_task_paramter" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.add_task_paramter" class="headerlink" title="Permalink to this definition">¶</a>  

 `add_task_paramters`<span class="sig-paren">(</span>*task*, *parameters*, *commit=True*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.add_task_paramters" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.add_task_paramters" class="headerlink" title="Permalink to this definition">¶</a>  

 `find_etl_class_instance`<span class="sig-paren">(</span>*partial\_module\_name*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.find_etl_class_instance" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.find_etl_class_instance" class="headerlink" title="Permalink to this definition">¶</a>  

 `find_etl_class_name`<span class="sig-paren">(</span>*partial\_module\_name*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.find_etl_class_name" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.find_etl_class_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `find_etl_class_type`<span class="sig-paren">(</span>*partial\_module\_name*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.find_etl_class_type" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.find_etl_class_type" class="headerlink" title="Permalink to this definition">¶</a>  

 `find_etl_classes`<span class="sig-paren">(</span>*partial\_module\_name*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.find_etl_classes" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.find_etl_classes" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_etl_class_instance`<span class="sig-paren">(</span>*qualified\_name*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.get_etl_class_instance" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.get_etl_class_instance" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_heartbeat_age_timedelta`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.get_heartbeat_age_timedelta" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.get_heartbeat_age_timedelta" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_heartbeat_time`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.get_heartbeat_time" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.get_heartbeat_time" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_jobs_by_root_id`<span class="sig-paren">(</span>*root\_task\_id*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.get_jobs_by_root_id" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.get_jobs_by_root_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_next_task_id`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.get_next_task_id" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.get_next_task_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_scheduler_id_for_host`<span class="sig-paren">(</span>*qualified\_host\_name=None*, *allow\_create=False*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.get_scheduler_id_for_host" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.get_scheduler_id_for_host" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_scheduler_row_for_id`<span class="sig-paren">(</span>*scheduler\_id*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.get_scheduler_row_for_id" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.get_scheduler_row_for_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_status_code_list`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.get_status_code_list" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.get_status_code_list" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_task_parameter_dict`<span class="sig-paren">(</span>*task*<span class="sig-paren">)</span> → dict<a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.get_task_parameter_dict" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.get_task_parameter_dict" class="headerlink" title="Permalink to this definition">¶</a>  
|              |                                                                                                                                                                                                                                                                                                                            |
|--------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters:  | **task** (<a href="https://docs.python.org/2/library/functions.md#int" class="reference external" title="(in Python v2.7)"><em>int</em></a> *or* <a href="bi_etl.scheduler.models.md#bi_etl.scheduler.models.ETL_Tasks" class="reference internal" title="bi_etl.scheduler.models.ETL_Tasks"><em>ETL_Tasks</em></a>) – |
| Returns:     |                                                                                                                                                                                                                                                                                                                            |
| Return type: | <a href="https://docs.python.org/2/library/stdtypes.md#dict" class="reference external" title="(in Python v2.7)">dict</a>                                                                                                                                                                                                |

 `get_task_record`<span class="sig-paren">(</span>*task\_id*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.get_task_record" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.get_task_record" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_task_status`<span class="sig-paren">(</span>*task\_id*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.get_task_status" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.get_task_status" class="headerlink" title="Permalink to this definition">¶</a>  
Gets the Status of a task

|              |                                                                                                                                                                            |
|--------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Returns:     | **status\_of\_task**                                                                                                                                                       |
| Return type: | <a href="bi_etl.scheduler.status.md#bi_etl.scheduler.status.Status" class="reference internal" title="bi_etl.scheduler.status.Status">bi_etl.scheduler.status.Status</a> |

 `heatbeat_now`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.heatbeat_now" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.heatbeat_now" class="headerlink" title="Permalink to this definition">¶</a>  

 `load_parameters`<span class="sig-paren">(</span>*etl\_task*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.load_parameters" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.load_parameters" class="headerlink" title="Permalink to this definition">¶</a>  
This is done in the etl\_task thread/process (called by run method) so that the parameters don’t have to be loaded into the scheduler thread or passed between threads/processes.

 `qualified_host_name`<a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.qualified_host_name" class="headerlink" title="Permalink to this definition">¶</a>  
Gets the qualified host name of the scheduler server.

 `scan_etl_classes`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.scan_etl_classes" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.scan_etl_classes" class="headerlink" title="Permalink to this definition">¶</a>  

 `scan_etl_classes_performed` *= False*<a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.scan_etl_classes_performed" class="headerlink" title="Permalink to this definition">¶</a>  

 `wait_for_task`<span class="sig-paren">(</span>*task\_id*, *check\_interval=1*, *max\_wait=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler_interface.md#SchedulerInterface.wait_for_task" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler_interface.SchedulerInterface.wait_for_task" class="headerlink" title="Permalink to this definition">¶</a>  
Waits for a task to finish.

|              |                                                                                                                                                                                                                                                                                   |
|--------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters:  | -   **task\_id** (<a href="https://docs.python.org/2/library/functions.md#int" class="reference external" title="(in Python v2.7)"><em>int</em></a>) – The task\_id to wait for                                                                                                 
  -   **check\_interval** (<a href="https://docs.python.org/2/library/functions.md#float" class="reference external" title="(in Python v2.7)"><em>float</em></a>) – How many seconds to wait between checks. The argument may be a floating point number for subsecond precision.  
  -   **max\_wait** (<a href="https://docs.python.org/2/library/functions.md#float" class="reference external" title="(in Python v2.7)"><em>float</em></a>) – The maximum seconds to wait for the job to finish. If None or 0, will wait indefinitely.                             |
| Returns:     | **status\_of\_task**                                                                                                                                                                                                                                                              |
| Return type: | <a href="bi_etl.scheduler.status.md#bi_etl.scheduler.status.Status" class="reference internal" title="bi_etl.scheduler.status.Status">bi_etl.scheduler.status.Status</a>                                                                                                        |

#### Previous topic

[bi\_etl.scheduler.scheduler module](bi_etl.scheduler.scheduler.md "previous chapter")

#### Next topic

[bi\_etl.scheduler.sdtout\_queue module](bi_etl.scheduler.sdtout_queue.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.scheduler.sdtout_queue.md "bi_etl.scheduler.sdtout_queue module") |
-   [previous](bi_etl.scheduler.scheduler.md "bi_etl.scheduler.scheduler module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.scheduler package](bi_etl.scheduler.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
