"""
Created on Sep 15, 2014

@author: woodd
"""
from configparser import ConfigParser

import errno
import logging
import traceback
import warnings
from queue import Empty
from typing import Union

from CaseInsensitiveDict import CaseInsensitiveDict

from bi_etl import utility
from bi_etl.bi_config_parser import BIConfigParser
from bi_etl.database.connect import Connect, DatabaseMetadata
from bi_etl.notifiers.email import Email
from bi_etl.scheduler import models
from bi_etl.scheduler import queue_io
from bi_etl.scheduler.exceptions import ParameterError, TaskStopRequested
from bi_etl.scheduler.messages import ChildRunOK
from bi_etl.scheduler.messages import ChildRunRequested
from bi_etl.scheduler.messages import ChildSetDisplayName
from bi_etl.scheduler.messages import ChildStatusUpdate
from bi_etl.scheduler.status import Status
from bi_etl.statistics import Statistics
from bi_etl.timer import Timer


# For memory testing:
# import gc
# from pympler import tracker

# pylint: disable=too-many-instance-attributes, too-many-public-methods
# pylint: disable=too-many-statements, too-many-branches, too-many-arguments

class ETLTask(object):
    """
    ETL Task runnable base class.

    load() **must** be overridden.

    depends_on() should be overridden.

    start_following_tasks() can be overridden.
    """

    DEFAULT_NO_MAIL = False
    CLASS_VERSION = 1.0

    def __init__(self,
                 task_id=None,
                 parent_task_id=None,
                 root_task_id=None,
                 scheduler=None,
                 task_rec=None,
                 config=None
                 ):
        """
        Constructor. This code will run on the scheduler thread and the execution thread.
        It should do as little as possible.

         Parameters
        ----------
        task_id: int
            The task_id of the job (only for :class:`bi_etl.scheduler.scheduler.Scheduler`).
        parent_task_id: int
            The task_id of the parent of this job (only for :class:`bi_etl.scheduler.scheduler.Scheduler`).
        root_task_id: int
            The task_id of the root ancestor of this job
            (only for :class:`bi_etl.scheduler.scheduler.Scheduler`).
        scheduler: bi_etl.scheduler.scheduler.Scheduler
            The :class:`bi_etl.scheduler.scheduler.Scheduler` this job should be run under.
            Defaults to not running via a scheduler.
        config: bi_etl.bi_config_parser.BIConfigParser
            The configuration :class:`bi_etl.bi_config_parser.BIConfigParser` to use
            (See :doc:`config_ini`). If passed it should be an instance
            of :class:`bi_etl.bi_config_parser.BIConfigParser`.
        """
        self._log = None
        self._task_rec = None

        # If we got both task_id and task_rec
        if task_id and task_rec:
            # Make sure they match
            assert task_id == task_rec.task_id, 'Conflicting task_id values given {} and {}'.format(task_id,
                                                                                                    task_rec.task_id)
            self.task_rec = task_rec
        # Otherwise if we got only task_id
        elif task_id:
            assert isinstance(task_id, int), "task_id is not an integer or None!"
            if scheduler:
                # If we got a scheduler, use it to get the task_record
                self.task_rec = scheduler.get_task_record(task_id)
            else:
                # Otherwise make one (it will never get stored though
                self.task_rec = models.ETL_Tasks()
                self.task_id = task_id
        # Otherwise if we got only task_rec
        elif task_rec:
            self.task_rec = task_rec
        # Otherwise we didn't get either (local run)
        else:
            # Make a task_rec (it will never get stored though)
            self.task_rec = models.ETL_Tasks()
        # Make sure we don't refer to task_rec anymore only self.task_rec
        del task_rec

        if self.parent_task_id is None:
            self.parent_task_id = parent_task_id
        else:
            assert parent_task_id == self.task_rec.parent_task_id, 'Conflicting parent_task_id values given {} and {}'.format(
                task_id, self.task_rec.parent_task_id)

        if self.root_task_id is None:
            self.root_task_id = root_task_id
        else:
            assert root_task_id == self.task_rec.root_task_id, 'Conflicting parent_task_id values given {} and {}'.format(
                root_task_id, self.task_rec.root_task_id)

        self._externally_provided_scheduler = (scheduler is not None)
        self._scheduler = scheduler
        self._config = config
        if self.status is None:
            self.status = Status.new
        self._parameters_loaded = False
        self._parameter_dict = CaseInsensitiveDict()
        self.parent_to_child = None
        self.child_to_parent = None
        self.object_registry = list()
        self.thread_running = None
        self.summary_message_from_client = False
        self.last_log_msg_time = None
        self.pending_log_msgs = list()
        self.last_log_msg = ""
        # set initial default value for waiting_for_workflow
        self.waiting_for_workflow = False
        # Try and get waiting_for_workflow from the parent
        if self.parent_task_id is not None:
            try:
                self.waiting_for_workflow = self.parent_task.needs_to_ok_child_runs()
                self.parent_task.register_child(self)
            except TypeError:
                pass  # We're not running on a full Scheduler
        self._children = set()
        # Used by the scheduler to tell if this task has written it's dependencies to the log
        self._logged_dependencies = False
        self._normalized_dependents_set = None
        self._mutually_exclusive_with_set = None
        self._database_pool = None
        self.init_timer = Timer(start_running=False)
        self.load_timer = Timer(start_running=False)
        self.finish_timer = Timer(start_running=False)

    def __getstate__(self):
        odict = dict()
        odict['version'] = self.CLASS_VERSION
        odict['task_id'] = self.task_id
        odict['root_task_id'] = self.root_task_id
        odict['parent_task_id'] = self.parent_task_id
        odict['status'] = self.status
        # We don't pass scheduler or config from the Scheduler to the running instance
        # odict['scheduler'] = self._scheduler
        # print("__getstate__ {}".format(utility.dict_to_str(odict)))
        return odict

    def __setstate__(self, odict):
        # print("__setstate__ {}".format(utility.dict_to_str(odict)))
        if 'version' not in odict:
            odict['version'] = 0.0
        if odict['version'] != self.CLASS_VERSION:
            raise ValueError("ETLTask versions incompatible between scheduler and target server")
        self.__init__(task_id=odict['task_id'],
                      parent_task_id=odict['parent_task_id'],
                      root_task_id=odict['root_task_id'],
                      # We don't pass scheduler or config from the Scheduler to the running instance
                      # scheduler= odict['scheduler']
                      )

    def log_logging_level(self):
        # Calling bi_etl.utility version
        utility.log_logging_level(self.log)

    def __repr__(self):
        msg = "{cls}(task_id={task_id}, parent_task_id={parent_task_id}, root_task_id={root_task_id})"
        return msg.format(
            cls=self.name,
            task_id=self.task_id,
            parent_task_id=self.parent_task_id,
            root_task_id=self.root_task_id,
        )

    def __str__(self):
        return self.name

    @property
    def name(self):
        """
        Note: Return value needs to be compatible with find_etl_class
        """
        module = self.__class__.__module__

        return module + '.' + self.__class__.__name__

    @property
    def task_rec(self):
        return self._task_rec

    @task_rec.setter
    def task_rec(self, new_value):
        assert isinstance(new_value, models.ETL_Tasks)
        self._task_rec = new_value

    @property
    def status(self):
        return self.task_rec.Status

    @status.setter
    def status(self, new_value):
        self.task_rec.Status = new_value

    @property
    def task_id(self):
        return self.task_rec.task_id

    @task_id.setter
    def task_id(self, new_value):
        if new_value is not None:
            new_value = int(new_value)
        self.task_rec.task_id = new_value

    @property
    def display_name(self):
        return self.task_rec.display_name

    @display_name.setter
    def display_name(self, new_value):
        if self.child_to_parent:
            self.child_to_parent.put(ChildSetDisplayName(self.task_id, new_value))
            self.task_rec.display_name = new_value
        else:
            self.log.debug('Setting display_name in task_rec= {}'.format(new_value))
            self.task_rec.display_name = new_value
            self.scheduler.session.commit()

    @property
    def parent_task_id(self):
        return self.task_rec.parent_task_id

    @parent_task_id.setter
    def parent_task_id(self, new_value):
        if new_value is not None:
            new_value = int(new_value)
        self.task_rec.parent_task_id = new_value

    @property
    def parent_task(self):
        if self.parent_task_id is not None:
            if self._scheduler is not None and hasattr(self._scheduler, 'get_task_by_id'):
                return self._scheduler.get_task_by_id(self.parent_task_id)  # pylint: disable=no-member
            else:
                raise TypeError('Scheduler required to get ETLTask.parent_task')
        else:
            return None

    @property
    def root_task_id(self):
        return self.task_rec.root_task_id

    @root_task_id.setter
    def root_task_id(self, new_value):
        if new_value is not None:
            new_value = int(new_value)
        self.task_rec.root_task_id = new_value

    @property
    def root_task(self):
        if self.root_task_id is not None:
            if type(self.scheduler).__name__ == 'Scheduler':
                # pylint: disable=no-member
                return self.scheduler.get_task_by_id(self.root_task_id)
            else:
                raise TypeError('Scheduler required to get ETLTask.root_task')
        else:
            return None

    @property
    def children(self):
        return self._children

    def register_child(self, child_task_object):
        return self._children.add(child_task_object)

    @property
    def log(self):
        """
        Get a logger using the task name.
        """
        if self._log is None:
            self._log = logging.getLogger(self.name)

        return self._log

    # pylint: disable=no-self-use
    def depends_on(self):
        """
        Override to provide a static list of tasks that this task will wait on if they are running.

        Each dependent task entry should consist of either
        1) The module name (str)
        2) A tuple of the module name (str) and class name (str)

        This task will run if the dependent jobs are not active at all in the scheduler.
        This does mean you need to be careful with the order that jobs are added to the scheduler since
        if jobs are supposed to run A->B->C, but you add (and commit) job C first, it will see that B is
        not running and start.  The scheduler would then allow A to run, and block B until both A and C
        are is_finished (since it checks forward and backwards for dependencies.
        """
        return list()

    @property
    def normalized_dependents_set(self):
        """
        Build a set of modules this task depends on.
        See depends_on.
        Each will be "normalized" to be a fully qualified name.
        """
        if self._normalized_dependents_set is None:
            normalized_dependents_set = set()
            self._normalized_dependents_set = normalized_dependents_set
            depends_on = self.depends_on()
            if depends_on is not None:
                if isinstance(depends_on, str):
                    depends_on = [depends_on]

                for dep_name in depends_on:
                    qualified_classes = self.scheduler.find_etl_classes(dep_name)
                    if len(qualified_classes) > 0:
                        for dep_task_name in qualified_classes:
                            normalized_dependents_set.add(dep_task_name)
                    else:
                        self.log.warning('dependent entry {} did not match any classes'.format(dep_name))

        return self._normalized_dependents_set

    def _mutually_exclusive_execution(self):
        """
        See mutually_exclusive_execution.
        This method has the default functionality so it's easier to call on that logic when
        overriding mutually_exclusive_execution.
        """
        if self.allow_concurrent_runs():
            return list()
        else:
            return [self.name]

    def mutually_exclusive_execution(self):
        """
        Override to provide a list of task names (or partial names that match modules) 
        that this task can not run at the same time as.

        If allow_concurrent_runs is false, defaults to a list with just self.name
        If allow_concurrent_runs is true, defaults to an empty list
        """
        return self._mutually_exclusive_execution()

    @property
    def mutually_exclusive_with_set(self):
        """
        Build a set of modules this task is mutually exclusive with.
        The list is obtained using `mutually_exclusive_execution`.
        Each list member will be "normalized" to be a fully qualified name.
        """
        if self._mutually_exclusive_with_set is None:
            mutually_exclusive_with_set = set()
            self._mutually_exclusive_with_set = mutually_exclusive_with_set
            mutually_exclusive_with_list = self.mutually_exclusive_execution()
            if mutually_exclusive_with_list is not None:
                for mutually_exclusive_with in mutually_exclusive_with_list:
                    mutually_exclusive_with = self.scheduler.find_etl_classes(mutually_exclusive_with)
                    if len(mutually_exclusive_with) > 0:
                        for mutually_exclusive_with_name in mutually_exclusive_with:
                            mutually_exclusive_with_set.add(mutually_exclusive_with_name)
                    else:
                        self.log.warning(
                            'mutually_exclusive value {} did not match any classes'.format(mutually_exclusive_with))

        return self._mutually_exclusive_with_set

    @property
    def config(self) -> ConfigParser:
        """
        Get the task configuration object. If it was not passed in, it will be read from the users
        folder.
        """
        if self._config is None:
            self._config = BIConfigParser()
            self._config.read_config_ini()
        return self._config

    @property
    def scheduler(self):
        """
        Get the existing :class`bi_etl.scheduler.scheduler.Scheduler` that this task is running under.
        or
        Get an instance of :class`bi_etl.scheduler.scheduler_interface.SchedulerInterface` that can be
        used to interact with the main Scheduler.
        """
        if self._scheduler is None:
            # Import is done here to prevent circular module level imports
            self.log.debug("Building scheduler")
            from bi_etl.scheduler.scheduler_interface import SchedulerInterface
            self._scheduler = SchedulerInterface(config=self.config,
                                                 log_name=self.name + '_SchedulerInterface'
                                                 )
        return self._scheduler

    def add_child_task_to_scheduler(self,
                                    etl_task_class_type,
                                    parameters=None,
                                    display_name=None,
                                    ):
        """
        Start a new task on the :class`bi_etl.scheduler.scheduler.Scheduler`
        that will be a child of this task.
        """
        new_task_id = None
        if self.task_id is not None:
            new_task_id = self.scheduler.add_task_by_class(etl_task_class_type,
                                                           parent_task_id=self.task_id,
                                                           root_task_id=self.root_task_id,
                                                           parameters=parameters,
                                                           display_name=display_name,
                                                           )
        else:
            msg = 'Not running in a scheduler. Child task {} not actually scheduled.'.format(etl_task_class_type)
            self.log.warning(msg)
        return new_task_id

    def add_child_task_by_partial_name_to_scheduler(self,
                                                    partial_module_name,
                                                    parameters=None,
                                                    display_name=None,
                                                    ):
        """
        Start a new task on the :class`bi_etl.scheduler.scheduler.Scheduler`
        that will be a child of this task.
        """
        new_task_id = None
        if self.task_id is not None:
            new_task_id = self.scheduler.add_task_by_partial_name(partial_module_name,
                                                                  parent_task_id=self.task_id,
                                                                  root_task_id=self.root_task_id,
                                                                  parameters=parameters,
                                                                  display_name=display_name,
                                                                  )
        else:
            msg = 'Not running in a scheduler. Child task {} not actually scheduled.'.format(partial_module_name)
            self.log.warning(msg)
        return new_task_id

    def start_following_tasks(self):
        """
        Override to add tasks that should follow after this tasks to the scheduler.
        This is called at the end of ETLTask.run
        """
        return

    def load_parameters(self):
        """
        Load parameters for this task from the scheduler.
        """
        # set to loaded no matter what
        self._parameters_loaded = True
        if self.task_id is not None:
            self.scheduler.load_parameters(self)

    def set_parameter(self,
                      param_name: str,
                      param_value: object,
                      local_only: bool = False,
                      commit: bool = True):
        """
        Add a single parameter to this task.

        Parameters
        ----------
        param_name: str
            The name of the parameter to add
        param_value: object
            The value of the parameter
        commit: bool
        local_only: bool
        """
        if not self._parameters_loaded:
            self.load_parameters()
        self._parameter_dict[param_name] = param_value

        if not local_only:
            if self.task_id is not None:
                self.log.info('add_parameter to scheduler {} = {}'.format(param_name, param_value))
                self.scheduler.add_task_paramter(self.task_id, param_name, param_value, commit=commit)
        else:
            print("add_parameter local {}={}".format(param_name, param_value))

    # Deprecated name
    def add_parameter(self,
                      param_name: str,
                      param_value: object,
                      local_only: bool = False,
                      commit: bool = True):
            warnings.warn("add_parameter is deprecated, please use set_parameter instead")
            self.set_parameter(param_name=param_name,
                               param_value=param_value,
                               local_only=local_only,
                               commit=commit)

    def set_parameters(self, local_only=False, commit=True, *args, **kwargs):
        """
        Add multiple parameters to this task.
        Parameters can be passed in as any combination of:
        * dict instance. Example ``add_parameters( {'param1':'example', 'param2':100} )``
        * list of lists. Example: ``add_parameters( [ ['param1','example'], ['param2',100] ] )``
        * list of tuples. Example: ``add_parameters( [ ('param1','example'), ('param2',100) ] )``
        * keyword arguments. Example: ``add_parameters(foo=1, bar='apple')``
        
        Parameters
        ----------
        local_only: boolean
            Optional. Default= False. Add parameters to local task only. Do not record in the scheduler.
        commit: boolean 
            Optional. Default= True. Commit changes to the task database.
        args: list
            list of lists. or list of tuples. See above.
        kwargs: dict
            keyword arguments send to parameters. See above.
        """
        # Support add_parameters(param1='example', param2=100)
        self._parameter_dict.update(kwargs)
        for param_name, param_value in kwargs.items():
            self.set_parameter(param_name, param_value, local_only=local_only, commit=commit)
        # Also accept a list of dicts, tuples, or lists
        # eg. add_parameters( [ ('param1','example'), ('param2',100) ] )
        #  or add_parameters( [ ['param1','example'], ['param2',100] ] )
        #  or add_parameters( [ ('param1','example'), ['param2',100] ] )
        #  or parms = {'param1':'example', 'param2':100}
        #     add_parameters(parms)
        #### which is equivalent to
        #     add_parameters(**parms)
        for arg in args:
            if isinstance(arg, dict):
                for param_name, param_value in arg.items():
                    self.set_parameter(param_name, param_value, local_only=local_only, commit=commit)
            elif hasattr(arg, '__getitem__'):
                if len(arg) == 2:
                    self.set_parameter(arg[0], arg[1], local_only=local_only, commit=commit)
                else:
                    raise ValueError("add_parameters sequence {} had unexpected length {}".format(arg, len(arg)))

    # Deprecated name
    def add_parameters(self, local_only=False, commit=True, *args, **kwargs):
        warnings.warn("add_parameters is deprecated, please use set_parameters instead")
        self.set_parameters(local_only=local_only,
                            commit=commit,
                            *args,
                            **kwargs)

    def parameters(self):
        """
        Returns a generator yielding tuples of parameter (name,value)
        """
        if not self._parameters_loaded:
            self.load_parameters()
        for param_name in self._parameter_dict:
            yield param_name, self._parameter_dict[param_name]

    def parameter_names(self):
        """
        Returns a list of parameter names
        """
        if not self._parameters_loaded:
            self.load_parameters()
        return list(self._parameter_dict.keys())

    def get_parameter(self, param_name, default=None):
        """
        Returns the value of the parameter with the name provided, or default if that is not None.
        
        Parameters
        ----------
        param_name: str
            The parameter to retrieve        
        default: any 
            The default value. *Default* default = None
            
        Raises
        ------
        ParameterError: 
            If named parameter does not exist and no default is provided.
        """
        if not self._parameters_loaded:
            self.load_parameters()

        try:
            return self._parameter_dict[param_name]
        except KeyError as e:
            if default is None:
                raise ParameterError(e) from e
            else:
                return default

    def add_database(self, database_object):
        # _database_pool is used to close connections when the task finishes
        self._database_pool.append(database_object)

    def get_database(self, database_name, user=None, schema=None, **kwargs) -> DatabaseMetadata:
        """
        Get a new database connection.
        
        Parameters
        ----------
        database_name: str
            The name of the database section in :doc:`config_ini`
        user: str
        schema: str
        """

        return Connect.get_database_metadata(config=self.config,
                                             database_name=database_name,
                                             user=user,
                                             schema=schema,
                                             **kwargs
                                             )

    def get_setting(self, setting_name, assignments=None):
        return self.config.get(section=self.name, option=setting_name, vars=assignments)

    def get_setting_or_default(self, setting_name, default):
        return self.config.get(section=self.name, option=setting_name, fallback=default)

    def register_object(self, obj):
        """
        Register an ETLComponent object with the task.
        This allows the task to 
        1) Get statistics from the component
        2) Close the component when done
        
        Parameters
        ----------
        obj: bi_etl.components.etlcomponent.ETLComponent
            A sub-class of :class`~bi_etl.components.etlcomponent.ETLComponent`
        """
        self.object_registry.append(obj)
        return obj

    # pylint: disable=singleton-comparison
    def debug_sql(self, mode: Union[bool, int] = True):
        """
        Control the output of sqlalchemy engine

        Parameters
        ----------
        mode
            Boolean (debug if True, Error if false) or int logging level.
        """
        if isinstance(mode, bool):
            if mode:
                self.log.info('Setting sqlalchemy.engine to DEBUG')
                logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
                logging.getLogger('sqlalchemy.engine.base.Engine').setLevel(logging.DEBUG)
            else:
                self.log.info('Setting sqlalchemy.engine to ERROR')
                logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
                logging.getLogger('sqlalchemy.engine.base.Engine').setLevel(logging.ERROR)
        else:
            self.log.info('Setting sqlalchemy.engine to {}'.format(mode))
            logging.getLogger('sqlalchemy.engine').setLevel(mode)
            logging.getLogger('sqlalchemy.engine.base.Engine').setLevel(mode)

    def __thread_init(self):
        """
        Base class pre-load initialization.  Runs on the execution server.
        Override init instead of this.
        """
        queue_io.redirect_output_to(self.child_to_parent)

        config = self.config
        if not isinstance(config, BIConfigParser):
            config = BIConfigParser(config)
        config.set_dated_log_file_name(self.name, '.log')
        config.setup_logging()

        self.log_logging_level()
        self.log.debug("externally_provided_scheduler = {}".format(self._externally_provided_scheduler))

        self._database_pool = list()

    def init(self):
        """
        pre-load initialization.  Runs on the execution server. Override to add setup tasks.
        
        Note: init method is useful in cases were you wish to define a common base class
        with a single load method. Each inheriting class can then do it's own stuff in init
        With init you can have the flow of execution be:
        
        1) spec_class.init (if any code before super call)
        2) base_class.init
        3) spec_class.init (after super call, where your code should really go)
        4) base_class.load
        
        Note 2: Sometimes the functionality above can be achieved with `__init__`.  However, when
        the scheduler thread creates an ETLTask, it creates an instance and thus runs __init__. 
        Therefore, you will want `__init__` to be as simple as possible.  On the other hand, `init`
        is run only by the task execution thread. So it can safely do more time consuming work. 
        Again though this method is for when class inheritance is used, and that logic can not go 
        into the `load` method.         
        
        Why does the scheduler create an instance?
        It does that in case a task needs a full instance and possibly parameter values in order 
        to answer some of the methods like `depends_on` or `mutually_exclusive_execution`.        
        """
        pass

    def load(self):
        """
        Placeholder for load. This is where the main body of the ETLTask's work should be performed.
        """
        raise AttributeError("{} load not implemented".format(self))

    def finish(self):
        """
        Placeholder for post-load cleanup. This might be useful for cleaning up what was done in ``init``.
        It could also allow an inheriting class to begin waiting for children (see ``process_messages``)
        """
        pass

    def send_mesage(self, msg):
        if self.child_to_parent is not None:
            self.child_to_parent.put(msg)

    def allow_concurrent_runs(self):
        return False

    def needs_to_ok_child_runs(self):
        """
        Override and return True if you need to give OK before children are allowed to run.
        See process_child_run_requested
        """
        return False

    def process_child_run_requested(self, childRunRequested):
        """
        Override to examine child task before giving OK.
        """
        self.send_mesage(ChildRunOK(childRunRequested.child_task_id))

    def needs_to_get_child_statuses(self):
        """
        Override and return True if you want to get status updates on children.
        """
        return False

    def needs_to_get_ancestor_statuses(self):
        """
        Override and return True if you want to get status updates on any ancestor.
        """
        return False

    def process_child_status_update(self, childStatusUpdate):
        """
        Override to examine child task status (ChildRunFinished instances)
        """
        pass

    def process_messages(self, block=False):
        """
        Processes messages for this task.  Should be called somewhere in any row looping.
        
        Parameters
        ----------
        block: boolean 
            Block while waiting. Defaults to False.
            If block is True, this will run until a terminating message is received or an exception is thrown by the process_X calls.
            If block if False, you probably want to call inside a loop.


        **Example Code:**
                
        .. code-block:: python

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
                    
        
        """
        q = self.parent_to_child
        if q is not None:
            try:
                while True:
                    try:
                        msg = q.get(block=block, timeout=10)
                        self.log.debug("process_messages got {}".format(msg))
                        if msg == 'stats':
                            self.child_to_parent.put(self.statistics)
                        elif msg == 'stop':
                            self.log.info("Stop signal received")
                            raise TaskStopRequested()
                        elif isinstance(msg, ChildRunRequested):
                            self.process_child_run_requested(msg)
                        elif isinstance(msg, ChildStatusUpdate):
                            self.process_child_status_update(msg)
                        else:
                            self.log.warning("Got unexpected message from parent: {}".format(repr(msg)))
                    except IOError as e:
                        if e.errno == errno.EINTR:
                            continue
                        else:
                            raise
            except Empty:
                pass

    def run(self,
            no_mail=None,
            parent_to_child=None,
            child_to_parent=None,
            ):
        """
        Should not generally be overridden.
        This is called smtp_to run the task's code in the init, load, and finish methods.
        """
        self.child_to_parent = child_to_parent
        self.parent_to_child = parent_to_child
        self.__thread_init()

        if no_mail is None:
            # If run directly, assume it a testing run and don't send e-mails
            if self.__class__.__module__ == '__main__':
                self.log.info("Direct module execution detected. Failure e-mails will not be sent")
                no_mail = True
            else:
                no_mail = ETLTask.DEFAULT_NO_MAIL

        self.status = Status.running

        try:
            # Note: init method is useful in cases were you wish to define a common base class
            # with a single load method. Each inheriting class can then do it's own stuff in init
            # With init you can have the flow of execution be:
            #  1) spec_class.init (if any code before super call)
            #  2) base_class.init
            #  3) spec_class.init (after super call, where your code should really go)
            #  3) base_class.load

            self.init_timer.start()
            self.init()
            self.init_timer.stop()

            self.process_messages()

            self.load_timer.start()
            self.load()
            self.load_timer.stop()

            self.process_messages()

            # finish would be the place to cleanup anything done in the init method 
            self.finish_timer.start()
            self.finish()
            self.finish_timer.stop()

            self.log.info("{} done.".format(self))
            self.status = Status.succeeded
            stats = self.statistics
            if self.child_to_parent is not None:
                self.child_to_parent.put(stats)
            stats_formatted = Statistics.format_statistics(stats)
            self.log.info("{} statistics=\n{stats}".format(self, stats=stats_formatted))

            self.start_following_tasks()
        except Exception as e:  # pylint: disable=broad-except
            self.status = Status.failed
            self.log.exception(e)
            self.log.error(utility.dict_to_str(e.__dict__))
            if not no_mail:
                smtp_to = self.config.get('SMTP', 'distro_list', fallback=None)
                if not smtp_to:
                    self.log.warning("SMTP distro_list option not found. No mail sent.")
                else:
                    environment = self.config.get('SMTP', 'environment', fallback='Unknown_ENVT')
                    message_list = list()
                    message_list.append(repr(e))
                    message_list.append("Task ID = {}".format(self.task_id))
                    ui_url = self.config.get('Scheduler', 'base_ui_url', fallback=None)
                    if ui_url and self.task_id:
                        message_list.append("Run details are here: {}{}".format(ui_url, self.task_id))
                    message_content = '\n'.join(message_list)
                    subject = "{environment} {etl} load failed".format(environment=environment, etl=self)

                    #TODO: Define notifiers setup from config
                    notifiers_list = [Email(self.config, smtp_to)]

                    for notifier in notifiers_list:
                        notifier.send(message_content, subject=subject)
            self.log.info("{} FAILED.".format(self))
            if self.child_to_parent is not None:
                self.child_to_parent.put(e)

        self.log.info("Status = {}".format(repr(self.status)))

        # Send out status
        if self.child_to_parent is not None:
            self.child_to_parent.put(self.status)

        return self.status == Status.succeeded

    @property
    def statistics(self):
        """
        Return the execution statistics from the task and all of it's registered components.
        """
        stats = Statistics()
        # Only report init stats if something significant was done there
        if self.init_timer.seconds_elapsed > 1:
            stats['Task Init'] = (self.init_timer.statistics)

        for obj in self.object_registry:
            try:
                name = str(obj)
                # Ensure we capture all distinct object stats by giving each a distinct name
                i = 0
                while name in stats:
                    i += 1
                    name = "{}_{}".format(obj, i)
                stats[name] = obj.statistics
            except AttributeError as e:
                self.log.info("'{}' does not report statistics. Msg={}".format(obj, e))
            except Exception as e:  # pylint: disable=broad-except
                self.log.exception(e)

        stats['Task Load'] = (self.load_timer.statistics)

        # Only report finish stats if something significant was done there
        if self.finish_timer.seconds_elapsed > 1:
            stats['Task Finish'] = (self.finish_timer.statistics)

        return stats

    def close(self):
        """
        Cleanup the task. Close any registered objects, close any database connections.
        """
        try:
            self.log.debug("close")
            for obj in self.object_registry:
                if hasattr(obj, 'close'):
                    obj.close()
                del obj
            del self.object_registry
            for database in self._database_pool:
                database.bind.dispose()
                database.clear()
            del self._database_pool
        except Exception as e:  # pylint: disable=broad-except
            self.log.debug(repr(e))

    def __enter__(self):
        return self

    def __exit__(self, exit_type, exit_value, exit_traceback):
        self.close()


def run_task(task_name,
             parameters=None,
             config=None,
             no_mail=None,
             # Scheduler specific
             scheduler=None,
             task_id=None,
             parent_task_id=None,
             root_task_id=None,
             parent_to_child=None,
             child_to_parent=None,
             ):
    """
    Used to find an ETL task module and start it.

    Parameters
    ----------
    task_name: str
        The task name to run. Must match the name or at least *ending* of the name of a module under **etl_jobs**.
    class_name: str
        The class name within the module. Defaults to None which means it expects to find one ETLTask based class there.
    arameters: list or dict
        Parameters for the task. Passed to method :meth:`bi_etl.scheduler.task.ETLTask.add_parameters`.
    config: bi_etl.bi_config_parser.BIConfigParser 
        The configuration to use (defaults to reading it from :doc:`config_ini`).
        If passed it should be an instance of :class:`bi_etl.bi_config_parser.BIConfigParser`.
    no_mail: boolean
        Skip sending email on failure? See no_mail in :meth:`bi_etl.scheduler.task.ETLTask.run`.
    scheduler: bi_etl.scheduler.scheduler.Scheduler
        The :class:`bi_etl.scheduler.scheduler.Scheduler` this job should be run under. 
        Optional. Defaults to not running via a scheduler.
    task_id: int
        The task_id of the job (only for :class:`bi_etl.scheduler.scheduler.Scheduler`).
    parent_task_id: int
        The task_id of the parent of this job (only for :class:`bi_etl.scheduler.scheduler.Scheduler`).
    root_task_id: int
        The task_id of the root ancestor of this job (only for :class:`bi_etl.scheduler.scheduler.Scheduler`).
    parent_to_child: Queue
        A queue to use for parent to child communication (only for :class:`bi_etl.scheduler.scheduler.Scheduler`).
    child_to_parent: Queue 
        A queue to use for child to parent communication (only for :class:`bi_etl.scheduler.scheduler.Scheduler`).
    """
    # For memory testing
    #tr = tracker.SummaryTracker()
    #tr.diff()
    ran_ok = False
    try:
        logging.basicConfig(level=logging.DEBUG)
        queue_out_stream = queue_io.redirect_output_to(child_to_parent)
        print("run_task...")
        if config is None:
            print("Reading config")
            config = BIConfigParser()
            config.read_config_ini()
            config.set_dated_log_file_name(task_name, '.log')
            print("setup_logging")
            config.setup_logging(queue_out_stream)
        elif isinstance(config, str):
            configFile = config.split(',')
            print(("Using config file(s) {}".format(configFile)))
            config = BIConfigParser()
            config.read(configFile)
            config.set_dated_log_file_name(task_name, '.log')
            print("setup_logging")
            config.setup_logging(queue_out_stream)
        else:
            print("Using passed config")

        print(('Scanning for task matching {}'.format(task_name)))
        # Import is done here to prevent circular module depencency
        from bi_etl.scheduler.scheduler_interface import SchedulerInterface
        if scheduler is None:
            scheduler = SchedulerInterface()
        etl_class = scheduler.find_etl_class_instance(task_name)
        etl_task = etl_class(task_id=task_id,
                             parent_task_id=parent_task_id,
                             root_task_id=root_task_id,
                             scheduler=scheduler,
                             config=config,
                             )
        if parameters is not None and len(parameters) > 0:
            etl_task.set_parameters(parameters)
        ran_ok = etl_task.run(no_mail=no_mail,
                              parent_to_child=parent_to_child,
                              child_to_parent=child_to_parent,
                              )
        # print('ran_ok = {}'.format(ran_ok))
        etl_task.close()
        print("run_task is done")

        # For memory testing
        #gc.collect()
        #tr.print_diff()

    except Exception as e:
        traceback.print_exc()
        print((repr(e)))
        if child_to_parent is not None:
            child_to_parent.put(e)
        raise e

    queue_io.restore_standard_output()
    return ran_ok
