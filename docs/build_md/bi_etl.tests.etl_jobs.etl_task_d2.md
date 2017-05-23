### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.tests.etl_jobs.etl_task_d3.md "bi_etl.tests.etl_jobs.etl_task_d3 module") |
-   [previous](bi_etl.tests.etl_jobs.etl_task_d1.md "bi_etl.tests.etl_jobs.etl_task_d1 module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.tests package](bi_etl.tests.md) »
-   [bi\_etl.tests.etl\_jobs package](bi_etl.tests.etl_jobs.md) »

<span id="bi-etl-tests-etl-jobs-etl-task-d2-module"></span>
bi\_etl.tests.etl\_jobs.etl\_task\_d2 module<a href="#module-bi_etl.tests.etl_jobs.etl_task_d2" class="headerlink" title="Permalink to this headline">¶</a>
===========================================================================================================================================================

Created on Apr 18, 2016

@author: woodd

 *class* `bi_etl.tests.etl_jobs.etl_task_d2.``ETL_Task_D2`<span class="sig-paren">(</span>*task\_id=None*, *parent\_task\_id=None*, *root\_task\_id=None*, *scheduler=None*, *task\_rec=None*, *config=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/tests/etl_jobs/etl_task_d2.md#ETL_Task_D2" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="bi_etl.tests.etl_jobs.etl_test_task_base.md#bi_etl.tests.etl_jobs.etl_test_task_base.ETL_Test_Task_Base" class="reference internal" title="bi_etl.tests.etl_jobs.etl_test_task_base.ETL_Test_Task_Base"><code class="xref py py-class docutils literal">bi_etl.tests.etl_jobs.etl_test_task_base.ETL_Test_Task_Base</code></a>

 `CLASS_VERSION` *= 1.0*<a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.CLASS_VERSION" class="headerlink" title="Permalink to this definition">¶</a>  

 `DEFAULT_NO_MAIL` *= False*<a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.DEFAULT_NO_MAIL" class="headerlink" title="Permalink to this definition">¶</a>  

 `add_child_task_by_partial_name_to_scheduler`<span class="sig-paren">(</span>*partial\_module\_name*, *parameters=None*, *display\_name=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.add_child_task_by_partial_name_to_scheduler" class="headerlink" title="Permalink to this definition">¶</a>  
Start a new task on the :class\`bi\_etl.scheduler.scheduler.Scheduler\` that will be a child of this task.

 `add_child_task_to_scheduler`<span class="sig-paren">(</span>*etl\_task\_class\_type*, *parameters=None*, *display\_name=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.add_child_task_to_scheduler" class="headerlink" title="Permalink to this definition">¶</a>  
Start a new task on the :class\`bi\_etl.scheduler.scheduler.Scheduler\` that will be a child of this task.

 `add_database`<span class="sig-paren">(</span>*database\_object*<span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.add_database" class="headerlink" title="Permalink to this definition">¶</a>  

 `add_parameter`<span class="sig-paren">(</span>*param\_name: str*, *param\_value: object*, *local\_only: bool = False*, *commit: bool = True*<span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.add_parameter" class="headerlink" title="Permalink to this definition">¶</a>  

 `add_parameters`<span class="sig-paren">(</span>*local\_only=False*, *commit=True*, *\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.add_parameters" class="headerlink" title="Permalink to this definition">¶</a>  

 `allow_concurrent_runs`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.allow_concurrent_runs" class="headerlink" title="Permalink to this definition">¶</a>  

 `children`<a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.children" class="headerlink" title="Permalink to this definition">¶</a>  

 `close`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.close" class="headerlink" title="Permalink to this definition">¶</a>  
Cleanup the task. Close any registered objects, close any database connections.

 `config`<a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.config" class="headerlink" title="Permalink to this definition">¶</a>  
Get the task configuration object. If it was not passed in, it will be read from the users folder.

 `debug_sql`<span class="sig-paren">(</span>*mode: int = True*<span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.debug_sql" class="headerlink" title="Permalink to this definition">¶</a>  
Control the output of sqlalchemy engine

|             |                                                                          |
|-------------|--------------------------------------------------------------------------|
| Parameters: | **mode** – Boolean (debug if True, Error if false) or int logging level. |

 `depends_on`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/etl_jobs/etl_task_d2.md#ETL_Task_D2.depends_on" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.depends_on" class="headerlink" title="Permalink to this definition">¶</a>  

 `display_name`<a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.display_name" class="headerlink" title="Permalink to this definition">¶</a>  

 `finish`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.finish" class="headerlink" title="Permalink to this definition">¶</a>  
Placeholder for post-load cleanup. This might be useful for cleaning up what was done in `init`. It could also allow an inheriting class to begin waiting for children (see `process_messages`)

 `get_database`<span class="sig-paren">(</span>*database\_name*, *user=None*, *schema=None*, *\*\*kwargs*<span class="sig-paren">)</span> → bi\_etl.database.database\_metadata.DatabaseMetadata<a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.get_database" class="headerlink" title="Permalink to this definition">¶</a>  
Get a new database connection.

|             |                                                                                                                                                                                                                                                                                                 |
|-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **database\_name** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The name of the database section in <a href="config_ini.md" class="reference internal"><span class="doc">config.ini</span></a> 
  -   **user** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) –                                                                                                                                             
  -   **schema** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) –                                                                                                                                           |

 `get_parameter`<span class="sig-paren">(</span>*param\_name*, *default=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.get_parameter" class="headerlink" title="Permalink to this definition">¶</a>  
Returns the value of the parameter with the name provided, or default if that is not None.

|             |                                                                                                                                                                                                     |
|-------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **param\_name** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The parameter to retrieve               
  -   **default** (<a href="https://docs.python.org/2/library/functions.md#any" class="reference external" title="(in Python v2.7)"><em>any</em></a>) – The default value. *Default* default = None  |
| Raises:     | ParameterError: – If named parameter does not exist and no default is provided.                                                                                                                     |

 `get_setting`<span class="sig-paren">(</span>*setting\_name*, *assignments=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.get_setting" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_setting_or_default`<span class="sig-paren">(</span>*setting\_name*, *default*<span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.get_setting_or_default" class="headerlink" title="Permalink to this definition">¶</a>  

 `init`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.init" class="headerlink" title="Permalink to this definition">¶</a>  
pre-load initialization. Runs on the execution server. Override to add setup tasks.

Note: init method is useful in cases were you wish to define a common base class with a single load method. Each inheriting class can then do it’s own stuff in init With init you can have the flow of execution be:

1.  spec\_class.init (if any code before super call)
2.  base\_class.init
3.  spec\_class.init (after super call, where your code should really go)
4.  base\_class.load

Note 2: Sometimes the functionality above can be achieved with \_\_init\_\_. However, when the scheduler thread creates an ETLTask, it creates an instance and thus runs \_\_init\_\_. Therefore, you will want \_\_init\_\_ to be as simple as possible. On the other hand, init is run only by the task execution thread. So it can safely do more time consuming work. Again though this method is for when class inheritance is used, and that logic can not go into the load method.

Why does the scheduler create an instance? It does that in case a task needs a full instance and possibly parameter values in order to answer some of the methods like depends\_on or mutually\_exclusive\_execution.

 `load`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.load" class="headerlink" title="Permalink to this definition">¶</a>  

 `load_parameters`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.load_parameters" class="headerlink" title="Permalink to this definition">¶</a>  
Load parameters for this task from the scheduler.

 `log`<a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.log" class="headerlink" title="Permalink to this definition">¶</a>  
Get a logger using the task name.

 `log_logging_level`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.log_logging_level" class="headerlink" title="Permalink to this definition">¶</a>  

 `mutually_exclusive_execution`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.mutually_exclusive_execution" class="headerlink" title="Permalink to this definition">¶</a>  
Override to provide a list of task names (or partial names that match modules) that this task can not run at the same time as.

If allow\_concurrent\_runs is false, defaults to a list with just self.name If allow\_concurrent\_runs is true, defaults to an empty list

 `mutually_exclusive_with_set`<a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.mutually_exclusive_with_set" class="headerlink" title="Permalink to this definition">¶</a>  
Build a set of modules this task is mutually exclusive with. The list is obtained using mutually\_exclusive\_execution. Each list member will be “normalized” to be a fully qualified name.

 `name`<a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.name" class="headerlink" title="Permalink to this definition">¶</a>  
*Note* – Return value needs to be compatible with find\_etl\_class

 `needs_to_get_ancestor_statuses`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.needs_to_get_ancestor_statuses" class="headerlink" title="Permalink to this definition">¶</a>  
Override and return True if you want to get status updates on any ancestor.

 `needs_to_get_child_statuses`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.needs_to_get_child_statuses" class="headerlink" title="Permalink to this definition">¶</a>  
Override and return True if you want to get status updates on children.

 `needs_to_ok_child_runs`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.needs_to_ok_child_runs" class="headerlink" title="Permalink to this definition">¶</a>  
Override and return True if you need to give OK before children are allowed to run. See process\_child\_run\_requested

 `normalized_dependents_set`<a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.normalized_dependents_set" class="headerlink" title="Permalink to this definition">¶</a>  
Build a set of modules this task depends on. See depends\_on. Each will be “normalized” to be a fully qualified name.

 `parameter_names`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.parameter_names" class="headerlink" title="Permalink to this definition">¶</a>  
Returns a list of parameter names

 `parameters`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.parameters" class="headerlink" title="Permalink to this definition">¶</a>  
Returns a generator yielding tuples of parameter (name,value)

 `parent_task`<a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.parent_task" class="headerlink" title="Permalink to this definition">¶</a>  

 `parent_task_id`<a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.parent_task_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `process_child_run_requested`<span class="sig-paren">(</span>*childRunRequested*<span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.process_child_run_requested" class="headerlink" title="Permalink to this definition">¶</a>  
Override to examine child task before giving OK.

 `process_child_status_update`<span class="sig-paren">(</span>*childStatusUpdate*<span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.process_child_status_update" class="headerlink" title="Permalink to this definition">¶</a>  
Override to examine child task status (ChildRunFinished instances)

 `process_messages`<span class="sig-paren">(</span>*block=False*<span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.process_messages" class="headerlink" title="Permalink to this definition">¶</a>  
Processes messages for this task. Should be called somewhere in any row looping.

|             |                                                                                                                                                                                                                                                        |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | **block** (*boolean*) – Block while waiting. Defaults to False. If block is True, this will run until a terminating message is received or an exception is thrown by the process\_X calls. If block if False, you probably want to call inside a loop. |

**Example Code:**

    from bi_etl.scheduler.exceptions import WorkflowFinished

    def process_child_status_update(self, childStatusUpdate):
        # Placeholder for real check if done
        example_all_done = self.foo()

        if example_all_done:
            raise WorkflowFinished()

    def load(self):
        # Placeholder for real load code
        self.load_foo()

        #Begin waiting for children
        try:
           self.process_messages(block=True)
        except WorkflowFinished:
            pass

 `register_child`<span class="sig-paren">(</span>*child\_task\_object*<span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.register_child" class="headerlink" title="Permalink to this definition">¶</a>  

 `register_object`<span class="sig-paren">(</span>*obj*<span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.register_object" class="headerlink" title="Permalink to this definition">¶</a>  
Register an ETLComponent object with the task. This allows the task to 1) Get statistics from the component 2) Close the component when done

|             |                                                                                                                                                                                                                                                                                                                      |
|-------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | **obj** (<a href="bi_etl.components.etlcomponent.md#bi_etl.components.etlcomponent.ETLComponent" class="reference internal" title="bi_etl.components.etlcomponent.ETLComponent"><em>bi_etl.components.etlcomponent.ETLComponent</em></a>) – A sub-class of :class\`~bi\_etl.components.etlcomponent.ETLComponent\` |

 `root_task`<a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.root_task" class="headerlink" title="Permalink to this definition">¶</a>  

 `root_task_id`<a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.root_task_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `run`<span class="sig-paren">(</span>*no\_mail=None*, *parent\_to\_child=None*, *child\_to\_parent=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.run" class="headerlink" title="Permalink to this definition">¶</a>  
Should not generally be overridden. This is called smtp\_to run the task’s code in the init, load, and finish methods.

 `scheduler`<a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.scheduler" class="headerlink" title="Permalink to this definition">¶</a>  
*Get the existing* – class\`bi\_etl.scheduler.scheduler.Scheduler\` that this task is running under. or Get an instance of :class\`bi\_etl.scheduler.scheduler\_interface.SchedulerInterface\` that can be used to interact with the main Scheduler.

 `send_mesage`<span class="sig-paren">(</span>*msg*<span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.send_mesage" class="headerlink" title="Permalink to this definition">¶</a>  

 `set_parameter`<span class="sig-paren">(</span>*param\_name: str*, *param\_value: object*, *local\_only: bool = False*, *commit: bool = True*<span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.set_parameter" class="headerlink" title="Permalink to this definition">¶</a>  
Add a single parameter to this task.

|             |                                                                                                                                                                                               |
|-------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **param\_name** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The name of the parameter to add  
  -   **param\_value** (<a href="https://docs.python.org/2/library/functions.md#object" class="reference external" title="(in Python v2.7)"><em>object</em></a>) – The value of the parameter  
  -   **commit** (<a href="https://docs.python.org/2/library/functions.md#bool" class="reference external" title="(in Python v2.7)"><em>bool</em></a>) –                                       
  -   **local\_only** (<a href="https://docs.python.org/2/library/functions.md#bool" class="reference external" title="(in Python v2.7)"><em>bool</em></a>) –                                  |

 `set_parameters`<span class="sig-paren">(</span>*local\_only=False*, *commit=True*, *\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.set_parameters" class="headerlink" title="Permalink to this definition">¶</a>  
Add multiple parameters to this task. Parameters can be passed in as any combination of: \* dict instance. Example `add_parameters( {'param1':'example', 'param2':100} )` \* list of lists. Example: `add_parameters( [ ['param1','example'], ['param2',100] ] )` \* list of tuples. Example: `add_parameters( [ ('param1','example'), ('param2',100) ] )` \* keyword arguments. Example: `add_parameters(foo=1, bar='apple')`

|             |                                                                                                                                                                                                          |
|-------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **local\_only** (*boolean*) – Optional. Default= False. Add parameters to local task only. Do not record in the scheduler.                                                                           
  -   **commit** (*boolean*) – Optional. Default= True. Commit changes to the task database.                                                                                                                
  -   **args** (<a href="https://docs.python.org/2/library/functions.md#list" class="reference external" title="(in Python v2.7)"><em>list</em></a>) – list of lists. or list of tuples. See above.       
  -   **kwargs** (<a href="https://docs.python.org/2/library/stdtypes.md#dict" class="reference external" title="(in Python v2.7)"><em>dict</em></a>) – keyword arguments send to parameters. See above.  |

 `start_following_tasks`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.start_following_tasks" class="headerlink" title="Permalink to this definition">¶</a>  
Override to add tasks that should follow after this tasks to the scheduler. This is called at the end of ETLTask.run

 `statistics`<a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.statistics" class="headerlink" title="Permalink to this definition">¶</a>  
Return the execution statistics from the task and all of it’s registered components.

 `status`<a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.status" class="headerlink" title="Permalink to this definition">¶</a>  

 `task_id`<a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.task_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `task_rec`<a href="#bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2.task_rec" class="headerlink" title="Permalink to this definition">¶</a>  

#### Previous topic

[bi\_etl.tests.etl\_jobs.etl\_task\_d1 module](bi_etl.tests.etl_jobs.etl_task_d1.md "previous chapter")

#### Next topic

[bi\_etl.tests.etl\_jobs.etl\_task\_d3 module](bi_etl.tests.etl_jobs.etl_task_d3.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.tests.etl_jobs.etl_task_d3.md "bi_etl.tests.etl_jobs.etl_task_d3 module") |
-   [previous](bi_etl.tests.etl_jobs.etl_task_d1.md "bi_etl.tests.etl_jobs.etl_task_d1 module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.tests package](bi_etl.tests.md) »
-   [bi\_etl.tests.etl\_jobs package](bi_etl.tests.etl_jobs.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
