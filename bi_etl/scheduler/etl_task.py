"""
Created on Sep 15, 2014

@author: Derek Wood
"""
import importlib
import inspect
import logging
import socket
import types
import uuid
import warnings
from contextlib import ExitStack
from functools import lru_cache
from inspect import signature
from pathlib import Path
from typing import *

from config_wrangler.config_templates.config_hierarchy import ConfigHierarchy
from config_wrangler.config_templates.sqlalchemy_database import SQLAlchemyDatabase
from config_wrangler.config_types.dynamically_referenced import DynamicallyReferenced
from pydicti import dicti, Dicti

import bi_etl
import bi_etl.config.notifiers_config as notifiers_config
from bi_etl import utility
from bi_etl.components.etlcomponent import ETLComponent
from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base, BI_ETL_Config_Base_From_Ini_Env
from bi_etl.database.database_metadata import DatabaseMetadata
from bi_etl.notifiers import LogNotifier, Email, Slack, Jira
from bi_etl.notifiers.notifier_base import NotifierBase
from bi_etl.scheduler.exceptions import ParameterError
from bi_etl.scheduler.status import Status
from bi_etl.statistics import Statistics
from bi_etl.timer import Timer
from bi_etl.utility.dagster_utils.dagster_types import (
    dagster,
    DAGSTER_ASSET_KEY, DAGSTER_INPUTS_TYPE, DAGSTER_ASSET_IN,
    DAGSTER_CONFIG, DAGSTER_AUTO_MATERIALIZE_POLICY, DAGSTER_SENSOR_TYPE, DAGSTER_ASSETS_TYPE, _DAGSTER_INPUT_TYPE,
)

if TYPE_CHECKING:
    from bi_etl.utility.run_sql_script import RunSQLScript


class ETLTask(object):
    """
    ETL Task runnable base class.

    load() **must** be overridden.
    """
    CLASS_VERSION = 1.0
    _task_repo: Dict[str, 'ETLTask'] = dict()

    DAGSTER_compute_kind = 'python'

    @staticmethod
    def is_etl_task(item: Any):
        if inspect.isclass(item):
            baseclasses = inspect.getmro(item)
            if ETLTask in baseclasses:
                return True
        return False

    @staticmethod
    def get_etl_task_instance(input: _DAGSTER_INPUT_TYPE) -> Type['ETLTask']:
        if input is None:
            raise ValueError("get_etl_task_instance got None")

        if isinstance(input, types.ModuleType):
            module = input
            class_matches = list()
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj):
                    # Check that the class is defined in our module and not imported
                    if obj.__module__ == module.__name__:
                        if ETLTask.is_etl_task(obj) and str(obj) != str(ETLTask):
                            class_matches.append(obj)
                            print(obj)
            if len(class_matches) == 0:
                raise ValueError(f"No ETLTask found in {module}")
            elif len(class_matches) > 1:
                raise ValueError(f"Multiple ETLTasks found in {module}")
            else:
                # noinspection PyTypeChecker
                return class_matches[0]
        else:
            if ETLTask.is_etl_task(input):
                return input
            else:
                raise ValueError(
                    f"get_etl_task_instance passed {input} type={type(input)}. "
                    "Expected module or ETLTask based class."
                )

    @staticmethod
    def get_etl_task_list(input_list: DAGSTER_INPUTS_TYPE) -> List[Type['ETLTask']]:
        if input_list is None:
            return list()

        output_list = list()
        for task in input_list:
            if isinstance(task, types.ModuleType):
                module = task
                class_matches = list()
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj):
                        # Check that the class is defined in our module and not imported
                        if obj.__module__ == module.__name__:
                            if ETLTask.is_etl_task(obj) and str(obj) != str(ETLTask):
                                class_matches.append(obj)
                                print(obj)
                if len(class_matches) == 0:
                    raise ValueError(f"No ETLTask found in {module}")
                elif len(class_matches) > 1:
                    raise ValueError(f"Multiple ETLTasks found in {module}")
                else:
                    task = class_matches[0]
            output_list.append(task)
        return output_list

    @classmethod
    @lru_cache(maxsize=None)
    def dagster_asset_key(cls, **kwargs) -> DAGSTER_ASSET_KEY:
        module_name = cls.__module__
        asset_key_list = module_name.split('.')
        class_name = cls.__qualname__
        asset_key_list.append(class_name)
        return DAGSTER_ASSET_KEY(asset_key_list)

    @classmethod
    @lru_cache(maxsize=None)
    def dagster_job_name(cls, **kwargs) -> str:
        return cls.dagster_asset_key().path[-1]

    @classmethod
    @lru_cache(maxsize=None)
    def dagster_key_prefix(cls, **kwargs) -> Sequence[str]:
        return cls.dagster_asset_key().path[:-1]

    @classmethod
    @lru_cache(maxsize=None)
    def dagster_group_name(cls, **kwargs) -> Optional[str]:
        """
        group_name (Optional[str]): A string name used to organize multiple assets into groups.
        If not provided try these defaults in this order:
          - The asset key prefix will be used
          - The name "default" is used.
        """
        key_prefix = cls.dagster_key_prefix()
        if len(key_prefix) <= 1:
            return None
        else:
            # Could also build and AssetKey and call to_python_identifier
            return '__'.join(key_prefix[:-1])

    @classmethod
    @lru_cache(maxsize=None)
    def dagster_input_etl_tasks(cls, **kwargs) -> DAGSTER_INPUTS_TYPE:
        """
        List of ETLTask subclasses that are inputs to this task.
        Note: This needs to return the class objects and not instances of that class.
        """
        return []

    @classmethod
    @lru_cache(maxsize=None)
    def dagster_inputs_asset_id(cls, **kwargs) -> Dict[str, DAGSTER_ASSET_IN]:
        """
        Starting dictionary of dagster asset inputs.
        Normally the inputs will come from dagster_input_etl_tasks.
        """
        return {}

    @classmethod
    @lru_cache(maxsize=None)
    def dagster_get_config(
            cls,
            dagster_config: DAGSTER_CONFIG = None,
            *,
            debug: bool = False,
            **kwargs
    ) -> BI_ETL_Config_Base:
        """
        Build a config (subclass of BI_ETL_Config) for use by dagster runs.
        """
        # # Can we use dagster_config to set config items?
        # fields = dagster_config.to_fields_dict()
        # return BI_ETL_Config_Base(**fields)
        if dagster_config is not None:
            if debug:
                print("   WARNING: dagster_config is ignored")
        return BI_ETL_Config_Base_From_Ini_Env()

    @classmethod
    @lru_cache(maxsize=None)
    def dagster_auto_materialize_policy(
            cls,
            *,
            debug: bool = False,
            **kwargs
    ) -> Optional[DAGSTER_AUTO_MATERIALIZE_POLICY]:
        """
        auto_materialize_policy (AutoMaterializePolicy): (Experimental) Configure Dagster to automatically materialize
            this asset according to its FreshnessPolicy and when upstream dependencies change.
        """
        return dagster.AutoMaterializePolicy.eager().with_rules(
            dagster.AutoMaterializeRule.skip_on_not_all_parents_updated()
        )
        # return None

    @classmethod
    @lru_cache(maxsize=None)
    def dagster_retry_policy(
            cls,
            **kwargs
    ) -> Optional[dagster.RetryPolicy]:
        """
        retry_policy (Optional[RetryPolicy]): The retry policy for the op that computes the asset.
        """
        return None

    @classmethod
    @lru_cache(maxsize=None)
    def dagster_code_version(
            cls,
            **kwargs
    ) -> Optional[str]:
        """
         code_version (Optional[str]): (Experimental) Version of the code that generates this asset. In
            general, versions should be set only for code that deterministically produces the same
            output when given the same inputs.
        """
        return None

    @classmethod
    @lru_cache(maxsize=None)
    def dagster_description(
            cls,
            **kwargs
    ) -> Optional[str]:
        return None

    @classmethod
    @lru_cache(maxsize=None)
    def dagster_op_tags(
            cls,
            **kwargs
    ) -> Optional[Mapping[str, Any]]:
        """
        op_tags (Optional[Dict[str, Any]]): A dictionary of tags for the op that computes the asset.
            Frameworks may expect and require certain metadata to be attached to an op. Values that
            are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.
        """
        return None

    @classmethod
    @lru_cache(maxsize=None)
    def dagster_partitions_def(
            cls,
            *,
            debug: bool = False,
            **kwargs
    ) -> Optional[dagster.PartitionsDefinition]:
        """
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the asset.
        """
        return None

    @classmethod
    @lru_cache(maxsize=None)
    def dagster_asset_definition(
            cls,
            scope_set: Optional[Set[DAGSTER_ASSET_KEY]] = None,
            before_all_assets: Optional[Iterable[DAGSTER_ASSETS_TYPE]] = None,
            *,
            debug: bool = False,
            **kwargs
    ) -> dagster.AssetsDefinition:
        """
        Build a dagster asset for this ETLTask class.
        Note: The load method can capture and return results to dagster using the
              dagster_results member of the instance.  Those will be passed to jobs for assets
              that depend on this asset.

        Parameters
        ----------
        scope_set:
            A set of other assets that are in the current scope.
            If this is provided, it will be used to filter the dependencies to assets in the set.
        debug:
            True to print debug messages.
        kwargs:
            Placeholder for other arguments

        Returns
        -------
        AssetsDefinition built using the dagster_* class method results.

        """
        import dagster

        this_asset_key = cls.dagster_asset_key()
        if debug:
            print(f"Creating asset {this_asset_key}")
        job_name = this_asset_key.path[-1]
        key_prefix = this_asset_key.path[:-1]

        input_dict = cls.dagster_inputs_asset_id()
        input_etl_tasks = cls.get_etl_task_list(cls.dagster_input_etl_tasks())

        if input_etl_tasks is None or len(input_etl_tasks) == 0:
            if before_all_assets is not None:
                for dep in before_all_assets:
                    dep_asset_key = dep.key
                    input_dict[dep_asset_key.path[-1]] = dagster.AssetIn(key=dep_asset_key)

        else:
            for dep in input_etl_tasks:
                dep_asset_key = dep.dagster_asset_key()
                # Only add the dep if it is in our scope, or we have no scope
                if scope_set is None or dep_asset_key in scope_set:
                    input_dict[dep_asset_key.path[-1]] = dagster.AssetIn(key=dep_asset_key)
                    if debug:
                        print(f"   Adding dep {dep_asset_key}")
                else:
                    if debug:
                        print(f"   Skipping out of scope input {dep_asset_key}")

        @dagster.asset(
            name=job_name,
            key_prefix=key_prefix,
            ins=input_dict,
            auto_materialize_policy=cls.dagster_auto_materialize_policy(),
            retry_policy=cls.dagster_retry_policy(),
            group_name=cls.dagster_group_name(),
            compute_kind=cls.DAGSTER_compute_kind,
            code_version=cls.dagster_code_version(),
            description=cls.dagster_description(),
            op_tags=cls.dagster_op_tags(),
            partitions_def=cls.dagster_partitions_def(),
        )
        def run_task_via_dagster(
                context: dagster.AssetExecutionContext,
                config: dagster.PermissiveConfig,  # dagster config not bi_etl config
                **run_kwargs
        ):
            bi_etl_config = cls.dagster_get_config(config)

            job_inst = cls(
                config=bi_etl_config,
                root_task_id=context.run_id,
                task_id=context.asset_key,
                parent_task_id=context.dagster_run.parent_run_id,
            )
            job_inst.run(
                handle_exceptions=False,
                context=context,
                **run_kwargs
            )
            return job_inst.dagster_results

        return run_task_via_dagster

    @classmethod
    def dagster_schedules(
            cls,
            *,
            debug: bool = False,
            **kwargs
    ) -> Optional[Sequence[dagster.ScheduleDefinition]]:
        """
        Return one or more schedules linked to this task.
        They don't have to run only this task.
        """
        return None

    @classmethod
    def dagster_sensors(
            cls,
            *,
            debug: bool = False,
            **kwargs
    ) -> Optional[Sequence[DAGSTER_SENSOR_TYPE]]:
        """
        Return a list of one more sensors for this task
        """
        return None

    def __init__(self,
                 config: BI_ETL_Config_Base,
                 parent_task_id=None,
                 root_task_id=None,
                 **kwargs
                 ):
        """
        Constructor.
        It should do as little as possible.

        Parameters
        ----------
        parent_task_id:
            The task_id of the parent of this job
        root_task_id:
            The task_id of the root ancestor of this job
        config: bi_etl.config.bi_etl_config_base.BI_ETL_Config_Base
            The configuration :class:`bi_etl.config.bi_etl_config_base.BI_ETL_Config_Base` to use
            (See :doc:`config_ini`).
        """
        self.config = config
        self._log = None
        self.log_file_name = None
        self._task_rec = None

        self.task_id = uuid.uuid4()
        self.parent_task_id = parent_task_id
        self.root_task_id = root_task_id
        self.status = Status.new
        self._parameters_loaded = False
        self._parameter_dict = dicti()
        self.set_parameters(**kwargs)
        self.object_registry = list()
        self._exit_stack = ExitStack()
        self.thread_running = None
        self.summary_message_from_client = False
        self.last_log_msg_time = None
        self.pending_log_msgs = list()
        self.warning_messages = set()
        self.last_log_msg = ""
        self.exception = None
        self._manager = None
        self._database_pool = list()
        self.init_timer = Timer(start_running=False)
        self.load_timer = Timer(start_running=False)
        self.finish_timer = Timer(start_running=False)
        self.suppress_notifications = False
        # noinspection PyTypeChecker
        self._notifiers: Dict[NotifierBase] = dict()
        self.log_notifier = LogNotifier(name='log')
        self.log_handler = None
        self.dagster_results = None

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
        return odict

    def __setstate__(self, odict):
        if 'version' not in odict:
            odict['version'] = 0.0
        if odict['version'] != self.CLASS_VERSION:
            raise ValueError("ETLTask versions incompatible between scheduler and target server")
        self.__init__(task_id=odict['task_id'],
                      parent_task_id=odict['parent_task_id'],
                      root_task_id=odict['root_task_id'],
                      config=odict['config'],
                      )
        self.parent_to_child = odict['parent_to_child']
        self.child_to_parent = odict['child_to_parent']
        self._parameter_dict = Dicti(odict['_parameter_dict'])

    @property
    def dagster_context(self) -> Optional[dagster.AssetExecutionContext]:
        return self.get_parameter('context', default=None)

    def shutdown(self):
        if self._manager is not None:
            self._manager.shutdown()

    def log_logging_level(self):
        # Calling bi_etl.utility version
        utility.log_logging_level(self.log)

    def __repr__(self):
        return f"{self.name}(task_id={self.task_id}, " \
               f"parent_task_id={self.parent_task_id}, " \
               f"root_task_id={self.root_task_id})"

    def __str__(self):
        return self.name

    @property
    def name(self):
        """
        Note: Return value needs to be compatible with find_etl_class
        """
        module = self.__class__.__module__
        return f"{module}.{self.__class__.__name__}"

    @property
    def environment_name(self):
        environment = self.config.bi_etl.environment_name
        if environment == '*qualified_host_name*':
            environment = socket.gethostname()
        return environment

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
    def depends_on(self) -> Iterable['ETLTask']:
        """
        Override to provide a static list of tasks that this task will wait on if they are running.

        Each dependent task entry should consist of either
        1) The module name (str)
        2) A tuple of the module name (str) and class name (str)
        """
        return list()

    def internal_tasks(self) -> Iterable['ETLTask']:
        """
        Override to provide a static list of tasks that this task will run internally.
        Can be used by the job orchestrator to build a complete dependency tree.
        """
        return list()

    def dependency_full_set(self, parents: tuple = None) -> FrozenSet['ETLTask']:
        dependency_set = self.depends_on()
        if dependency_set is None:
            dependency_set = set()
        else:
            # Ensure dependency_set is in fact a set.
            # Even if it is a set, copy the set so that we don't modify the one sent by depends_on.
            # It might not always be a unique list object that is safe to modify
            dependency_set = set(dependency_set)

        # Find external dependencies of internal / sub-tasks
        internal_tasks = self.internal_tasks()

        self_tuple = (self,)
        if parents is None:
            parents = self_tuple
        else:
            parents = parents + self_tuple

        for sub_task in internal_tasks:
            if sub_task is None:
                continue
            if not isinstance(sub_task, ETLTask):
                raise ValueError(f"{self}.internal_tasks returned {sub_task} which is not an ETLTask")
            if sub_task not in parents:
                sub_deps = sub_task.dependency_full_set(parents=parents)
                if sub_deps is not None:
                    # Filter for dependencies outside this task
                    for sub_dep in sub_deps:
                        if sub_dep in parents or sub_dep == self:
                            raise ValueError(f"sub_task {sub_task} has dep {sub_dep} overlap with {self} or {parents}")
                        if sub_dep not in internal_tasks:
                            dependency_set.add(sub_dep)
        return frozenset(dependency_set)

    @property
    def target_database(self) -> DatabaseMetadata:
        raise NotImplementedError()

    # noinspection PyPep8Naming
    def PythonDep(self, etl_class_str: str) -> 'ETLTask':
        module, class_name = etl_class_str.rsplit('.', 1)
        mod_object = importlib.import_module(module)
        try:
            class_object = getattr(mod_object, class_name)
        except AttributeError:
            try:
                # First try the whole etl_class_str as a module name
                class_object = importlib.import_module(etl_class_str)
            except ModuleNotFoundError:
                # Next, try case-insensitive search
                found_matches = list()
                class_name_lower = class_name.lower()
                for found_class_name, found_class in inspect.getmembers(mod_object, inspect.isclass):
                    if found_class_name.lower() == class_name_lower:
                        found_matches.append(found_class)
                if len(found_matches) == 0:
                    raise ValueError(f"Module {mod_object} does not contain {class_name}")
                elif len(found_matches) > 1:
                    raise ValueError(
                        f"Module {mod_object} does contains more than one case-insensitive match for {class_name} "
                        f"they are {found_matches}"
                    )
                class_object = found_matches[0]

        if inspect.isclass(class_object):
            if not issubclass(class_object, ETLTask):
                raise ValueError(f"{etl_class_str} resolves to a class of {class_object} which is not a subclass of ETLTask")
        else:
            # class_object is most likely a module.  We'll search it for our class.
            matches = list()
            for class_in_module_name, class_in_module in inspect.getmembers(class_object, inspect.isclass):
                # Check that the class is defined in our module (directly or from a submodule)
                # and is not imported from elsewhere
                if class_in_module.__module__.startswith(class_object.__name__):
                    if issubclass(class_in_module, ETLTask) and class_in_module != ETLTask:
                        matches.append(class_in_module)
            if len(matches) > 1:
                raise ValueError(
                    f"PythonDep was given a module name '{etl_class_str}' and multiple ETLTask classes found inside it. "
                    f"Matches = {[match.name for match in matches]}"
                )
            elif len(matches) == 0:
                raise ValueError(
                    f"PythonDep was given a module name '{etl_class_str}' and no ETLTask classes found inside it. "
                )
            else:
                class_object = matches[0]

        etl_task = class_object(
            config=self.config,
        )
        return etl_task.get_task_singleton()

    # noinspection PyPep8Naming
    def SQLDep(
            self,
            sql_path: str,
            script_path: str = None,
            database: DatabaseMetadata = None
    ) -> 'RunSQLScript':
        if database is None:
            try:
                database = self.target_database
            except NotImplementedError:
                pass
        inst = self.get_sql_script_runner(
            database_entry=database,
            script_path=script_path,
            script_name=sql_path,
        )
        return inst.get_task_singleton()

    def load_parameters(self):
        """
        Load parameters for this task from the scheduler.
        """
        # set to loaded no matter what
        self._parameters_loaded = True

    def load_parameters_from_dict(self, parameters: dict):
        self._parameters_loaded = True
        for param_name, param_value in parameters.items():
            self.set_parameter(param_name, param_value)

    def set_parameter(
            self,
            param_name: str,
            param_value: object,
    ):
        """
        Add a single parameter to this task.

        Parameters
        ----------
        param_name: str
            The name of the parameter to add
        param_value: object
            The value of the parameter
        """
        if not self._parameters_loaded:
            self.load_parameters()
        self.log.info(f"add_parameter to task {param_name} = {repr(param_value)}")
        self._parameter_dict[param_name] = param_value

    def set_parameters(
            self,
            **kwargs
    ):
        """
        Add multiple parameters to this task.
        Parameters can be passed in as any combination of:
        * dict instance. Example ``set_parameters( {'param1':'example', 'param2':100} )``
        * list of lists. Example: ``set_parameters( [ ['param1','example'], ['param2',100] ] )``
        * list of tuples. Example: ``set_parameters( [ ('param1','example'), ('param2',100) ] )``
        * keyword arguments. Example: ``set_parameters(foo=1, bar='apple')``

        Parameters
        ----------
        kwargs:
            keyword arguments send to parameters. See above.
        """
        # Support set_parameters(param1='example', param2=100)
        self._parameter_dict.update(kwargs)
        for param_name, param_value in kwargs.items():
            self.set_parameter(param_name, param_value)

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

    def get_parameter(self, param_name, default=...):
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
            if default is ...:
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
        if isinstance(db_config, SQLAlchemyDatabase):
            database_obj = DatabaseMetadata(
                bind=db_config.get_engine(),
            )
        else:
            raise ValueError(
                "get_database_metadata expects SQLAlchemyDatabase config. "
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
    ) -> 'bi_etl.utility.run_sql_script.RunSQLScript':
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
            self.log.info(f'Setting sqlalchemy.engine to {mode}')
            logging.getLogger('sqlalchemy.engine').setLevel(mode)
            logging.getLogger('sqlalchemy.engine.base.Engine').setLevel(mode)

    def __thread_init(self):
        """
        Base class preload initialization.  Runs on the execution server.
        Override init instead of this.
        """
        if self.log_file_name is None:
            self.log_file_name = self.name
        self.config.logging.setup_logging()
        self.log_handler = self.config.logging.add_log_file_handler(log_file_prefix=self.log_file_name)

        self.log_logging_level()

    def init(self):
        """
        preload initialization.  Runs on the execution server. Override to add setup tasks.

        Note: init method is useful in cases were you wish to define a common base class
        with a single load method. Each inheriting class can then do its own stuff in init
        With init you can have the flow of execution be:

        1) spec_class.init (if any code before super call)
        2) base_class.init
        3) spec_class.init (after super call, where your code should really go)
        4) base_class.load

        Note 2: Sometimes the functionality above can be achieved with `__init__`.  However, when
        the scheduler thread creates an ETLTask, it creates an instance and thus runs __init__.
        Therefore, you will want `__init__` to be as simple as possible.  On the other hand, `init`
        is run only by the task execution thread. So it can safely do more time-consuming work.
        Again though this method is for when class inheritance is used, and that logic can not go
        into the `load` method.

        Why does the scheduler create an instance?
        It does that in case a task needs a full instance and possibly parameter values in order
        to answer some of the methods like `depends_on` or `mutually_exclusive_execution`.
        """
        pass

    def load(self, **kwargs):
        """
        Placeholder for load. This is where the main body of the ETLTask's work should be performed.
        """
        raise AttributeError(f"{self} load not implemented")

    def finish(self):
        """
        Placeholder for post-load cleanup. This might be useful for cleaning up what was done in ``init``.
        """
        pass

    def run(self,
            suppress_notifications=None,
            handle_exceptions=True,
            **kwargs
            ):
        """
        Should not generally be overridden.
        This is called to run the task's code in the init, load, and finish methods.
        """
        self.set_parameters(**kwargs)
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
            # with a single load method. Each inheriting class can then do its own stuff in init
            # With init you can have the flow of execution be:
            #  1) spec_class.init (if any code before super call)
            #  2) base_class.init
            #  3) spec_class.init (after super call, where your code should really go)
            #  3) base_class.load

            self.init_timer.start()
            self.init()
            self.init_timer.stop()

            self.load_timer.start()

            # Check for parameters to pass to the load function
            load_sig = signature(self.load)
            load_params = load_sig.parameters
            load_kwargs = dict()
            valid_parameter_names = set(self.parameter_names())
            for param in load_params.values():
                if param.kind in {param.POSITIONAL_ONLY, param.VAR_POSITIONAL}:
                    raise ValueError(f"bi_etl.ETLTask only supports keyword parameters.")
                else:
                    if param.name in valid_parameter_names:
                        load_kwargs[param.name] = self.get_parameter(param.name)
                    else:
                        if param.default == param.empty:
                            raise ValueError(f"{self} needs parameter {param.name}. Load takes {load_sig}")

            self.load(**load_kwargs)
            self.load_timer.stop()

            # finish would be the place to clean-up anything done in the init method
            self.finish_timer.start()
            self.finish()
            self.finish_timer.stop()

            self.log.info(f"{self} done.")
            self.status = Status.succeeded
            stats = self.statistics
            stats_formatted = Statistics.format_statistics(stats)
            self.log.info(f"{self} statistics=\n{stats_formatted}")

            # for entry, value in Statistics.flatten_statistics(stats).items():
            #     self.log.info(f"{self}.{entry} = {value}")

            self.close(error=False)
        except Exception as e:  # pylint: disable=broad-except
            self.close(error=True)
            self.exception = e
            self.status = Status.failed
            if not handle_exceptions:
                raise e
            self.log.exception(e)
            if not self.suppress_notifications:
                environment = self.config.bi_etl.environment_name
                message_list = list()
                message_list.append(repr(e))
                message_list.append(f"Task ID = {self.task_id}")
                if self.config.bi_etl.scheduler is not None:
                    ui_url = self.config.bi_etl.scheduler.base_ui_url
                    if ui_url and self.task_id:
                        message_list.append(f"Run details are here: {ui_url}{self.task_id}")
                message_content = '\n'.join(message_list)
                subject = f"{environment} {self} load failed"

                self.notify(self.config.notifiers.failures, subject=subject, message=message_content,)

            self.log.info(f"{self} FAILED.")
        finally:
            self.config.logging.remove_log_handler(self.log_handler)

        self.log.info(f"Status = {repr(self.status)}")

        return self.status == Status.succeeded

    def _build_notifier(self, channel_config: ConfigHierarchy) -> NotifierBase:
        config_channel_name = channel_config.full_item_name()
        notifier_class_str = 'unset'
        try:
            if channel_config == 'LogNotifier':
                notifier_class_str = channel_config
            else:
                notifier_class_str = channel_config.notifier_class

            if isinstance(channel_config, notifiers_config.LogNotifierConfig):
                notifier_instance = LogNotifier(name=config_channel_name)
            elif isinstance(channel_config, notifiers_config.SMTP_Notifier):
                notifier_instance = Email(channel_config, name=config_channel_name)
            elif isinstance(channel_config, notifiers_config.SlackNotifier):
                notifier_instance = Slack(channel_config, name=config_channel_name)
            elif isinstance(channel_config, notifiers_config.JiraNotifier):
                notifier_instance = Jira(channel_config, name=config_channel_name)
            else:
                module, class_name = channel_config.notifier_class.rsplit('.', 1)
                mod_object = importlib.import_module(module)
                class_object = getattr(mod_object, class_name)
                notifier_instance = class_object(channel_config, name=config_channel_name)

            if notifier_instance is not None:
                return notifier_instance
        except Exception as e:
            self.log.exception(e)
            if self.config.notifiers.failed_notifications is not None:
                try:
                    fallback_message = f'Notification to {channel_config} {notifier_class_str} failed with error={e}'
                    fallback_notifiers_list = self.get_notifiers(self.config.notifiers.failed_notifications)
                    for fallback_notifier in fallback_notifiers_list:
                        fallback_notifier.send(
                            subject=f"Failed to send to {channel_config}",
                            message=fallback_message,
                        )
                        return fallback_notifier
                except Exception as e:
                    self.log.exception(e)

    def get_notifier(self, channel_config: ConfigHierarchy) -> NotifierBase:
        config_channel_name = channel_config.full_item_name()
        if config_channel_name not in self._notifiers:
            self._notifiers[config_channel_name] = self._build_notifier(channel_config)
        return self._notifiers[config_channel_name]

    def get_notifiers(self, channel_list: List[DynamicallyReferenced], auto_include_log=True) -> List[NotifierBase]:
        notifiers_list = list()

        if auto_include_log:
            notifiers_list.append(self.log_notifier)

        for config_ref in channel_list:
            config_section = config_ref.get_referenced()
            if not isinstance(config_section, notifiers_config.NotifierConfigBase):
                raise ValueError(
                    f"Notifier reference {config_ref} is not to an instance of NotifierConfigBase: "
                    f"found type= {type(config_section)} value= {config_section}"
                )
            else:
                notifiers_list.append(self.get_notifier(config_section))

        return notifiers_list

    def notify(
            self,
            channel_list: List[DynamicallyReferenced],
            subject,
            message=None,
            sensitive_message: str = None,
            attachment=None,
            skip_channels: set = None,
            **kwargs
    ):
        if self.suppress_notifications:
            self.log.info(f"Notification to {channel_list} suppressed for:")
            self.log.info(f"{subject}: {message}")
        else:
            # Note: all exceptions are caught since we don't want notifications to kill the load
            try:
                filtered_channels = list()

                for channel in channel_list:
                    if skip_channels is None or channel.ref not in skip_channels:
                        filtered_channels.append(channel)

                notifiers_list = self.get_notifiers(filtered_channels)
                fallback_notifiers_list = self.get_notifiers(self.config.notifiers.failed_notifications)
                if len(notifiers_list) == 0:
                    notifiers_list.extend(fallback_notifiers_list)
                for notifier in notifiers_list:
                    try:
                        notifier.send(
                            subject=subject,
                            message=message,
                            sensitive_message=sensitive_message,
                            attachment=attachment,
                            **kwargs
                        )
                    except Exception as e:
                        self.log.exception(e)
                        if self.config.notifiers.failed_notifications is not None:
                            fallback_message = f"error={repr(e)} original_subject={subject} original_message={message}"
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

    def notify_status(
            self,
            channel_list: List[DynamicallyReferenced],
            status_message: str,
            skip_channels: set = None,
    ):
        """
        Send a temporary status messages that gets overwritten with the next status message that is sent.

        Parameters
        ----------
        channel_list
        status_message
        skip_channels

        Returns
        -------

        """
        if not self.suppress_notifications:
            # Note: all exceptions are caught since we don't want notifications to kill the load
            try:
                filtered_channels = list()

                for channel in channel_list:
                    if skip_channels is None or channel.ref not in skip_channels:
                        filtered_channels.append(channel)

                notifiers_list = self.get_notifiers(filtered_channels)
                notifiers_errors = dict()
                for notifier in notifiers_list:
                    try:
                        notifier.post_status(
                            status_message=status_message,
                        )
                    except Exception as e:
                        notifiers_errors[notifier.name] = e

                if len(notifiers_errors) >= len(notifiers_list):
                    # All notifiers failed to send status
                    warnings.warn(
                        "notify_status called but no notifiers are capable of status messages."
                        f"Errors = {notifiers_errors}"
                    )

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
                    name = f"{obj}_{i}"
                stats[name] = obj.statistics
            except AttributeError as e:
                self.log.info(f"'{obj}' does not report statistics. Msg={e}")
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
            self._exit_stack.close()
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

    # noinspection PyPep8Naming
    @staticmethod
    def ExitStack():
        """
        Convenience method to build an ExitStack
        """
        return ExitStack()

    def auto_close(self, ctx_mgr: Any) -> Any:
        return self._exit_stack.enter_context(ctx_mgr)

    def get_task_singleton(self):
        inst_name = self.name
        if inst_name in ETLTask._task_repo:
            inst = ETLTask._task_repo[inst_name]
        else:
            ETLTask._task_repo[inst_name] = self
            inst = self
        return inst
