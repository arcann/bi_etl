"""
Created on May 20, 2015

@author: Derek Wood
"""
import copyreg
import fnmatch
import getpass
import importlib
import inspect
import logging
import pickle as pickle
import pkgutil
import socket
import textwrap
import time
import traceback
import types
from datetime import datetime

# noinspection PyUnresolvedReferences
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.functions import func

from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base
from bi_etl.scheduler.models import (ETL_Tasks,
                                     ETL_Task_Params,
                                     ETL_Task_Status_CD,
                                     ETL_Task_Log,
                                     ETL_Task_Stats,
                                     ETL_Scheduler)
from bi_etl.scheduler.task import ETLTask, Status
from bi_etl.timer import Timer
from bi_etl.utility import log_logging_level, dict_to_str


#################
# Register a way of pickling and unpickling class methods
def _pickle_method(method):
    func_name = method.__func__.__name__
    obj = method.__self__
    cls = method.__self__.__class__
    return _unpickle_method, (func_name, obj, cls)


def _unpickle_method(func_name, obj, cls):
    funct = None
    for cls in cls.mro():
        try:
            funct = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
    if funct:
        return funct.__get__(obj, cls)
    else:
        raise RuntimeError('function {} not found'.format(func_name))


copyreg.pickle(types.MethodType, _pickle_method, _unpickle_method)


class SchedulerInterface(object):
    """
    Light scheduler interface that only interacts with the database.
    """
    CLASS_VERSION = 1.0
    CONFIG_SECTION = 'Scheduler'
    scan_etl_classes_performed = False
    SHARED_etl_task_classes = dict()
    SCHEDULER_ETL_JOBS_PACKAGE = 'bi_etl.scheduler.scheduler_etl_jobs'

    def __init__(self,
                 config: BI_ETL_Config_Base,
                 session=None,
                 log=None,
                 scheduler_id=None,
                 allow_create=False
                 ):

        self.config = config
        if log is None:
            self.log = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        else:
            self.log = log
        log_logging_level(self.log)

        self.etl_task_classes = SchedulerInterface.SHARED_etl_task_classes
        base_module_str = self.config.bi_etl.task_finder_base_module
        if base_module_str is None:
            self.base_modules = []
        else:
            if ',' in base_module_str:
                self.base_modules = [s.strip() for s in base_module_str.split(',')]
            else:
                self.base_modules = [base_module_str]
        if SchedulerInterface.SCHEDULER_ETL_JOBS_PACKAGE not in self.base_modules:
            self.base_modules.append(SchedulerInterface.SCHEDULER_ETL_JOBS_PACKAGE)

        ##############
        # Change the schema of the ETL task definition tables
        metadata = ETL_Tasks.__base__.metadata  # @UndefinedVariable pylint: disable=no-member

        if self.config.bi_etl.scheduler is None:
            raise ValueError("Config does not contain bi_etl.scheduler setting")

        # Pickup schema name from config
        schema = self.config.bi_etl.scheduler.db.database_schema
        self.schema = schema
        if self.schema is not None:
            self.log.info("Using etl_tasks tables in schema {}".format(schema))

            # We don't seem to need to change this.  In fact if we added a table dynamically we'd
            # probably want it to initially link in to the other public. tables
            # metadata.schema = 'onr_dw2'

            for tbl_index in metadata.tables:
                tbl = metadata.tables[tbl_index]
                tbl.schema = schema
                tbl.fullname = tbl.fullname.replace('public', schema)

            # Change schema on Sequences
            # pylint: disable=protected-access
            for seq_index in metadata._sequences:
                seq = metadata._sequences[seq_index]
                seq.schema = schema
            #
            # End  Change the schema
            ##############

        if session is None:
            scheduler_db = self.config.bi_etl.scheduler.db
            if scheduler_db is not None:
                self.log.debug("Making new session")
                self.session = scheduler_db.session()
            else:
                self.log.debug("Missing database option in INI file. No session creation possible")
                self.session = None
        else:
            self.log.debug("Using provided session {}".format(repr(session)))
            self.session = session
        del session

        if self.session is None:
            self.scheduler_row = None
            self.log.debug('scheduler_row not retried')
        else:
            if scheduler_id is None:
                scheduler_host_name = self.config.bi_etl.scheduler.host_name
                # Pass null scheduler_host_name to get_scheduler_id_for_host,
                # it looks up in the config or defaults to local host
                self.scheduler_row = self._get_scheduler_row_for_host(
                    qualified_host_name=scheduler_host_name,
                    allow_create=allow_create,
                )
            else:
                self.log.info('Using assigned scheduler ID {}.'.format(scheduler_id))
                self.scheduler_row = self.get_scheduler_row_for_id(scheduler_id)

            if self.scheduler_row is None:
                msg = """
                      Scheduler not found by name (ini Scheduler section : host setting).'
                      Defaulting to scheduler ID 1, if that exists.
                      """
                self.log.warning(textwrap.dedent(msg))
                self.scheduler_row = self.get_scheduler_row_for_id(1)

            self.scheduler_id = self.scheduler_row.scheduler_id
            self.log.info("scheduler_id = {}".format(self.scheduler_id))

    @property
    def ETL_Tasks(self):
        return ETL_Tasks

    @property
    def ETL_Task_Status_CD(self):
        return ETL_Task_Status_CD

    @property
    def ETL_Task_Params(self):
        return ETL_Task_Params

    @property
    def ETL_Task_Log(self):
        return ETL_Task_Log

    @property
    def ETL_Task_Stats(self):
        return ETL_Task_Stats

    @property
    def qualified_host_name(self):
        """
        Gets the qualified host name of the scheduler server.
        """
        return self.scheduler_row.qualified_host_name

    @staticmethod
    def _get_local_qualified_host_name():
        """
        Gets the qualified host name of the current server (not the scheduler server)
        """
        # =======================================================================
        # socket.getfqdn can return different values for each call if the host has multiple aliases.
        # In our case it alternated between values, however it seems like it could be more random than that.
        # So we'll get all aliases pick the lowest value (as a way of trying to be consistent).
        #
        # Note: You can also specify the hostname directly in the config to avoid this.
        # =======================================================================
        try:
            hostname, aliases, ipaddrs = socket.gethostbyaddr(socket.gethostname())
            aliases.append(hostname)

            return min([name for name in aliases if '.' in name])
        except socket.error:
            return socket.gethostname()

    def get_scheduler_row_for_id(self, scheduler_id):
        query = self.session.query(ETL_Scheduler).filter(ETL_Scheduler.scheduler_id == scheduler_id)
        scheduler_row = query.one()
        return scheduler_row

    def _get_scheduler_row_for_host(self, qualified_host_name: str = None, allow_create: bool = False):
        qualified_host_name = (qualified_host_name
                               or
                               self.config.bi_etl.scheduler.qualified_host_name
                               or
                               self._get_local_qualified_host_name()
                               )
        host_name = socket.gethostname() or qualified_host_name
        self.log.debug('get_scheduler_id_for_host: host name is {}'.format(host_name))
        try:
            query = self.session.query(ETL_Scheduler).filter(ETL_Scheduler.qualified_host_name == qualified_host_name)
            scheduler_row = query.one()
            return scheduler_row
        except NoResultFound:
            if allow_create:
                scheduler_row = ETL_Scheduler()
                try:
                    # We make the assumption here that two schedulers won't be initializing for the first
                    # time at the same instant. If they do, they'd get the same ID and one would fail 
                    # on the commit below (PK error)
                    max_row = self.session.query(func.max(ETL_Scheduler.scheduler_id).label("max_id")).one()
                    max_id = max_row.max_id
                except NoResultFound:
                    max_id = 0
                scheduler_row.scheduler_id = (max_id or 0) + 1
                scheduler_row.qualified_host_name = qualified_host_name
                scheduler_row.host_name = host_name
                self.session.add(scheduler_row)
                self.session.commit()
                return scheduler_row
            else:
                return None

    def get_scheduler_id_for_host(self, qualified_host_name=None, allow_create=False):
        scheduler_row = self._get_scheduler_row_for_host(qualified_host_name=qualified_host_name,
                                                         allow_create=allow_create
                                                         )
        if scheduler_row:
            return scheduler_row.scheduler_id
        else:
            return None

    def get_next_task_id(self):
        # We have to query the sequence each time because this code might be running
        # on a different server or thread from others
        next_id = self.session.execute(ETL_Tasks.task_id.default)
        return next_id

    def add_task_by_exact_name(
            self,
            module_name,
            class_name=None,
            display_name=None,
            parent_task_id=None,
            root_task_id=None,
            scheduler_id=None,
            parameters=None,
            submit_by_user_id=None,
            commit=True,
    ):
        """
        Add a task to the scheduler using a module name
        """
        msg = "add_task_by_exact_name module_name={module_name}, class_name={class_name} parent_task_id={parent_task_id} root_task_id={root_task_id}"
        self.log.debug(msg.format(module_name=module_name,
                                  class_name=class_name,
                                  parent_task_id=parent_task_id,
                                  root_task_id=root_task_id,
                                  )
                       )
        task_rec = ETL_Tasks()
        if scheduler_id is None:
            scheduler_id = self.scheduler_id
        task_rec.scheduler_id = scheduler_id
        task_rec.modulename = module_name
        task_rec.classname = class_name
        task_rec.display_name = display_name or module_name
        self.log.debug("--- Getting next task_id")
        task_rec.task_id = task_id = self.get_next_task_id()
        self.log.debug("--- New task_id={}".format(task_id))
        # We don't want self reference parent or root
        if parent_task_id == task_id:
            parent_task_id = None
        if root_task_id == task_id:
            root_task_id = None
        task_rec.parent_task_id = parent_task_id

        parent_task = None
        # Check if we need to fill in the root_task_id by looking up the parent
        if parent_task_id is not None and root_task_id is None:
            parent_task = self.get_task_record(parent_task_id)
            if parent_task is None:
                raise ValueError("--- parent_task_id {} is invalid".format(parent_task_id))
            elif parent_task.root_task_id is not None:
                root_task_id = parent_task.root_task_id
            else:
                root_task_id = parent_task_id
        task_rec.root_task_id = root_task_id

        if submit_by_user_id is not None:
            task_rec.submit_by_user_id = submit_by_user_id
        else:
            if parent_task_id is None:
                task_rec.submit_by_user_id = getpass.getuser()
            else:
                if parent_task is None:
                    parent_task = self.get_task_record(parent_task_id)
                task_rec.submit_by_user_id = parent_task.submit_by_user_id

        task_rec.Status = Status.new
        if parameters is not None:
            self.add_task_paramters(task_rec, parameters, commit=False)
        self.log.debug("--- Adding task to db {}".format(dict_to_str(task_rec)))
        self.session.add(task_rec)
        if commit:
            self.session.commit()
        else:
            self.session.flush()
        return task_id

    def add_task_by_class(
            self,
            etl_task_class_type,
            display_name=None,
            parent_task_id=None,
            root_task_id=None,
            scheduler_id=None,
            parameters=None,
            submit_by_user_id=None,
            commit=True,
    ):
        """
        Add a task to the scheduler using an instance of the task class type.

        Returns
        -------
        task_id: int
        """
        # Test that we got a class type
        if not isinstance(etl_task_class_type, type):
            # Turn name into a class type
            etl_task_class_type = self.find_etl_class_type(etl_task_class_type)
        return self.add_task_by_exact_name(
            module_name=etl_task_class_type.__module__,
            class_name=etl_task_class_type.__name__,
            display_name=display_name,
            parent_task_id=parent_task_id,
            root_task_id=root_task_id,
            scheduler_id=scheduler_id,
            parameters=parameters,
            submit_by_user_id=submit_by_user_id,
            commit=commit,
        )

    def scan_etl_classes(self):
        SchedulerInterface.scan_etl_classes_performed = True
        self.etl_task_classes.clear()
        self.log.debug('scan_etl_classes: base_modules={}'.format(self.base_modules))

        for base_module in self.base_modules:
            base_module_spec = importlib.util.find_spec(base_module)
            self._scan_etl_classes_in_base(base_module_spec)

    def _scan_etl_classes_in_base(self, base_module_spec):
        path = base_module_spec.submodule_search_locations
        prefix = base_module_spec.name + '.'
        self.log.debug('_scan_etl_classes_in_base: scanning path={}'.format(path))
        self.log.debug('_scan_etl_classes_in_base: using prefix={}'.format(prefix))
        for (module_finder, name, ispkg) in pkgutil.walk_packages(path=path,
                                                                  prefix=prefix,
                                                                  onerror=lambda pkg: self.log.debug(
                                                                      'Error importing package {}'.format(pkg))
                                                                  ):
            if not ispkg:
                module = None
                try:
                    self.log.debug('_scan_etl_classes_in_base: Loading module {}'.format(name))
                    module_loader = module_finder.find_spec(name).loader
                    module = module_loader.load_module(name)
                except (Exception, SystemExit) as e:  # pylint: disable=broad-except
                    self.log.debug('_scan_etl_classes_in_base: Skipping {} due to {}'.format(name, e))
                if module is not None:
                    try:
                        self.log.debug('_scan_etl_classes_in_base: Checking for matching class(es) in {}'.format(name))
                        task_class_dict = self._find_etl_classes_in_module(module)
                        if task_class_dict is not None:
                            self.etl_task_classes.update(task_class_dict)
                    except ValueError as e:
                        self.log.debug('_scan_etl_classes_in_base: Skipping {} due to {}'.format(name, e))

    def _find_etl_classes_in_module(self, module):
        """
        Returns a dictionary of the ETLTask instances defined in a given module
        """
        class_matches_by_type = dict()

        # Look for ETLTask inherited classes
        for _, classObj in inspect.getmembers(module, inspect.isclass):
            # Check that the class is defined in our module and not imported
            if classObj.__module__ == module.__name__:
                baseclasses = inspect.getmro(classObj)
                if ETLTask in baseclasses and str(classObj) != str(ETLTask):
                    inst = classObj()
                    qualified_name = inst.name
                    self.log.info('_find_etl_classes_in_module found {}'.format(qualified_name))
                    class_matches_by_type[qualified_name] = classObj

        return class_matches_by_type

    def _find_etl_class_in_module(self, module, class_name=None):
        class_matches_by_type = self._find_etl_classes_in_module(module)
        task_class = None
        if len(class_matches_by_type) == 1:
            name, task_class = class_matches_by_type.popitem()
            self.log.debug("_find_etl_class_in_module found 1 ETLTask matching class {}".format(name))
        else:
            if class_name is None:
                class_name = module.__name__.split('.')[-1]
            self.log.debug("_find_etl_class_in_module found ETLTask classes {}".format(class_matches_by_type))
            for name in class_matches_by_type:
                if name.lower() == class_name.lower():
                    task_class = class_matches_by_type[name]
                    self.log.debug("_find_etl_class_in_module found class by name {}={}".format(task_class, class_name))
        if task_class is None:
            msg = "Module {} doesn't contain a single ETLTask class, could not choose class from {}".format(module,
                                                                                                            class_matches_by_type)
            self.log.debug(msg)
            raise ValueError(msg)
        return task_class

    def _get_class_from_qualified_name(self, qualified_name):
        parts = qualified_name.split('.')
        module_part = '.'.join(parts[:-1])
        class_part = parts[-1:][0]
        module = importlib.import_module(module_part)
        etl_class = self._find_etl_class_in_module(module, class_part)
        return etl_class

    def find_etl_classes(self, partial_module_name):
        if not SchedulerInterface.scan_etl_classes_performed:
            # Since we don't have a class database, try and quickly import the module assuming it's fully qualified
            # TODO: Once classes and dependency hierarchy is stored in the database, scan that instead.
            try:
                # We try to get the class simply to verify it exists
                _ = self._get_class_from_qualified_name(partial_module_name)
                return [partial_module_name]  # Caller wants the qualified name not the instance
            except (ImportError, ValueError):
                pass
            self.scan_etl_classes()

        if not isinstance(partial_module_name, str):
            partial_module_name = str(partial_module_name)

        matches = list()
        for etl_class in self.etl_task_classes:
            if (fnmatch.fnmatch(etl_class, partial_module_name)
                    or fnmatch.fnmatch(etl_class, '*.' + partial_module_name + '.*')
                    or fnmatch.fnmatch(etl_class, '*.' + partial_module_name)
                    or fnmatch.fnmatch(etl_class, partial_module_name + '.*')
            ):
                matches.append(etl_class)
        return matches

    def find_etl_class_name(self, partial_module_name):
        matches = self.find_etl_classes(partial_module_name)
        if len(matches) == 1:
            return matches[0]
        else:
            raise ValueError(
                'partial_module_name {} matched {} and not a single record'.format(partial_module_name, matches))

    def get_etl_class_instance(self, qualified_name):
        if not SchedulerInterface.scan_etl_classes_performed:
            # Since we don't have a class database, try and quickly import the module assuming it's fully qualified
            etl_class = self._get_class_from_qualified_name(qualified_name)
            return etl_class
        return self.etl_task_classes[qualified_name]

    def find_etl_class_instance(self, partial_module_name):
        class_name = self.find_etl_class_name(partial_module_name)
        return self.get_etl_class_instance(class_name)

    def find_etl_class_type(self, partial_module_name):
        class_name = self.find_etl_class_name(partial_module_name)
        return self.get_etl_class_instance(class_name).__class__

    def add_task_by_partial_name(self,
                                 partial_module_name,
                                 display_name=None,
                                 parent_task_id=None,
                                 root_task_id=None,
                                 scheduler_id=None,
                                 parameters=None,
                                 submit_by_user_id=None,
                                 commit=True,
                                 ):
        """
        Add a task to the scheduler using the module_name (partial) and optionally class_name

        Returns
        -------
        task_id: int
        """
        etl_task_class_name = self.find_etl_class_name(partial_module_name)
        return self.add_task_by_exact_name(etl_task_class_name,
                                           display_name=display_name,
                                           parent_task_id=parent_task_id,
                                           root_task_id=root_task_id,
                                           scheduler_id=scheduler_id,
                                           parameters=parameters,
                                           submit_by_user_id=submit_by_user_id,
                                           commit=commit,
                                           )

    def get_task_record(self, task_id):
        # Make sure task_id is an integer
        task_id = int(task_id)
        return self.session.query(ETL_Tasks).get(task_id)

    def get_task_status(self, task_id):
        """
        Gets the Status of a task

        Returns
        -------
        status_of_task: bi_etl.scheduler.status.Status
        """
        return self.get_task_record(task_id).Status

    def wait_for_task(self, task_id, check_interval=1, max_wait=None):
        """
        Waits for a task to finish.

        Parameters
        ----------
        task_id: int
            The task_id to wait for

        check_interval: float
            How many seconds to wait between checks.
            The argument may be a floating point number for subsecond precision.
            
        max_wait: float
            The maximum seconds to wait for the job to finish.  If None or 0, will wait indefinitely.

        Returns
        -------
        status_of_task: bi_etl.scheduler.status.Status
        """
        timer = Timer()
        while not self.get_task_status(task_id).is_finished():
            if max_wait:
                if timer.seconds_elapsed > max_wait:
                    raise TimeoutError(
                        'wait_for_task wait time {} exceeded max_wait {}'.format(timer.seconds_elapsed, max_wait))
            time.sleep(check_interval)
        return self.get_task_status(task_id)

    def add_task_paramter(self, task, parameter_name, parameter_value, commit=True):
        if isinstance(task, int):
            task_rec = self.get_task_record(task)
        elif isinstance(task, ETL_Tasks):
            task_rec = task
        else:
            raise ValueError("add_task_paramter task parameter must be int or ETL_Tasks")
        task_rec.parameters.append(ETL_Task_Params(parameter_name, pickle.dumps(parameter_value)))
        if commit:
            self.session.commit()

    def add_task_paramters(self, task, parameters, commit=True):
        if isinstance(task, int):
            task_rec = self.get_task_record(task)
        elif isinstance(task, ETL_Tasks):
            task_rec = task
        else:
            raise ValueError("add_task_paramters task parameter must be int or ETL_Tasks")
        if isinstance(parameters, list):
            for parameter_name, parameter_value in parameters:
                self.add_task_paramter(task_rec, parameter_name, parameter_value, commit=commit)
        else:  # assume it's a dict
            for parameter_name in parameters:
                parameter_value = parameters[parameter_name]
                self.add_task_paramter(task_rec, parameter_name, parameter_value, commit=commit)
        if commit:
            self.session.commit()

    def get_task_parameter_dict(self, task) -> dict:
        """

        Parameters
        ----------
        task: int or ETL_Tasks

        Returns
        -------
        dict
        """
        if isinstance(task, int):
            task_id = task
            task_rec = self.get_task_record(task_id)
        elif isinstance(task, ETL_Tasks):
            task_rec = task
            task_id = task_rec.task_id
            assert task_id is not None, "get_task_parameter_dict called for task with no task_id {}".format(task_rec)
        else:
            raise ValueError('Unexpected type for task parameter {}'.format(type(task)))
        self.log.debug("Getting parameters for task id {}".format(task_id))
        params_dict = dict()
        for param_rec in task_rec.parameters:
            try:
                param_value = pickle.loads(param_rec.param_value)
                params_dict[param_rec.param_name] = param_value
            except pickle.UnpicklingError:
                traceback.print_exc()
                if len(param_rec.param_value) > 200:
                    msg = "ETL Task {} unable to unpickle {} value (too long to print. len={})"
                    msg = msg.format(repr(task_id),
                                     param_rec.param_name,
                                     len(param_rec.param_value)
                                     )
                    self.log.error(msg)
                else:
                    msg = "ETL Task {} unable to unpickle {} value '{}'"
                    msg = msg.format(repr(task_id),
                                     param_rec.param_name,
                                     param_rec.param_value
                                     )
                    self.log.error(msg)
                raise
        return params_dict

    def load_parameters(self, etl_task):
        """
        This is done in the etl_task thread/process (called by run method)
        so that the parameters don't have to be loaded into the scheduler thread or passed between threads/processes.
        """
        params_dict = self.get_task_parameter_dict(etl_task.task_id)
        for param_name in params_dict:
            etl_task.set_parameter(param_name, params_dict[param_name], local_only=True)

    def get_jobs_by_root_id(self, root_task_id):
        query = self.session.query(ETL_Tasks).filter(ETL_Tasks.root_task_id == root_task_id)
        return query

    def get_status_code_list(self):
        return self.session.query(ETL_Task_Status_CD).all()

    def get_heartbeat_time(self):
        if self.scheduler_row is not None:
            return self.scheduler_row.last_heartbeat
        else:
            return None

    def get_heartbeat_age_timedelta(self):
        last_heartbeat = self.get_heartbeat_time()
        if last_heartbeat is None:
            return None
        else:
            return (datetime.now() - last_heartbeat)

    def heatbeat_now(self):
        self.scheduler_row.last_heartbeat = datetime.now()
        self.session.flush()

    def __reduce__(self):
        return (SchedulerInterface, ())
