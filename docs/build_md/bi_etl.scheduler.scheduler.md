### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.scheduler.scheduler_interface.md "bi_etl.scheduler.scheduler_interface module") |
-   [previous](bi_etl.scheduler.queue_io.md "bi_etl.scheduler.queue_io module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.scheduler package](bi_etl.scheduler.md) »

<span id="bi-etl-scheduler-scheduler-module"></span>
bi\_etl.scheduler.scheduler module<a href="#module-bi_etl.scheduler.scheduler" class="headerlink" title="Permalink to this headline">¶</a>
==========================================================================================================================================

Created on Apr 14, 2015

@author: woodd

 *class* `bi_etl.scheduler.scheduler.``Scheduler`<a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="bi_etl.scheduler.scheduler_interface.md#bi_etl.scheduler.scheduler_interface.SchedulerInterface" class="reference internal" title="bi_etl.scheduler.scheduler_interface.SchedulerInterface"><code class="xref py py-class docutils literal">bi_etl.scheduler.scheduler_interface.SchedulerInterface</code></a>

Full-scheduler object with memory of active jobs.

 `CLASS_VERSION` *= 1.0*<a href="#bi_etl.scheduler.scheduler.Scheduler.CLASS_VERSION" class="headerlink" title="Permalink to this definition">¶</a>  

 `CONFIG_SECTION` *= 'Scheduler'*<a href="#bi_etl.scheduler.scheduler.Scheduler.CONFIG_SECTION" class="headerlink" title="Permalink to this definition">¶</a>  

 `ETL_Task_Log`<a href="#bi_etl.scheduler.scheduler.Scheduler.ETL_Task_Log" class="headerlink" title="Permalink to this definition">¶</a>  

 `ETL_Task_Params`<a href="#bi_etl.scheduler.scheduler.Scheduler.ETL_Task_Params" class="headerlink" title="Permalink to this definition">¶</a>  

 `ETL_Task_Stats`<a href="#bi_etl.scheduler.scheduler.Scheduler.ETL_Task_Stats" class="headerlink" title="Permalink to this definition">¶</a>  

 `ETL_Task_Status_CD`<a href="#bi_etl.scheduler.scheduler.Scheduler.ETL_Task_Status_CD" class="headerlink" title="Permalink to this definition">¶</a>  

 `ETL_Tasks`<a href="#bi_etl.scheduler.scheduler.Scheduler.ETL_Tasks" class="headerlink" title="Permalink to this definition">¶</a>  

 `MAX_DEPENDENTS_DEPTH` *= 100*<a href="#bi_etl.scheduler.scheduler.Scheduler.MAX_DEPENDENTS_DEPTH" class="headerlink" title="Permalink to this definition">¶</a>  

 `SCHEDULER_ETL_JOBS_PACKAGE` *= 'bi\_etl.scheduler.scheduler\_etl\_jobs'*<a href="#bi_etl.scheduler.scheduler.Scheduler.SCHEDULER_ETL_JOBS_PACKAGE" class="headerlink" title="Permalink to this definition">¶</a>  

 `SHARED_etl_task_classes` *= {}*<a href="#bi_etl.scheduler.scheduler.Scheduler.SHARED_etl_task_classes" class="headerlink" title="Permalink to this definition">¶</a>  

 `add_dependency`<span class="sig-paren">(</span>*etl\_task*, *dependent\_task*, *dependent\_reason*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.add_dependency" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.add_dependency" class="headerlink" title="Permalink to this definition">¶</a>  

 `add_log_message`<span class="sig-paren">(</span>*etl\_task*, *msg*, *allow\_duplicates=True*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.add_log_message" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.add_log_message" class="headerlink" title="Permalink to this definition">¶</a>  

 `add_task_by_class`<span class="sig-paren">(</span>*etl\_task\_class\_type*, *display\_name=None*, *parent\_task\_id=None*, *root\_task\_id=None*, *scheduler\_id=None*, *parameters=None*, *submit\_by\_user\_id=None*, *commit=True*<span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.add_task_by_class" class="headerlink" title="Permalink to this definition">¶</a>  
Add a task to the scheduler using an instance of the task class type.

|              |                                                                                                                            |
|--------------|----------------------------------------------------------------------------------------------------------------------------|
| Returns:     | **task\_id**                                                                                                               |
| Return type: | <a href="https://docs.python.org/2/library/functions.md#int" class="reference external" title="(in Python v2.7)">int</a> |

 `add_task_by_exact_name`<span class="sig-paren">(</span>*module\_name*, *class\_name=None*, *display\_name=None*, *parent\_task\_id=None*, *root\_task\_id=None*, *scheduler\_id=None*, *parameters=None*, *submit\_by\_user\_id=None*, *commit=True*<span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.add_task_by_exact_name" class="headerlink" title="Permalink to this definition">¶</a>  
Add a task to the scheduler using a module name

 `add_task_by_partial_name`<span class="sig-paren">(</span>*partial\_module\_name*, *display\_name=None*, *parent\_task\_id=None*, *root\_task\_id=None*, *scheduler\_id=None*, *parameters=None*, *submit\_by\_user\_id=None*, *commit=True*<span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.add_task_by_partial_name" class="headerlink" title="Permalink to this definition">¶</a>  
Add a task to the scheduler using the module\_name (partial) and optionally class\_name

|              |                                                                                                                            |
|--------------|----------------------------------------------------------------------------------------------------------------------------|
| Returns:     | **task\_id**                                                                                                               |
| Return type: | <a href="https://docs.python.org/2/library/functions.md#int" class="reference external" title="(in Python v2.7)">int</a> |

 `add_task_paramter`<span class="sig-paren">(</span>*task*, *parameter\_name*, *parameter\_value*, *commit=True*<span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.add_task_paramter" class="headerlink" title="Permalink to this definition">¶</a>  

 `add_task_paramters`<span class="sig-paren">(</span>*task*, *parameters*, *commit=True*<span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.add_task_paramters" class="headerlink" title="Permalink to this definition">¶</a>  

 `add_task_to_active`<span class="sig-paren">(</span>*etl\_task*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.add_task_to_active" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.add_task_to_active" class="headerlink" title="Permalink to this definition">¶</a>  

 `append_task_summary_message`<span class="sig-paren">(</span>*etl\_task*, *summary\_message*, *commit=True*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.append_task_summary_message" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.append_task_summary_message" class="headerlink" title="Permalink to this definition">¶</a>  
Append to the tasks summary message.

 `check_dependencies`<span class="sig-paren">(</span>*etl\_task*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.check_dependencies" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.check_dependencies" class="headerlink" title="Permalink to this definition">¶</a>  

 `check_for_cpu`<span class="sig-paren">(</span>*etl\_task*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.check_for_cpu" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.check_for_cpu" class="headerlink" title="Permalink to this definition">¶</a>  
Checks for available CPU, if available it STARTS THE TASK and returns True. If not it returns False

 `check_for_new_task_commands`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.check_for_new_task_commands" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.check_for_new_task_commands" class="headerlink" title="Permalink to this definition">¶</a>  
Looks in the database repository for new task commands:  
-   new task: Creates an ETLTask instance, and checks it’s predesssors.
-   stop\_requested: Sends a stop signal to the task
-   kill\_requested: Sends s SIGKILL to terminate the task

 `check_for_previous_instance_tasks`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.check_for_previous_instance_tasks" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.check_for_previous_instance_tasks" class="headerlink" title="Permalink to this definition">¶</a>  
Looks in the database repository for tasks from a previous instance.

 `check_for_required_table_maintenance`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.check_for_required_table_maintenance" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.check_for_required_table_maintenance" class="headerlink" title="Permalink to this definition">¶</a>  

 `check_if_done`<span class="sig-paren">(</span>*etl\_task*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.check_if_done" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.check_if_done" class="headerlink" title="Permalink to this definition">¶</a>  

 `check_if_log_message_flush_needed`<span class="sig-paren">(</span>*etl\_task*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.check_if_log_message_flush_needed" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.check_if_log_message_flush_needed" class="headerlink" title="Permalink to this definition">¶</a>  

 `delete_old_run_logs`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.delete_old_run_logs" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.delete_old_run_logs" class="headerlink" title="Permalink to this definition">¶</a>  

 `find_etl_class_instance`<span class="sig-paren">(</span>*partial\_module\_name*<span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.find_etl_class_instance" class="headerlink" title="Permalink to this definition">¶</a>  

 `find_etl_class_name`<span class="sig-paren">(</span>*partial\_module\_name*<span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.find_etl_class_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `find_etl_class_type`<span class="sig-paren">(</span>*partial\_module\_name*<span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.find_etl_class_type" class="headerlink" title="Permalink to this definition">¶</a>  

 `find_etl_classes`<span class="sig-paren">(</span>*partial\_module\_name*<span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.find_etl_classes" class="headerlink" title="Permalink to this definition">¶</a>  

 `flush_log_messages`<span class="sig-paren">(</span>*etl\_task*, *time\_now=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.flush_log_messages" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.flush_log_messages" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_etl_class_instance`<span class="sig-paren">(</span>*qualified\_name*<span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.get_etl_class_instance" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_etl_tasks_by_name`<span class="sig-paren">(</span>*etl\_task\_name*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.get_etl_tasks_by_name" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.get_etl_tasks_by_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_heartbeat_age_timedelta`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.get_heartbeat_age_timedelta" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_heartbeat_time`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.get_heartbeat_time" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_jobs_by_root_id`<span class="sig-paren">(</span>*root\_task\_id*<span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.get_jobs_by_root_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_next_task_id`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.get_next_task_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_scheduler_id_for_host`<span class="sig-paren">(</span>*qualified\_host\_name=None*, *allow\_create=False*<span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.get_scheduler_id_for_host" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_scheduler_row_for_id`<span class="sig-paren">(</span>*scheduler\_id*<span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.get_scheduler_row_for_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_status_code_list`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.get_status_code_list" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_task_by_id`<span class="sig-paren">(</span>*etl\_task\_id*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.get_task_by_id" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.get_task_by_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_task_parameter_dict`<span class="sig-paren">(</span>*task*<span class="sig-paren">)</span> → dict<a href="#bi_etl.scheduler.scheduler.Scheduler.get_task_parameter_dict" class="headerlink" title="Permalink to this definition">¶</a>  
|              |                                                                                                                                                                                                                                                                                                                            |
|--------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters:  | **task** (<a href="https://docs.python.org/2/library/functions.md#int" class="reference external" title="(in Python v2.7)"><em>int</em></a> *or* <a href="bi_etl.scheduler.models.md#bi_etl.scheduler.models.ETL_Tasks" class="reference internal" title="bi_etl.scheduler.models.ETL_Tasks"><em>ETL_Tasks</em></a>) – |
| Returns:     |                                                                                                                                                                                                                                                                                                                            |
| Return type: | <a href="https://docs.python.org/2/library/stdtypes.md#dict" class="reference external" title="(in Python v2.7)">dict</a>                                                                                                                                                                                                |

 `get_task_record`<span class="sig-paren">(</span>*task\_id*<span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.get_task_record" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_task_status`<span class="sig-paren">(</span>*task\_id*<span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.get_task_status" class="headerlink" title="Permalink to this definition">¶</a>  
Gets the Status of a task

|              |                                                                                                                                                                            |
|--------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Returns:     | **status\_of\_task**                                                                                                                                                       |
| Return type: | <a href="bi_etl.scheduler.status.md#bi_etl.scheduler.status.Status" class="reference internal" title="bi_etl.scheduler.status.Status">bi_etl.scheduler.status.Status</a> |

 `heatbeat_now`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.heatbeat_now" class="headerlink" title="Permalink to this definition">¶</a>  

 `kill_task`<span class="sig-paren">(</span>*etl\_task*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.kill_task" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.kill_task" class="headerlink" title="Permalink to this definition">¶</a>  

 `load_parameters`<span class="sig-paren">(</span>*etl\_task*<span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.load_parameters" class="headerlink" title="Permalink to this definition">¶</a>  
This is done in the etl\_task thread/process (called by run method) so that the parameters don’t have to be loaded into the scheduler thread or passed between threads/processes.

 `process_statistics`<span class="sig-paren">(</span>*etl\_task*, *stats*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.process_statistics" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.process_statistics" class="headerlink" title="Permalink to this definition">¶</a>  

 `purge_old_lager_parameters`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.purge_old_lager_parameters" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.purge_old_lager_parameters" class="headerlink" title="Permalink to this definition">¶</a>  

 `qualified_host_name`<a href="#bi_etl.scheduler.scheduler.Scheduler.qualified_host_name" class="headerlink" title="Permalink to this definition">¶</a>  
Gets the qualified host name of the scheduler server.

 `read_child_messages`<span class="sig-paren">(</span>*etl\_task*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.read_child_messages" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.read_child_messages" class="headerlink" title="Permalink to this definition">¶</a>  

 `remove_active_task_record`<span class="sig-paren">(</span>*etl\_task*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.remove_active_task_record" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.remove_active_task_record" class="headerlink" title="Permalink to this definition">¶</a>  

 `run_task`<span class="sig-paren">(</span>*etl\_task*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.run_task" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.run_task" class="headerlink" title="Permalink to this definition">¶</a>  

 `scan_etl_classes`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.scan_etl_classes" class="headerlink" title="Permalink to this definition">¶</a>  

 `scan_etl_classes_performed` *= False*<a href="#bi_etl.scheduler.scheduler.Scheduler.scan_etl_classes_performed" class="headerlink" title="Permalink to this definition">¶</a>  

 `send_task_message`<span class="sig-paren">(</span>*etl\_task*, *message*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.send_task_message" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.send_task_message" class="headerlink" title="Permalink to this definition">¶</a>  

 `set_task_status`<span class="sig-paren">(</span>*etl\_task*, *new\_status*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.set_task_status" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.set_task_status" class="headerlink" title="Permalink to this definition">¶</a>  

 `set_task_summary_message`<span class="sig-paren">(</span>*etl\_task*, *summary\_message*, *commit=False*, *from\_client=False*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.set_task_summary_message" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.set_task_summary_message" class="headerlink" title="Permalink to this definition">¶</a>  
set the tasks summary message. Note: Since this is often called on conjunction with set\_task\_status, we default to no commit here.

 `start_monitoring`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.start_monitoring" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.start_monitoring" class="headerlink" title="Permalink to this definition">¶</a>  

 `stop_task`<span class="sig-paren">(</span>*etl\_task*<span class="sig-paren">)</span><a href="_modules/bi_etl/scheduler/scheduler.md#Scheduler.stop_task" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.scheduler.scheduler.Scheduler.stop_task" class="headerlink" title="Permalink to this definition">¶</a>  

 `wait_for_task`<span class="sig-paren">(</span>*task\_id*, *check\_interval=1*, *max\_wait=None*<span class="sig-paren">)</span><a href="#bi_etl.scheduler.scheduler.Scheduler.wait_for_task" class="headerlink" title="Permalink to this definition">¶</a>  
Waits for a task to finish.

|              |                                                                                                                                                                                                                                                                                   |
|--------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters:  | -   **task\_id** (<a href="https://docs.python.org/2/library/functions.md#int" class="reference external" title="(in Python v2.7)"><em>int</em></a>) – The task\_id to wait for                                                                                                 
  -   **check\_interval** (<a href="https://docs.python.org/2/library/functions.md#float" class="reference external" title="(in Python v2.7)"><em>float</em></a>) – How many seconds to wait between checks. The argument may be a floating point number for subsecond precision.  
  -   **max\_wait** (<a href="https://docs.python.org/2/library/functions.md#float" class="reference external" title="(in Python v2.7)"><em>float</em></a>) – The maximum seconds to wait for the job to finish. If None or 0, will wait indefinitely.                             |
| Returns:     | **status\_of\_task**                                                                                                                                                                                                                                                              |
| Return type: | <a href="bi_etl.scheduler.status.md#bi_etl.scheduler.status.Status" class="reference internal" title="bi_etl.scheduler.status.Status">bi_etl.scheduler.status.Status</a>                                                                                                        |

#### Previous topic

[bi\_etl.scheduler.queue\_io module](bi_etl.scheduler.queue_io.md "previous chapter")

#### Next topic

[bi\_etl.scheduler.scheduler\_interface module](bi_etl.scheduler.scheduler_interface.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.scheduler.scheduler_interface.md "bi_etl.scheduler.scheduler_interface module") |
-   [previous](bi_etl.scheduler.queue_io.md "bi_etl.scheduler.queue_io module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.scheduler package](bi_etl.scheduler.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
