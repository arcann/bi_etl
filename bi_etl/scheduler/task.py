"""
Created on Sep 15, 2014

@author: Derek Wood
"""
import errno
import importlib
import logging
import socket
import traceback
import warnings
from pathlib import Path
from queue import Empty
from typing import *

from config_wrangler.config_templates.sqlalchemy_database import SQLAlchemyDatabase, SQLAlchemyMetadata
from config_wrangler.config_types.dynamically_referenced import DynamicallyReferenced
from pydicti import dicti, Dicti

import bi_etl.config.notifiers_config as notifiers_config
from bi_etl import utility
from bi_etl.components.etlcomponent import ETLComponent
from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base, BI_ETL_Config_Base_From_Ini_Env
from bi_etl.database.database_metadata import DatabaseMetadata
from bi_etl.notifiers import LogNotifier, Email, Slack, Jira
from bi_etl.notifiers.notifier_base import NotifierBase
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

if TYPE_CHECKING:
    from bi_etl.scheduler.scheduler_interface import SchedulerInterface

# pylint: disable=too-many-instance-attributes, too-many-public-methods
# pylint: disable=too-many-statements, too-many-branches, too-many-arguments


class ETLTask(object):
    """
    ETL Task runnable base class.

    load() **must** be overridden.

    depends_on() should be overridden.

    start_following_tasks() can be overridden.
    """

    CLASS_VERSION = 1.0

    def __init__(self,
                 config: BI_ETL_Config_Base,
                 task_id=None,
                 parent_task_id=None,
                 root_task_id=None,
                 scheduler=None,
                 task_rec=None,
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
        config: bi_etl.config.bi_etl_config_base.BI_ETL_Config_Base
            The configuration :class:`bi_etl.config.bi_etl_config_base.BI_ETL_Config_Base` to use
            (See :doc:`config_ini`).
        """
        self.config = config
        self._log = None
        self.log_file_name = None
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
        if self.status is None:
            self.status = Status.new
        self._parameters_loaded = False
        self._parameter_dict = dicti()
        self.parent_to_child = None
        self.child_to_parent = None
        self.object_registry = list()
        self.thread_running = None
        self.summary_message_from_client = False
        self.last_log_msg_time = None
        self.pending_log_msgs = list()
        self.warning_messages = set()
        self.last_log_msg = ""
        self.exception = None
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
        self._manager = None
        # Used by the scheduler to tell if this task has written it's dependencies to the log
        self._logged_dependencies = False
        self._normalized_dependents_set = None
        self._mutually_exclusive_with_set = None
        self._database_pool = list()
        self.init_timer = Timer(start_running=False)
        self.load_timer = Timer(start_running=False)
        self.finish_timer = Timer(start_running=False)
        self.suppress_notifications = False
        self.log_handler = None

    def __getstate__(self):
        odict = dict()
        odict['version'] = self.CLASS_VERSION
        odict['task_id'] = self.task_id
        odict['root_task_id'] = self.root_task_id
        odict['parent_task_id'] = self.parent_task_id
        odict['status'] = self.status
        odict['parent_to_child'] = self.parent_to_child
        odict['child_to_parent'] = self.child_to_parent
        odict['_parameter_dict'] = dict(self._parameter_dict)
        odict['config'] = self.config
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
                      config=odict['config'],
                      # We don't pass scheduler from the Scheduler to the running instance
                      # scheduler= odict['scheduler']
                      )
        self.parent_to_child = odict['parent_to_child']
        self.child_to_parent = odict['child_to_parent']
        self._parameter_dict = Dicti(odict['_parameter_dict'])

    def shutdown(self):
        if self._manager is not None:
            self._manager.shutdown()

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
    def environment_name(self):
        environment = self.config.bi_etl.environment_name
        if environment == '*qualified_host_name*':
            if self._scheduler is not None:
                environment = self._scheduler.qualified_host_name
            else:
                environment = socket.gethostname()
        return environment

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
            from bi_etl.scheduler.scheduler import Scheduler
            if isinstance(self.scheduler, Scheduler):
                assert isinstance(self.scheduler, Scheduler)
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

    def add_warning(self, warning_message):
        self.warning_messages.add(warning_message)

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
    def scheduler(self) -> 'SchedulerInterface':
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
            self._scheduler = SchedulerInterface(
                config=self.config,
            )
        return self._scheduler

    def add_child_task_to_scheduler(
            self,
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
            new_task_id = self.scheduler.add_task_by_class(
                etl_task_class_type,
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
            new_task_id = self.scheduler.add_task_by_partial_name(
                partial_module_name,
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

    def set_parameter(
            self,
            param_name: str,
            param_value: object,
            local_only: bool = False,
            commit: bool = True
    ):
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
    def add_parameter(
            self,
            param_name: str,
            param_value: object,
            local_only: bool = False,
            commit: bool = True,
    ):
        warnings.warn("add_parameter is deprecated, please use set_parameter instead")
        self.set_parameter(param_name=param_name,
                           param_value=param_value,
                           local_only=local_only,
                           commit=commit)

    def set_parameters(
            self,
            local_only=False,
            commit=True,
            *args,
            **kwargs
    ):
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
        #
        # which is equivalent to
        #     add_parameters(**parms)
        for arg in args:
            if isinstance(arg, Mapping):
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

    def get_database_name(self):
        """
        Returns the database name (entry in config) to use for calls to get_database where
        no name is provided.

        :return:
        """
        return NotImplementedError()

    def get_database_metadata(self, db_config: SQLAlchemyDatabase) -> DatabaseMetadata:
        if isinstance(db_config, SQLAlchemyMetadata):
            database_obj = DatabaseMetadata(
                bind=db_config.get_engine(),
                schema=db_config.schema,
            )
        elif isinstance(db_config, SQLAlchemyDatabase):
            database_obj = DatabaseMetadata(
                bind=db_config.get_engine(),
            )
        else:
            raise ValueError(
                "get_database_metadata expects SQLAlchemyDatabase or SQLAlchemyMetadata configs. "
                f"Got {type(db_config)} {db_config}"
            )
        self.add_database(database_obj)
        return database_obj

    def get_database(self, database_name: str) -> DatabaseMetadata:
        db_config = getattr(self.config, database_name)
        return self.get_database_metadata(db_config)

    def get_sql_script_runner(
            self,
            script_name: Union[str, Path],
            script_path: Union[str, Path],
            database_entry: Union[str, DatabaseMetadata, None] = None,
    ):
        if database_entry is None:
            database_entry = self.get_database_name()
        # Late import to avoid circular dependency
        from bi_etl.utility.run_sql_script import RunSQLScript
        return RunSQLScript(
            config=self.config,
            database_entry=database_entry,
            script_path=script_path,
            script_name=script_name,
        )

    def run_sql_script(
            self,
            script_name: Union[str, Path],
            script_path: Union[str, Path],
            database_entry: Union[str, DatabaseMetadata],
    ):
        runner = self.get_sql_script_runner(
            script_name=script_name,
            script_path=script_path,
            database_entry=database_entry,
        )
        ok = runner.run()
        if not ok:
            raise ValueError(f"{script_name} {runner} failed with error {runner.exception}")

    def register_object(self, obj: Union[ETLComponent, Statistics]):
        """
        Register an ETLComponent or Statistics object with the task.
        This allows the task to 
        1) Get statistics from the component
        2) Close the component when done
        
        """
        self.object_registry.append(obj)
        return obj

    def make_statistics_entry(self, stats_id) -> Statistics:
        stats = Statistics(stats_id=stats_id)
        self.register_object(stats)
        return stats

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

        if self.log_file_name is None:
            self.log_file_name = self.name
        self.config.logging.setup_logging()
        self.log_handler = self.config.logging.add_log_file_handler(log_file_prefix=self.log_file_name)

        self.log_logging_level()
        self.log.debug("externally_provided_scheduler = {}".format(self._externally_provided_scheduler))

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

    # noinspection PyMethodMayBeStatic
    def allow_concurrent_runs(self):
        return False

    # noinspection PyMethodMayBeStatic
    def needs_to_ok_child_runs(self):
        """
        Override and return True if you need to give OK before children are allowed to run.
        See process_child_run_requested
        """
        return False

    def process_child_run_requested(self, child_run_requested):
        """
        Override to examine child task before giving OK.
        """
        self.send_mesage(ChildRunOK(child_run_requested.child_task_id))

    # noinspection PyMethodMayBeStatic
    def needs_to_get_child_statuses(self):
        """
        Override and return True if you want to get status updates on children.
        """
        return False

    # noinspection PyMethodMayBeStatic
    def needs_to_get_ancestor_statuses(self):
        """
        Override and return True if you want to get status updates on any ancestor.
        """
        return False

    def process_child_status_update(self, child_status_update):
        """
        Override to examine child task status (ChildRunFinished instances)
        """
        pass

    def process_messages(self, block=False):
        """
        Processes messages for this task.  Should be called somewhere in any row looping.

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
        
        Parameters
        ----------
        block: boolean 
            Block while waiting. Defaults to False.
            If block is True, this will run until a terminating message is received or an exception is thrown by the process_X calls.
            If block if False, you probably want to call inside a loop.
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
            suppress_notifications=None,
            parent_to_child=None,
            child_to_parent=None,
            handle_exceptions=True,
            ):
        """
        Should not generally be overridden.
        This is called to run the task's code in the init, load, and finish methods.
        """
        self.child_to_parent = child_to_parent
        self.parent_to_child = parent_to_child
        self.__thread_init()

        if suppress_notifications is None:
            # If run directly, assume it a testing run and don't send e-mails
            if self.__class__.__module__ == '__main__':
                self.log.info("Direct module execution detected. Notifications will not be sent")
                self.suppress_notifications = True
        else:
            self.suppress_notifications = suppress_notifications

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
            self.close(error=False)
        except Exception as e:  # pylint: disable=broad-except
            self.close(error=True)
            self.exception = e
            self.status = Status.failed
            if not handle_exceptions:
                raise e
            self.log.exception(e)
            self.log.error(e)
            self.log.info(repr(e))
            self.log.info(utility.dict_to_str(e.__dict__))
            if not self.suppress_notifications:
                environment = self.config.bi_etl.environment_name
                message_list = list()
                message_list.append(repr(e))
                message_list.append("Task ID = {}".format(self.task_id))
                if self.config.bi_etl.scheduler is not None:
                    ui_url = self.config.bi_etl.scheduler.base_ui_url
                    if ui_url and self.task_id:
                        message_list.append("Run details are here: {}{}".format(ui_url, self.task_id))
                message_content = '\n'.join(message_list)
                subject = f"{environment} {self} load failed"

                self.notify(self.config.notifiers.failures, subject=subject, message=message_content,)

            self.log.info("{} FAILED.".format(self))
            if self.child_to_parent is not None:
                self.child_to_parent.put(e)
        finally:
            self.config.logging.remove_log_handler(self.log_handler)

        self.log.info("Status = {}".format(repr(self.status)))

        # Send out status
        if self.child_to_parent is not None:
            self.child_to_parent.put(self.status)

        return self.status == Status.succeeded

    def get_notifiers(self, channel_list: List[DynamicallyReferenced], auto_include_log=True) -> List[NotifierBase]:
        notifiers_list = list()
        notifier_class_str = 'unset'

        if auto_include_log:
            notifiers_list.append(LogNotifier())

        for config_ref in channel_list:
            config_section = config_ref.get_referenced()
            if not isinstance(config_section, notifiers_config.NotifierConfigBase):
                raise ValueError(f"Notifier is not an instance of NotifierConfigBase: type= {type(config_section)} value= {config_section}")
            try:
                if config_section == 'LogNotifier':
                    notifier_class_str = config_section
                else:
                    notifier_class_str = config_section.notifier_class

                if isinstance(config_section, notifiers_config.LogNotifierConfig):
                    notifier_instance = LogNotifier()
                elif isinstance(config_section, notifiers_config.SMTP_Notifier):
                    notifier_instance = Email(config_section)
                elif isinstance(config_section, notifiers_config.SlackNotifier):
                    notifier_instance = Slack(config_section)
                elif isinstance(config_section, notifiers_config.JiraNotifier):
                    notifier_instance = Jira(config_section)
                else:
                    module, class_name = config_section.notifier_class.rsplit('.', 1)
                    mod_object = importlib.import_module(module)
                    class_object = getattr(mod_object, class_name)
                    notifier_instance = class_object(config_section)

                if notifier_instance is not None:
                    notifiers_list.append(notifier_instance)
            except Exception as e:
                self.log.exception(e)
                if self.config.notifiers.failed_notifications is not None:
                    try:
                        fallback_message = f'Notification to {config_section} {notifier_class_str} failed with error={e}'
                        fallback_notifiers_list = self.get_notifiers(self.config.notifiers.failed_notifications)
                        for fallback_notifier in fallback_notifiers_list:
                            fallback_notifier.send(
                                subject=f"Failed to send to {config_section}",
                                message=fallback_message,
                            )
                            notifiers_list.append(fallback_notifier)
                    except Exception as e:
                        self.log.exception(e)
        return notifiers_list

    def notify(
            self,
            channel_list: List[DynamicallyReferenced],
            subject,
            message=None,
            sensitive_message: str = None,
            attachment=None,
            skip_channels: set = None,
    ):
        if not self.suppress_notifications:
            # Note: all exceptions are caught since we don't want notifications to kill the load
            try:
                filtered_channels = list()

                for channel in channel_list:
                    if skip_channels is None or channel.ref not in skip_channels:
                        filtered_channels.append(channel)

                notifiers_list = self.get_notifiers(filtered_channels)
                for notifier in notifiers_list:
                    try:
                        notifier.send(
                            subject=subject,
                            message=message,
                            sensitive_message=sensitive_message,
                            attachment=attachment,
                        )
                    except Exception as e:
                        self.log.exception(e)
                        if self.config.notifiers.failed_notifications is not None:
                            fallback_message = f"error={e} original_subject={subject} original_message={message}"
                            fallback_notifiers_list = self.get_notifiers(self.config.notifiers.failed_notifications)
                            for fallback_notifier in fallback_notifiers_list:
                                try:
                                    fallback_notifier.send(
                                        subject=f"Failed to send to {notifier}",
                                        message=fallback_message,
                                        sensitive_message=sensitive_message,
                                        attachment=attachment,
                                    )
                                except Exception as e:
                                    self.log.exception(e)

            except Exception as e:
                self.log.exception(e)

    @property
    def statistics(self):
        """
        Return the execution statistics from the task and all of it's registered components.
        """
        stats = Statistics(self.name)
        # Only report init stats if something significant was done there
        if self.init_timer.seconds_elapsed > 1:
            stats['Task Init'] = self.init_timer.statistics

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

        stats['Task Load'] = self.load_timer.statistics

        # Only report finish stats if something significant was done there
        if self.finish_timer.seconds_elapsed > 1:
            stats['Task Finish'] = self.finish_timer.statistics

        return stats

    def close(self, error: bool = False):
        """
        Cleanup the task. Close any registered objects, close any database connections.
        """
        try:
            self.log.debug("close")
            for obj in self.object_registry:
                if hasattr(obj, 'close'):
                    obj.close(error=error)
                del obj
            del self.object_registry
            self.object_registry = list()
            for database in self._database_pool:
                database.bind.dispose()
                database.clear()
            del self._database_pool
            self._database_pool = list()
        except Exception as e:  # pylint: disable=broad-except
            self.log.debug(repr(e))

    def __enter__(self):
        return self

    def __exit__(self, exit_type, exit_value, exit_traceback):
        self.close()


##################


def run_task(task_name,
             parameters=None,
             config=None,
             suppress_notifications=None,
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
    parameters: list or dict
        Parameters for the task. Passed to method :meth:`bi_etl.scheduler.task.ETLTask.add_parameters`.
    config: Union[str, bi_etl.config.bi_etl_config_base.BI_ETL_Config_Base]
        The configuration to use (defaults to reading it from :doc:`config_ini`).
        If passed it should be an string reference to an ini file
        or an instance of :class:`bi_etl.config.bi_etl_config_base.BI_ETL_Config_Base`.
    suppress_notifications: boolean
        Skip sending email on failure? See suppress_notifications in :meth:`bi_etl.scheduler.task.ETLTask.run`.
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
    # tr = tracker.SummaryTracker()
    # tr.diff()

    try:
        logging.basicConfig(level=logging.DEBUG)
        queue_out_stream = queue_io.redirect_output_to(child_to_parent)
        print("run_task...")
        if config is None:
            config = BI_ETL_Config_Base()
        elif isinstance(config, str):
            config = BI_ETL_Config_Base_From_Ini_Env(file_name=config)
        else:
            print("Using passed config")

        print(('Scanning for task matching {}'.format(task_name)))
        # Import is done here to prevent circular module dependency
        from bi_etl.scheduler.scheduler_interface import SchedulerInterface
        if scheduler is None:
            scheduler = SchedulerInterface(config)
        etl_class = scheduler.find_etl_class_instance(task_name)
        etl_task = etl_class(task_id=task_id,
                             parent_task_id=parent_task_id,
                             root_task_id=root_task_id,
                             scheduler=scheduler,
                             config=config,
                             )
        if parameters is not None and len(parameters) > 0:
            etl_task.set_parameters(parameters)
        ran_ok = etl_task.run(suppress_notifications=suppress_notifications,
                              parent_to_child=parent_to_child,
                              child_to_parent=child_to_parent,
                              )
        # print('ran_ok = {}'.format(ran_ok))
        etl_task.close()
        print("run_task is done")

        # For memory testing
        # gc.collect()
        # tr.print_diff()

    except Exception as e:
        traceback.print_exc()
        print((repr(e)))
        if child_to_parent is not None:
            child_to_parent.put(e)
        raise e

    queue_io.restore_standard_output()
    return ran_ok
