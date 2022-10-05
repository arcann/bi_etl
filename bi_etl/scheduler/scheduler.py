"""
Created on Apr 14, 2015

@author: Derek Wood
"""
import codecs
import multiprocessing
import textwrap
import time
import traceback
import warnings
from datetime import datetime, timedelta
from queue import Empty

from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm.exc import DetachedInstanceError

import bi_etl.scheduler
import bi_etl.scheduler.dependent_reasons as dependent_reasons
from bi_etl.conversions import replace_tilda
from bi_etl.scheduler.exceptions import CircularDependency
from bi_etl.scheduler.exceptions import DependencyDeeperThanLimit
from bi_etl.scheduler.messages import ChildSetDisplayName
from bi_etl.scheduler.messages import (ChildStatusUpdate,
                                       ChildRunRequested,
                                       ChildRunOK,
                                       ChildNotOccupyingCPU,
                                       ChildOccupyingCPU,
                                       SummaryMessage
                                       )
from bi_etl.scheduler.models import (ETL_Tasks,
                                     ETL_Task_Log,
                                     ETL_Task_Stats,
                                     ETL_Task_Dependency
                                     )
from bi_etl.scheduler.scheduler_etl_jobs.etl_task_status_cd import ETL_Task_Status_CD
from bi_etl.scheduler.scheduler_interface import SchedulerInterface
from bi_etl.scheduler.task import Status, TaskStopRequested, ETLTask
from bi_etl.statistics import Statistics
from bi_etl.utility import dict_to_pairs


#pylint: disable=too-many-instance-attributes, too-many-public-methods, too-many-nested-blocks 
#pylint: disable=too-many-statements, too-many-branches, too-many-arguments, too-many-locals
#pylint: disable=invalid-name

# Ignore long lines for now
#pylint: disable=line-too-long

class Scheduler(SchedulerInterface):
    """
    Full-scheduler object with memory of active jobs.
    """

    MAX_DEPENDENTS_DEPTH = 100

    def __init__(self):
        super(Scheduler, self).__init__(log_name='Scheduler', allow_create= True)
        
        # Register the replace_tilda method of handling unicode errors 
        codecs.register_error('replace_tilda', replace_tilda)
        
        # Use the spawn method to get a clean python instance for each ETL Job
        multiprocessing.set_start_method('spawn')  # @UndefinedVariable
        self.trace = self.config.getboolean('Scheduler', 'trace', fallback=False)

        self.log.info("Init full Scheduler instance")

        # TODO: Setup to monitor config file and reload if it changes

        # Only used by the full scheduler so we import here
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import psutil
        self.psutil = psutil

        self.etl_task_by_id = dict()
        self.etl_task_by_name = dict()
        maximum_concurrent_tasks = self.config.getint_('Scheduler',
                                                       'maximum_concurrent_tasks',
                                                       fallback=None
                                                       )
        if maximum_concurrent_tasks is None:
            try:
                self.maximum_concurrent_tasks = multiprocessing.cpu_count()  # @UndefinedVariable
                msg = """
                      Setting maximum_concurrent_tasks to CPU count of {}.
                      Provide Scheduler.maximum_concurrent_tasks in config if something else is desired.
                      """
                msg = textwrap.dedent(msg)
                self.log.warning(msg.format(self.maximum_concurrent_tasks))
            except NotImplementedError as e:
                self.log.warning(e)
                self.maximum_concurrent_tasks = 1
                msg = """
                      Defaulting to {} concurrent tasks. 
                      Provide maximum_concurrent_tasks in config if something else is desired.
                      """
                msg = textwrap.dedent(msg)
                msg = msg.format(self.maximum_concurrent_tasks)
                self.log.warning(msg)
        else:
            self.maximum_concurrent_tasks = maximum_concurrent_tasks
        self.log.info("maximum_concurrent_tasks = {}".format(maximum_concurrent_tasks))
        self.tasks_occupying_cpu = set()
        self.log_flush_interval = 10
        self.process_check_interval = self.config.getint('Scheduler', 'process_check_interval', fallback=5)
        self.seconds_to_keep_finished_tasks = 60
        self.days_to_keep_run_logs = 30
        self.days_to_keep_large_parameters = 7
        self.min_large_parameter_size = 1024  # Parameters over 1 KB are considered large
        self.last_table_maintenance_run = None
        self.log.debug("Finished Init full Scheduler instance")
        self._new_tasks_query = None

        heartbeat_age_timedelta = self.get_heartbeat_age_timedelta()
        if (heartbeat_age_timedelta is not None 
            and heartbeat_age_timedelta < timedelta(seconds= self.process_check_interval * 2)
            ):
            raise RuntimeError('Another scheduler appears to be active!')

    def _create_etl_task_object_from_task_rec(self, task_rec):
        task_id = task_rec.task_id
        if not isinstance(task_id, int):
            task_id = int(task_id)
        parent_task_id = task_rec.parent_task_id
        root_task_id = task_rec.root_task_id
        parent_task = None
        if parent_task_id is not None:
            parent_task = self.get_task_by_id(task_rec.parent_task_id)
            if parent_task is None:
                self.log.warning("Task {} {} started with parent id {} that is not known".format(task_id, task_rec.modulename, parent_task_id))
            else:
                # Check parent status
                if parent_task.status == Status.succeeded:
                    self.add_log_message(parent_task, 'Child started status changing to ancestors_running')
                    self.set_task_status(parent_task, Status.ancestors_running)
                elif parent_task.status.is_terminated() or parent_task.status.is_termination_pending():
                    task_rec.Status = Status.stop_requested
                elif parent_task.status == Status.failed:
                    #pylint: disable= redefined-variable-type
                    task_rec.Status = Status.stopped

                if root_task_id != parent_task_id and root_task_id != parent_task.root_task_id:
                    self.log.warning("Creating task {task_id} listed as has having parent_task_id={parent_task_id} "
                                     "which has root_task_id={root_task_id}...".format(
                                        task_id = task_id,
                                        parent_task_id = parent_task_id,
                                        root_task_id = parent_task.root_task_id,
                                        )
                                     )
                    self.log.warning("...however, parent database record has root_task_id={}".format(root_task_id))
                    self.log.warning("...correcting the task database row")
                    task_rec.root_task_id = parent_task.root_task_id
                    root_task_id = parent_task.root_task_id
        if root_task_id is not None:
            root_task = self.get_task_by_id(root_task_id)
            if parent_task is None:
                parent_task = root_task
            if root_task is None:
                self.log.warning("Task {} {} started with root id {} that is not known".format(task_id, task_rec.modulename, root_task_id))
            else:
                if root_task.task_rec.Status.is_finished():
                    self.set_task_status(root_task, Status.ancestors_running)
        try:
            # Support finding the instance using either module alone (which could include an embedded classname) or module + classname
            if task_rec.classname:                
                instance_name = task_rec.modulename + '.' + task_rec.classname
            else:
                instance_name = task_rec.modulename
            
            ETLTask_Class = self.find_etl_class_instance(partial_module_name= instance_name)
        except ValueError as e:
            self.log.exception(e)
            self._write_log_message(task_rec.task_id, repr(e))
            task_rec.summary_message = repr(e)
            task_rec.Status = Status.failed
            self.session.commit()
            return None
        
        try:
            etl_task = ETLTask_Class(task_id= task_id,
                                     parent_task_id=parent_task_id,
                                     root_task_id=root_task_id,
                                     scheduler= self,
                                     task_rec = task_rec,
                                     config= self.config,
                                     )
        # Scheduler doesn't die no matter what!
        except Exception as e:  # pylint: disable=broad-except
            self.log.exception(e)
            self._write_log_message(task_rec.task_id, repr(e))
            task_rec.summary_message = repr(e)
            task_rec.Status = Status.failed
            self.session.commit()
            return None
        
        self.log.debug("Task {} object created in memory".format(repr(etl_task)))
        # Make extra sure ETLTask stored the task_ids properly
        assert etl_task.task_id == task_id
        assert etl_task.parent_task_id == parent_task_id
        assert etl_task.root_task_id == root_task_id

        return etl_task

    def get_task_by_id(self, etl_task_id):
        if not isinstance(etl_task_id, int):
            etl_task_id = int(etl_task_id)
        # Check active tasks in memory
        if etl_task_id in self.etl_task_by_id:
            return self.etl_task_by_id[etl_task_id]
        else:
            # Otherwise try to get it from the database
            task_rec = self.get_task_record(etl_task_id)
            return self._create_etl_task_object_from_task_rec(task_rec)

    def get_etl_tasks_by_name(self, etl_task_name):
        if etl_task_name in self.etl_task_by_name:
            return self.etl_task_by_name[etl_task_name]
        else:
            return []

    def add_task_to_active(self, etl_task):
        assert isinstance(etl_task, ETLTask)
        if not isinstance(etl_task.task_id, int):
            etl_task.task_id = int(etl_task.task_id)
        self.etl_task_by_id[etl_task.task_id] = etl_task
        task_name = etl_task.name
        if task_name not in self.etl_task_by_name:
            self.etl_task_by_name[task_name] = dict()
        self.etl_task_by_name[task_name][etl_task.task_id] = etl_task

    def remove_active_task_record(self, etl_task):
        # Last chance to flush message queue
        self.flush_log_messages(etl_task)
        try:
            etl_task_name = etl_task.name

            if not hasattr(etl_task, 'thread_running'):
                # Stopped before it was started
                pass
            elif etl_task.thread_running:
                self.log.warning("remove_active_task_record called with Task {} but has thread_running = True".format(repr(etl_task)))
            else:
                self.log.debug("Removing completed task {} from active tasks".format(etl_task))
                self.session.flush()
                try:

                    self.session.expunge(etl_task.task_rec)
                except AttributeError:
                    pass
                except InvalidRequestError:
                    pass
                del self.etl_task_by_id[etl_task.task_id]
                del self.etl_task_by_name[etl_task_name][etl_task.task_id]
                # Remove children
                for child_task in etl_task.children:
                    self.remove_active_task_record(child_task)
        except KeyError:
            self.log.error(traceback.format_exc())
            self.log.error("ETL Task {} was not in etl_task_by_name".format(repr(etl_task)))

    def set_task_status(self, etl_task, new_status):
        self.log.debug("set_task_status task_id={} new_status={}".format(etl_task.task_id, new_status))
        self.add_log_message(etl_task, "set_task_status new_status={}".format(new_status))

        # Set status on both the object and the task_rec
        # TODO: Clean that up
        etl_task.status = new_status

        if new_status.is_finished():
            etl_task.task_rec.finished_date = datetime.now()
        #self.log.debug("Task row = {}".format(dict_to_str(etl_task.task_rec)))
        self.session.flush()
        self.session.commit()
        # Check if parent wants child status updates
        if etl_task.parent_task is not None:
            if etl_task.parent_task.needs_to_get_child_statuses():
                self.send_task_message(etl_task.parent_task, ChildStatusUpdate(etl_task.task_id, new_status))
        # Check if root wants ancestor status updates
        if etl_task.root_task is not None and etl_task.root_task != etl_task.parent_task:
            if etl_task.root_task.needs_to_get_ancestor_statuses():
                self.send_task_message(etl_task.root_task, ChildStatusUpdate(etl_task.task_id, new_status))

    def send_task_message(self, etl_task, message):
        try:
            etl_task.parent_to_child.put(message)
        except AttributeError:
            self.log.warning("send_task_message called on task {} with no parent_to_child".format(etl_task))

    def set_task_summary_message(self, etl_task, summary_message, commit = False, from_client= False):
        """
        set the tasks summary message.
        Note: Since this is often called on conjunction with set_task_status, we default to no commit here.
        """
        self.add_log_message(etl_task, msg = summary_message, allow_duplicates= False)
        self.log.debug("set_task_summary_message task={} message={}".format(etl_task, summary_message))
        if etl_task.summary_message_from_client and not from_client:
            self.log.debug("Not storing summary message because it would override a client message")
        else:
            etl_task.task_rec.summary_message = str(summary_message)[:4000]
            if commit:
                self.session.commit()

    def append_task_summary_message(self, etl_task, summary_message, commit = True):
        """
        Append to the tasks summary message.
        """
        self.set_task_summary_message(etl_task, etl_task.task_rec.summary_message + ' ' + summary_message)
        if commit:
            self.session.commit()

    def check_for_cpu(self, etl_task):
        """
        Checks for available CPU, if available it STARTS THE TASK and returns True.
        If not it returns False
        """
        if len(self.tasks_occupying_cpu) < self.maximum_concurrent_tasks:
            self.run_task(etl_task)
            return True
        else:
            return False

    @staticmethod
    def _depth_first_dependent_search(start, target, limit, current_depth=0, call_tree=None):
        if current_depth >= limit:
            raise DependencyDeeperThanLimit(limit, call_tree)

        # Make sure we are dealing with the ETL_Tasks task record from the model and not the ETL_Task object
        if isinstance(start, ETLTask):
            start = start.task_rec

        if isinstance(target, ETLTask):
            target = target.task_rec

        if call_tree is None:
            call_tree = list()
        call_tree.append(start)

        if start.task_id == target.task_id:
            return call_tree

        for u in start.dependencies:
            #if u.dependent_reason == dependent_reasons.Predecessor:
            # TODO: Track the u.dependent_reason in the call_tree
            if Scheduler._depth_first_dependent_search(u.dependent_on_task, target, limit, current_depth+1, call_tree):
                return call_tree

        # Remove ourselves from the master call tree
        call_tree.remove(start)
        return None

    def add_dependency(self, etl_task, dependent_task, dependent_reason):
        done = False
        assert isinstance(etl_task, ETLTask), 'add_dependency: etl_task is not an ETLTask but is a {}'.format(type(etl_task))
        assert isinstance(dependent_task, ETLTask), 'add_dependency: dependent_task is not an ETLTask but is a {}'.format(type(dependent_task))
        if dependent_task.task_id == ETLTask.task_id:
            self.add_log_message(etl_task, 'Not recording dependency on {} since that is this task'.format(repr(dependent_task)))
            return
        # Don't depend on cross root tasks that are already dependent on something in our root
        if dependent_task.task_rec.root_task_id != etl_task.task_rec.root_task_id:
            for dep_dep_record in dependent_task.task_rec.dependencies:
                dep_dep_task_rec = dep_dep_record.dependent_on_task
                if dep_dep_task_rec.root_task_id == etl_task.task_rec.root_task_id:
                    self.add_log_message(etl_task, 'Not recording dependency on {} since it is waiting on our root'.format(repr(dependent_task)))
                    done = True

        if not done:
            for exist_dep in etl_task.task_rec.dependencies:
                if exist_dep.dependent_on_task_id == dependent_task.task_id:
                    if exist_dep.current_blocking_flag == 'N':
                        self.add_log_message(etl_task, 'Re-blocking dependency on {}'.format(repr(dependent_task)))
                        exist_dep.current_blocking_flag = 'Y'
                    else:
                        self.add_log_message(etl_task, 'Already dependent on {} blocking_flag = {}'.format(repr(dependent_task), exist_dep.current_blocking_flag))
                    done = True

        if not done:
            # Make sure dependent_task isn't also directly or indirectly dependent on etl_task
            loop = Scheduler._depth_first_dependent_search(start= dependent_task.task_rec,
                                                           target= etl_task.task_rec,
                                                           limit= Scheduler.MAX_DEPENDENTS_DEPTH
                                                           )
            if loop is not None:
                raise CircularDependency(loop)
            else:
                self.add_log_message(etl_task, 'Adding dependency on {}'.format(repr(dependent_task)))
                dep = ETL_Task_Dependency(etl_task.task_rec, dependent_task.task_rec, str(dependent_reason))
                self.session.add(dep)

    def check_dependencies(self, etl_task):
        #pylint: disable=protected-access
        
        assert isinstance(etl_task, ETLTask), "check_dependencies needs an ETLTask got a {}".format(type(etl_task))
        
        if not etl_task._logged_dependencies:
            self.add_log_message(etl_task, 'depends_on = {}'.format(etl_task.depends_on()))
            self.add_log_message(etl_task, 'normalized_dependents_set = {}'.format(etl_task.normalized_dependents_set))
            self.add_log_message(etl_task, 'mutually_exclusive_with_set = {}'.format(etl_task.mutually_exclusive_with_set))
            etl_task._logged_dependencies = True

        dependencies_met = True

        # Scan existing dependencies to check if they are still relevant
        for dep in etl_task.task_rec.dependencies:
            if dep.current_blocking_flag == 'Y':
                dep_task = self.get_task_by_id(dep.dependent_on_task_id)
                dependent_reason_class = dependent_reasons.getFromString(dep.dependent_reason)
                if dependent_reason_class is None:
                    self.add_log_message(
                        etl_task,
                        f"Unable to process dependent_reason {dep}. "
                        f"Assuming it will get re-added. dep_task= {repr(dep_task)}"
                    )
                    dep.current_blocking_flag = 'N'
                elif dependent_reason_class.release_wait_on_status(dep_task.status):
                    self.add_log_message(etl_task, 'No longer blocked by {}'.format(repr(dep_task)))
                    dep.current_blocking_flag = 'N'
                else:
                    if self.trace:
                        self.log.debug(f"{repr(etl_task)} still blocked by {dep} {repr(dep_task)}")
                    dependencies_met = False
            elif dep.current_blocking_flag != 'N':
                self.log.warning(f'{dep} current_blocking_flag has unexpected value of {dep.current_blocking_flag}')

        # Check for new dependencies

        # Check jobs that we depend on to make sure they are not actively running or failed
        # For example given jobs A-> B -> C
        # If A is running then B should not start
        # If A failed, then B should fail
        for dep_name in etl_task.normalized_dependents_set:
            # Check if that task name is active (running, or waiting)
            dep_obj_dict = self.get_etl_tasks_by_name(dep_name)
            if dep_obj_dict is not None and len(dep_obj_dict) > 0:
                # Scan the entire list as dependent objects
                for dep_task_id in dep_obj_dict:
                    dep_task = dep_obj_dict[dep_task_id]
                    assert isinstance(dep_task, ETLTask)

                    if dependent_reasons.Predecessor.wait_on_status(dep_task.task_rec.Status):
                        try:
                            self.add_dependency(etl_task, dep_task, dependent_reasons.Predecessor)
                            self.log.debug("Task {etl_task} has to wait because dependent "
                                           "job {dep} has not is_finished yet.".format(
                                                etl_task= repr(etl_task),
                                                dep=repr(dep_task)
                            ))
                            dependencies_met = False
                        except CircularDependency as error:
                            # Somehow that task is waiting for us, so we'll skip waiting on it
                            self.add_log_message(etl_task, 'Did not add dependency on {} due to {}'.format(
                                repr(dep_task),
                                error
                            ))
                    else:  # Failed
                        if etl_task.root_task_id is not None and dep_task.root_task_id == etl_task.root_task_id:
                            # If our predecessor within the same root failed, cancel this job
                            if dep_task.status.value < 0 or dep_task.status.is_termination_pending():
                                msg = "Predecessor {} failed with status {}".format(
                                    repr(dep_task),
                                    repr(dep_task.status)
                                )
                                self.log.debug("Task {etl_task} {msg}".format(etl_task=repr(etl_task), msg=msg))
                                self.add_log_message(etl_task, msg + "\n", allow_duplicates=False)
                                self.set_task_summary_message(etl_task, "Predecessor {} failed".format(
                                    dep_task.task_id
                                ))
                                self.set_task_status(etl_task, Status.cancelled)
                                return
                        else:
                            # Different root task instance failed (any tasks with root of None are considered different)
                            pass
            else:
                self.add_log_message(etl_task, "Predecessor {} is not registered with scheduler".format(dep_name))

        # Check to see if another instance of this task is running
        # Check if that task name is active (running, or waiting)
        # TODO: Have a way that tasks can indicate if it's OK for another instance to run at the same time.
        if dependencies_met:
            for exclusive_etl_task in etl_task.mutually_exclusive_with_set:
                exclusive_etl_task_obj_dict = self.get_etl_tasks_by_name(exclusive_etl_task)
                for exclusive_etl_task_instance_task_id in exclusive_etl_task_obj_dict:
                    exclusive_etl_task_instance = exclusive_etl_task_obj_dict[exclusive_etl_task_instance_task_id]
                    if exclusive_etl_task_instance.task_id != etl_task.task_id:
                        # Check if that task also lists us as Mutually exclusive
                        if etl_task.name in exclusive_etl_task_instance.mutually_exclusive_with_set:
                            # If so treat like another instance of self.
                            # We wait only on those before us in line (based on Task ID)
                            if dependent_reasons.OtherSelf.wait_on_status(exclusive_etl_task_instance.status):
                                if etl_task.task_id > exclusive_etl_task_instance.task_id:
                                    try:
                                        msg = "Waiting for other waiting instance {} with status {}".format(
                                            exclusive_etl_task_instance.task_id,
                                            exclusive_etl_task_instance.status
                                        )
                                        self.add_dependency(etl_task,
                                                            exclusive_etl_task_instance,
                                                            dependent_reasons.OtherSelf)
                                        self.add_log_message(etl_task, msg + "\n", allow_duplicates=False)
                                        self.log.debug("Task {etl_task} has to wait because another instance {other}"
                                                       " is also waiting and arrived first.".format(
                                                         etl_task= repr(etl_task),
                                                         other=repr(exclusive_etl_task_instance)
                                        ))
                                        dependencies_met = False
                                    except CircularDependency as error:
                                        # Somehow that task is waiting for us, so we'll skip waiting on it
                                        self.add_log_message(etl_task, 'Did not add dependency on {} due to {}'.format(
                                            repr(exclusive_etl_task_instance), error
                                        ))
                        else:  # Other task isn't directly listing us a Mutually Exclusive (which it probably should)
                            # Do we add ourselves to exclusive_etl_task_instance.mutually_exclusive_with_set ?
                            if dependent_reasons.MutuallyExclusive.wait_on_status(exclusive_etl_task_instance.status):
                                self.log.debug("Task {etl_task} has to wait because an instance of a mutually exclusive"
                                               " task {other} has not is_finished yet.".format(
                                                  etl_task= repr(etl_task),
                                                  other=repr(exclusive_etl_task_instance)
                                ))
                                try:
                                    msg = "Waiting for an instance of a mutually exclusive" \
                                          " task {} (and maybe others)".format(exclusive_etl_task_instance.task_id)
                                    self.add_log_message(etl_task, msg + "\n", allow_duplicates=False)
                                    self.add_dependency(etl_task,
                                                        exclusive_etl_task_instance,
                                                        dependent_reasons.MutuallyExclusive)
                                    dependencies_met = False
                                except CircularDependency as error:
                                    # Somehow that task is waiting for us, so we'll skip waiting on it
                                    self.add_log_message(etl_task,
                                                         'Did not add dependency on {} due to {}'.format(
                                                             repr(exclusive_etl_task_instance),
                                                             error
                                                         ))

        # Check to make sure there are no running jobs that list this job as a dependency
        # That would make this a source of that job and so we don't want to start running until that job finishes
        # For example given jobs A -> B -> C
        # If B is running then A should not start.  If C is running A should be OK to start.
        if dependencies_met:
            for running_etl_task_id in self.etl_task_by_id:
                running_etl_task = self.get_task_by_id(running_etl_task_id)
                if dependent_reasons.Follower.wait_on_status(running_etl_task.status):
                    for dep_name in running_etl_task.normalized_dependents_set:
                        if dep_name == etl_task.name:
                            try:
                                self.add_dependency(etl_task, running_etl_task, dependent_reasons.Follower)
                                dependencies_met = False
                                self.log.debug(
                                    "Task {etl_task} has to wait because following job {flw} is still active.".format(
                                        etl_task= etl_task,
                                        flw=running_etl_task
                                        )
                                    )
                            except CircularDependency as error:
                                self.log.warning(error)
                                self.add_log_message(etl_task,
                                                     'Did not add dependency on {} due to {}'.format(
                                                         repr(running_etl_task),
                                                         error
                                                     ))
        if dependencies_met:
            # check if parent has needs_to_ok_child_runs() == True which sets waiting_for_workflow flag
            if etl_task.waiting_for_workflow:
                if not etl_task.parent_task:
                    self.add_log_message(etl_task, 'waiting_for_workflow: Cannot wait for non-existing parent!')
                    self.set_task_status(etl_task, Status.failed)
                elif not etl_task.parent_task.thread_running:
                    self.add_log_message(etl_task,
                                         'waiting_for_workflow: Parent not running to approve us! (parent={})'.format(
                                             repr(etl_task.parent_task)
                                         ))
                    self.set_task_status(etl_task, Status.failed)
                else:
                    # Send a message requesting etl_tasks run (should have already been sent)
                    self.send_task_message(etl_task.parent_task, message=ChildRunRequested(etl_task.task_id))
                    self.set_task_status(etl_task, Status.waiting_for_workflow)
            else:
                # Check for cpu right away (rather than waiting for the next pass)
                if not self.check_for_cpu(etl_task):
                    # If check_for_cpu didn't start the task, set it to wait for CPU
                    self.set_task_status(etl_task, Status.waiting_for_cpu)
        else:
            if etl_task.status == Status.new:
                self.set_task_status(etl_task, Status.waiting_for_dependencies)
            # This should be non-empty here, but lets check
            if len(etl_task.task_rec.dependencies) > 0:
                waiting_for_list = [str(d) for d in etl_task.task_rec.dependencies if d.current_blocking_flag == 'Y']
                waiting_for = "Waiting for {}".format(', '.join(waiting_for_list))
                self.set_task_summary_message(etl_task, waiting_for)
            else:
                self.set_task_summary_message(etl_task, "Dependencies not met")

    def check_for_new_task_commands(self):
        """
        Looks in the database repository for new task commands:
          * new task: Creates an ETLTask instance, and checks it's predesssors.
          * stop_requested: Sends a stop signal to the task
          * kill_requested: Sends s SIGKILL to terminate the task
        """

        #TODO: For new tasks this method of reading ETL_Tasks works. However, for stop requests it can fail.
        #      If the web-interface writes a stop request right as the scheduler updates the status message,
        #      the stop status will get overwritten by the status message update.
        #      Proposed solution: Create a scheduler message queue table that can be used to send messages
        #      to the scheduler. In environments where it's possible, the web-interface could also use
        #      a sockets interface to communicate directly with the scheduler.

        try:
            if self._new_tasks_query is None:
                valid_status_codes = [s.value for s in [Status.new, Status.stop_requested, Status.kill_requested]]
                query = self.session.query(ETL_Tasks).filter(ETL_Tasks.status_id.in_(valid_status_codes) )
                query = query.filter( ETL_Tasks.scheduler_id == self.scheduler_id )
                query = query.order_by(ETL_Tasks.task_id)
                self._new_tasks_query = query
            else:
                query = self._new_tasks_query
            for task_rec in query.all():
                if task_rec.Status == Status.new:
                    self.log.info("Registering new task {r.modulename} id {r.task_id} parent_task_id "
                                  "{r.parent_task_id} root_task_id {r.root_task_id}".format(
                                     r=task_rec
                    ))
                    etl_task = self._create_etl_task_object_from_task_rec(task_rec)
                    if etl_task is not None:
                        self.add_task_to_active(etl_task)
                        self.check_dependencies(etl_task)
                    else:
                        self.log.info("--Failed registering new task {r.modulename} id {r.task_id} "
                                      "parent_task_id {r.parent_task_id} root_task_id {r.root_task_id}".format(
                                          r=task_rec
                        ))
                elif task_rec.Status == Status.stop_requested:
                    if task_rec.task_id in self.etl_task_by_id:
                        try:
                            etl_task = self.etl_task_by_id[task_rec.task_id]
                            self.stop_task(etl_task)
                        # Scheduler doesn't die no matter what!
                        except Exception:  #pylint: disable=broad-except
                            task_rec.summary_message = traceback.format_exc()
                            self.session.commit()
                    else:
                        # it's not running, just change it's listing to stopped
                        self.log.warning("Got request to stop task that is not active. task_id={}".format(task_rec.task_id))
                        task_rec.Status = Status.stopped
                        self.session.commit()
                elif task_rec.Status == Status.kill_requested:
                    if task_rec.task_id in self.etl_task_by_id:
                        try:
                            etl_task = self.etl_task_by_id[task_rec.task_id]
                            self.kill_task(etl_task)
                        # Scheduler doesn't die no matter what!
                        except Exception:  #pylint: disable=broad-except
                            task_rec.summary_message = traceback.format_exc()
                            self.session.commit()
                    else:
                        # it's not running, just change it's listing to stopped
                        self.log.warning("Got request to kill task that is not active. task_id={}".format(
                            task_rec.task_id
                        ))
                        task_rec.Status = Status.stopped
                        self.session.commit()
                else:
                    self.log.error("Got task with un-expected status in "
                                   "check_for_new_task_commands. task_id={} status={}".format(
                                       task_rec.task_id,
                                       task_rec.Status
                    ))
        # Scheduler doesn't die no matter what!
        except Exception as e:  #pylint: disable=broad-except
            self.log.error(traceback.format_exc())
            self.log.error(repr(e))

    def run_task(self, etl_task):
        self.log.info("Starting task {}".format(etl_task))
        self.add_log_message(etl_task, 'Starting process')
        try:
            parent_to_child = multiprocessing.Queue()  # @UndefinedVariable
            child_to_parent = multiprocessing.Queue()  # @UndefinedVariable
            # Run method to avoid serializing the task itself
            process = multiprocessing.Process(target=bi_etl.scheduler.task.run_task,  # @UndefinedVariable
                                              kwargs={
                                                      'task_name': etl_task.name,
                                                      'task_id': etl_task.task_id,
                                                      'parent_task_id': etl_task.parent_task_id,
                                                      'root_task_id': etl_task.root_task_id,
                                                      'parent_to_child': parent_to_child,
                                                      'child_to_parent': child_to_parent,
                                                      'scheduler': self,
                                                     }
                           )
            process.start()
            etl_task.thread_running = True
            # After starting add the Queues to our copy of the etl_task object
            etl_task.parent_to_child = parent_to_child
            etl_task.child_to_parent = child_to_parent
            etl_task.process = process

            etl_task.task_rec.started_date = datetime.now()

            self.tasks_occupying_cpu.add(etl_task.task_id)
            self.log.debug('tasks_occupying_cpu = {}'.format(self.tasks_occupying_cpu))
            etl_task.task_rec.pid = process.pid
            self.set_task_summary_message(etl_task, None)
            self.set_task_status(etl_task, Status.running)
        # Scheduler doesn't die no matter what!
        except Exception as e:  #pylint: disable=broad-except
            self.add_log_message(etl_task,  traceback.format_exc() )
            self.set_task_summary_message(etl_task, repr(e))
            self.set_task_status(etl_task, Status.failed)

    def stop_task(self, etl_task):
        if etl_task.status.is_alive():
            self.set_task_summary_message(etl_task, "Stopping")
            self.log.debug("Sending stop request to {}".format(repr(etl_task)))
            self.send_task_message(etl_task, message='stop')
            self.set_task_status(etl_task, Status.stop_signal_sent)
        elif not etl_task.status.is_finished():
            self.set_task_status(etl_task, Status.stopped)

    def kill_task(self, etl_task):
        if etl_task.status.is_alive():
            self.set_task_summary_message(etl_task, "Killing")
            etl_task.process.terminate()
            if etl_task.status != Status.kill_signal_sent:
                self.set_task_status(etl_task, Status.kill_signal_sent)
        elif not etl_task.status.is_finished():
            self.set_task_status(etl_task, Status.stopped)

    def _write_log_message(self, task_id, msg, time_now=None):
        if msg is not None:
            if time_now is None:
                time_now = datetime.now()

            msg_rec = ETL_Task_Log()
            msg_rec.task_id = task_id
            msg_rec.log_entry_ts = time_now
            # TODO: despite having the database column support uncode, cx_oracle is getting
            # errors when we send unicode through. So we'll trip it out for now.
            msg = msg.encode('ascii', 'replace_tilda').decode('ascii')
            msg_rec.log_entry = msg
             
            self.session.add(msg_rec)

    def flush_log_messages(self, etl_task, time_now= None):

        if len(etl_task.pending_log_msgs) > 0:
            self.log.debug("flush_log_messages task_id={}".format(etl_task.task_id))
            if time_now is None:
                time_now = datetime.now()
            # Make sure log messages are at least 1 second apart to avoid PK violation
            if (etl_task.last_log_msg_time is not None
                and ((time_now - etl_task.last_log_msg_time) < timedelta(seconds=1))
               ):
                    time_now = etl_task.last_log_msg_time + timedelta(seconds = 1)
                    # Set the new last time
                    etl_task.last_log_msg_time = time_now

            if self.trace:
                self.log.debug("flush_log_messages task_id={} add msg".format(etl_task.task_id))

            log_entry = ''.join(etl_task.pending_log_msgs)
            self._write_log_message(etl_task.task_id, msg=log_entry, time_now=time_now)

            if self.trace:
                self.log.debug("flush_log_messages task_id={} commit".format(etl_task.task_id))            
            self.session.commit()
            del etl_task.pending_log_msgs[:]
            etl_task.last_log_msg_time = time_now
            if self.trace:
                self.log.debug("flush_log_messages task_id={} done".format(etl_task.task_id))

    def check_if_log_message_flush_needed(self, etl_task):
        time_now = datetime.now()
        if etl_task.last_log_msg_time is None:
            # Set the initial value to when we got called first,
            # this will delay the first log storage until log_flush_interval
            etl_task.last_log_msg_time = time_now
        elif (time_now - etl_task.last_log_msg_time) > timedelta(seconds=self.log_flush_interval):
            self.flush_log_messages(etl_task, time_now)

    def add_log_message(self, etl_task, msg, allow_duplicates=True):
        if msg is None:
            return

        if self.trace:
            self.log.debug("add_log_message task_id={} msg=---{}---".format(etl_task.task_id, msg.strip()))
        msg_ok = True
        if msg != etl_task.last_log_msg:
            etl_task.last_log_msg = msg
        else:
            if not allow_duplicates:
                msg_ok = False
        if msg_ok:
            if not isinstance(msg, str):
                msg = str(msg)
            # Add an ending new line if it's not there
            if not msg.endswith('\n'):
                msg += '\n'
            etl_task.pending_log_msgs.append(msg)
        else:
            if self.trace:
                self.log.debug("add_log_message task_id={} msg=---{}--- not saved (duplicate)".format(etl_task.task_id, msg.strip()))

        #self.check_if_log_message_flush_needed(etl_task)

    def process_statistics(self, etl_task, stats):
        task_rec = etl_task.task_rec
        for stat_name, stat_value in dict_to_pairs(stats):
            stat_name = str(stat_name)
            stat_value = str(stat_value)
            if stat_name in task_rec.stats:
                if task_rec.stats[stat_name] != stat_value:
                    task_rec.stats[stat_name] = ETL_Task_Stats(stat_name, stat_value)
            else:
                task_rec.stats[stat_name] = ETL_Task_Stats(stat_name, stat_value)
        self.session.commit()

    @staticmethod
    def _is_reloaded_instance(msg, class_obj):
        """
        Like isinstance but it should deal with modules that have been reloaded.
        Unlike isinstance it will NOT handle cases where msg inherits from class_obj
        """
        return str(type(msg)) == str(class_obj)

    def read_child_messages(self, etl_task):
        is_reloaded_instance = self._is_reloaded_instance
        q = etl_task.child_to_parent
        # Check that we actually have a queue
        if q is None:
            return
        try:
            while True:
                msg = q.get_nowait()
                if is_reloaded_instance(msg, Statistics):
                    self.process_statistics(etl_task, msg)
                elif isinstance(msg, str):  # basestring won't be affected by reload, so use the normal isinstance
                    self.add_log_message(etl_task, msg)
                elif is_reloaded_instance(msg, TaskStopRequested):
                    self.set_task_summary_message(etl_task, "Stopped")
                    self.set_task_status(etl_task, Status.stopped)
                elif isinstance(msg, Exception):  # Exception won't be affected by reload, so use the normal isinstance
                    self.set_task_summary_message(etl_task, repr(msg), from_client= True)
                elif is_reloaded_instance(msg, Status):
                    if etl_task.status not in [Status.stopped, Status.stop_signal_sent]:
                        self.log.debug("read_child_messages setting {} status to {}".format(etl_task, msg))
                        self.set_task_status(etl_task, msg)
                elif is_reloaded_instance(msg, ChildSetDisplayName):
                    child_task_id = msg.child_task_id
                    child_task = self.get_task_by_id(child_task_id)
                    child_task.display_name = msg.display_name
                elif is_reloaded_instance(msg, ChildRunOK):
                    child_task_id = msg.child_task_id
                    child_task = self.get_task_by_id(child_task_id)
                    if child_task is None:
                        self.log.error("Got ChildRunOK for invalid child task_id {}".format(child_task_id))
                    else:
                        child_task.waiting_for_workflow = False
                        msg = "Got ChildRunOK for {}, clearing waiting_for_workflow flag".format(child_task)
                        self.add_log_message(child_task, msg)
                        if child_task.status == Status.waiting_for_workflow:
                            self.set_task_status(child_task, Status.waiting_for_dependencies)
                        else:
                            msg = "After ChildRunOK on {}, leaving status as {}".format(child_task, child_task.status)
                            self.add_log_message(child_task, msg)
                elif is_reloaded_instance(msg, ChildNotOccupyingCPU):
                    child_task_id = msg.child_task_id
                    if child_task_id in self.tasks_occupying_cpu:
                        self.tasks_occupying_cpu.remove(child_task_id)
                    else:
                        child_task = self.get_task_by_id(child_task_id)
                        msg = "{} Sent ChildNotOccupyingCPU but it wasn't occupying CPU".format(child_task)
                        self.add_log_message(child_task, msg)
                        self.log.warning(msg)
                elif is_reloaded_instance(msg, ChildOccupyingCPU):
                    child_task_id = msg.child_task_id
                    if child_task_id not in self.tasks_occupying_cpu:
                        self.tasks_occupying_cpu.add(child_task_id)
                    else:
                        child_task = self.get_task_by_id(child_task_id)
                        msg = "{} Sent ChildOccupyingCPU but it already was occupying CPU".format(child_task)
                        self.add_log_message(child_task, msg)
                        self.log.warning(msg)
                elif is_reloaded_instance(msg, SummaryMessage):
                    if msg.append:
                        self.append_task_summary_message(etl_task, msg.summary_message)
                    else:
                        self.set_task_summary_message(etl_task, msg.summary_message, from_client= True)
                else:
                    self.log.warning("Got unexpected message from client: {}".format(repr(msg)))
        except Empty:
            pass

    def check_if_done(self, etl_task):
        try:
            self.log.debug("Calling is_alive: {}".format(repr(etl_task)))
            if hasattr(etl_task, 'process') and etl_task.process.is_alive():
                if etl_task.status.is_finished():
                    self.log.warning("Task {} is completed but is_alive is still true.".format(repr(etl_task)))
                    try:
                        self.log.warning("...Process={}".format(etl_task.process))
                        self.log.warning("...Process PID={}".format(etl_task.process.pid))
                    except AttributeError:
                        pass
            else:
                if hasattr(etl_task, 'thread_running') and etl_task.thread_running:
                    self.log.debug("Calling join: {}".format(repr(etl_task)))
                    self.add_log_message(etl_task, "Cleaning up thread")
                    etl_task.process.join(10)
                    if etl_task.task_id in self.tasks_occupying_cpu:
                        self.tasks_occupying_cpu.remove(etl_task.task_id)
                        self.log.debug('tasks_occupying_cpu = {}'.format(self.tasks_occupying_cpu))
                    etl_task.thread_running = False
                    if etl_task.process.exitcode != 0:
                        self.log.warning("etl_task {} had exit code {}".format(repr(etl_task), etl_task.process.exitcode))
                        self.add_log_message(etl_task, "exit code {}".format( etl_task.process.exitcode))
                    if etl_task.status == Status.succeeded:
                        self.set_task_summary_message(etl_task, "Done", commit=True)

                if etl_task.status in [Status.running, Status.succeeded, Status.ancestors_running]:
                    children_done = True
                    children_status = None
                    for child_task in etl_task.children:
                        if child_task.status != child_task.task_rec.Status:
                            self.log.error('child_task.status {} != child_task.task_rec.Status {}'.format(child_task.status, child_task.task_rec.Status))
                            self.add_log_message(etl_task,'ERROR child_task.status {} != child_task.task_rec.Status {}'.format(child_task.status, child_task.task_rec.Status))
                            child_task.status = child_task.task_rec.Status
                        if not child_task.status.is_finished():
                            children_done = False
                            self.log.debug("check_if_done etl_task {} waiting for child {} in status {}".format(repr(etl_task), repr(child_task), child_task.status))
                            self.add_log_message(etl_task, "Waiting for child {} in status {}".format(repr(child_task), child_task.status))
                            break
                        else:  # Get the "worst" child status... the lowest.
                            self.add_log_message(etl_task, "Collecting status for child {} in status {}".format(repr(child_task), child_task.status))
                            if children_status is None:
                                children_status = child_task.status
                                self.log.debug("check_if_done etl_task {} first child status {}".format(repr(etl_task), children_status))
                            elif child_task.status < children_status:
                                children_status = child_task.status
                                self.log.debug("check_if_done etl_task {} new low child status {}".format(repr(etl_task), children_status))
                    if children_done:
                        # Set is_finished time
                        self.add_log_message(etl_task, "Task and all ancestors is_finished")
                        self.set_task_summary_message(etl_task, 'Done')
                        self.log.debug("check_if_done: {} not is_alive and children_done. "
                                       "etl_task.status={} children_status={}".format(
                                          repr(etl_task),
                                          etl_task.status,
                                          children_status
                        ))
                        if children_status is not None:
                            if children_status == Status.failed:
                                self.set_task_status(etl_task, Status.ancestor_failed)
                            else:
                                self.set_task_status(etl_task, children_status)
                        else:
                            # Double check for child messages that might update our status
                            self.read_child_messages(etl_task)
                            # If still running then task must have failed
                            if etl_task.status == Status.running:
                                self.set_task_status(etl_task, Status.failed)
                        self.log.debug("check_if_done: {} chilren_done etl_task.status={}".format(repr(etl_task), etl_task.status))
                        self.add_log_message(etl_task, "Final status = {}".format(etl_task.status))
                    else:  # children not done
                        if etl_task.status != Status.ancestors_running:
                            # From above we know status is in
                            # [Status.running, Status.succeeded, Status.ancestors_running]
                            self.set_task_status(etl_task, Status.ancestors_running)
                elif etl_task.status == Status.failed:
                    pass
                elif etl_task.status == Status.stop_signal_sent:
                    self.set_task_status(etl_task, Status.stopped)
                elif etl_task.status == Status.stopped:
                    pass
                elif etl_task.status == Status.kill_signal_sent:
                    self.set_task_status(etl_task, Status.killed)
                else:
                    self.log.warning("Unexpected status {} in check_if_done for task {}".format(
                        etl_task.status,
                        repr(etl_task)
                    ))
                    self.set_task_status(etl_task, Status.failed)

        except AttributeError as e:
            self.log.error("check_if_done: {}".format(repr(e)))

    def check_for_previous_instance_tasks(self):
        """
        Looks in the database repository for tasks from a previous instance.
        """
        running_status_codes = list()
        for s in Status:
            if not s.is_finished() and not s == Status.new:
                running_status_codes.append(s.value)
        query = self.session.query(ETL_Tasks).filter(ETL_Tasks.status_id.in_(running_status_codes) )
        query = query.filter( ETL_Tasks.scheduler_id == self.scheduler_id )
        query = query.order_by(ETL_Tasks.task_id)
        our_process = self.psutil.Process()
        wait_pids = list()
        for task_rec in query.all():
            self.log.info("Found task {task_rec.task_id} {task_rec.modulename} "
                          "for previous scheduler instance listed as active".format(
                              task_rec=task_rec
            ))
            pid = task_rec.pid
            if pid and self.psutil.pid_exists(pid):
                try:
                    process = self.psutil.Process(pid)
                    if (process.is_running()
                        and (process.exe() == our_process.exe())
                        and (process.gids() == our_process.gids())
                       ):
                        self.log.info("  {task_rec.task_id} {task_rec.modulename} is still running "
                                      "as pid {task_rec.pid}".format(task_rec=task_rec))
                        wait_pids.append(pid)
                        process.terminate()
                        task_rec.summary_message = "Killed (active task PID) on scheduler restart. " \
                                                   "Prior status was {}".format(task_rec.Status)
                    else:
                        task_rec.summary_message = "Killed (PID didn't match) on scheduler restart. " \
                                                   "Prior status was {}".format(task_rec.Status)
                except self.psutil.NoSuchProcess:
                    pass
            else:
                task_rec.summary_message = "Killed (PID not active) on scheduler restart. " \
                                           "Prior status was {}".format(task_rec.Status)
            task_rec.Status = Status.killed
            self.log.info("  {task_rec.task_id} {task_rec.modulename} "
                          "new status = {task_rec.status_id}".format(task_rec=task_rec))

        self.session.commit()
        if len(wait_pids) > 0:
            self.log.info("Waiting for previous schedulers tasks to end.")
            self.psutil.wait_procs(wait_pids, timeout=30)
            self.log.info("Done waiting for previous schedulers tasks to end.")

    def delete_old_run_logs(self):
        query = self.session.query(ETL_Tasks)
        query = query.filter(ETL_Tasks.submitted_date <
                             (datetime.now()-timedelta(days=self.days_to_keep_run_logs) )
                             )
        query.delete()

    def purge_old_lager_parameters(self):
        query = self.session.query(ETL_Tasks)
        query = query.filter(ETL_Tasks.submitted_date <
                             (datetime.now()-timedelta(days=self.days_to_keep_large_parameters) )
                             )
        for etl_task_rec in query:
            for param in etl_task_rec.parameters:
                if len(param.param_value) > self.min_large_parameter_size:
                    param.param_value = 'PURGED'

    def check_for_required_table_maintenance(self):
        # Delete etl_task records from the database after retention period X days
        if (self.last_table_maintenance_run is None
            or (datetime.now() - self.last_table_maintenance_run) > timedelta(hours=24)
           ):
            self.log.info("Performing table cleanup")
            #logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
            #logging.getLogger('sqlalchemy.engine.base.Engine').setLevel(logging.DEBUG)
            self.delete_old_run_logs()
            self.purge_old_lager_parameters()
            self.session.commit()
            self.last_table_maintenance_run = datetime.now()

    def start_monitoring(self):
        #logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
        #logging.getLogger('sqlalchemy.engine.base.Engine').setLevel(logging.DEBUG)
        #logging.getLogger('sqlalchemy.orm').setLevel(logging.DEBUG)

        # Check for tasks that are listed as running, or waiting from the last run of the scheduler
        self.log.info("check_for_previous_instance_tasks")
        self.check_for_previous_instance_tasks()
        
        self.scan_etl_classes()

        self.log.info("Running status code upsert task")
        self.add_task_by_class(ETL_Task_Status_CD)

        self.log.info("Starting monitoring for new jobs")

        while True:
            try:
                self.check_for_new_task_commands()

                list_to_remove = list()

                for etl_task_id in self.etl_task_by_id:
                    etl_task = self.etl_task_by_id[etl_task_id]
                    #self.log.debug("Checking on task {}".format(repr(etl_task)))
                    self.session.refresh(etl_task.task_rec)        
                    status = etl_task.status
                    if not status.is_finished():
                        self.log.debug("Checking task {} with status {}".format(repr(etl_task), status))

                    if etl_task.thread_running or etl_task.status.is_termination_pending():
                        # Read any messages in the queue for this task
                        self.read_child_messages(etl_task)
                        self.check_if_done(etl_task)
                    elif status.is_finished():
                        # Check if we can remove from memory (active tasks)
                        if etl_task.root_task_id is None:
                            if etl_task.task_rec.finished_date is not None:
                                if ((datetime.now() - etl_task.task_rec.finished_date)
                                    > timedelta(minutes=self.seconds_to_keep_finished_tasks)
                                   ):
                                    list_to_remove.append(etl_task)
                            else:
                                self.log.warning("Task {} has is_finished status but no finished_date.".format(
                                    repr(etl_task)
                                ))
                    elif status == Status.ancestors_running:
                        self.check_if_done(etl_task)
                    elif status == Status.waiting_for_cpu:
                        self.check_for_cpu(etl_task)
                    elif status == Status.waiting_for_dependencies:
                        self.check_dependencies(etl_task)
                    else:
                        msg = "Unexpected status {} in monitoring loop for task {}".format(status, etl_task)
                        self.log.warning(msg)
                    self.flush_log_messages(etl_task)
                # End for loop of etl_task's

                etl_task = None

                for etl_task in list_to_remove:
                    self.remove_active_task_record(etl_task)

                # Update heart beat time in etl_schedulers table
                self.heatbeat_now()

                self.check_for_required_table_maintenance()

                self.session.commit()
            except (CircularDependency, DependencyDeeperThanLimit) as e:
                self.add_log_message(etl_task, repr(e))
                self.set_task_summary_message(etl_task, "Invalid dependency. See log.")
                self.set_task_status(etl_task, Status.failed)
                self.flush_log_messages(etl_task)
            # Scheduler doesn't die no matter what!
            except DetachedInstanceError:
                raise SystemExit
            except Exception as e:  #pylint: disable=broad-except
                self.log.error(traceback.format_exc())
                self.log.error(repr(e))
                try:
                    self.session.commit()                
                except Exception:  #pylint: disable=broad-except
                    # OK, things are more serious here. Rollback?
                    # We might just not have a database connection anymore
                    # We'll let a rollback failure kill the Scheduler (outer shell script should re-start it)
                    self.session.rollback()
            except KeyboardInterrupt:
                self.log.error("KeyboardInterrupt, killing tasks")
                for etl_task_id in self.etl_task_by_id:
                    etl_task = self.etl_task_by_id[etl_task_id]
                    if etl_task.thread_running:
                        self.kill_task(etl_task)
                self.log.error("KeyboardInterrupt done killing tasks")
                raise SystemExit

            if len(self.etl_task_by_id) > 0:
                self.log.debug("Wait {} sec before checking status again".format(self.process_check_interval))
            try:
                time.sleep(self.process_check_interval)
            except KeyboardInterrupt:
                self.log.error("KeyboardInterrupt killing tasks")
                try:
                    self.session.rollback()
                # Different DBs seem to give different exceptions here
                except Exception:  #pylint: disable=broad-except
                    # Already exiting
                    pass
                for etl_task_id in self.etl_task_by_id:
                    etl_task = self.etl_task_by_id[etl_task_id]
                    if etl_task.thread_running:
                        try:
                            self.kill_task(etl_task)
                        except Exception: #pylint: disable=broad-except
                            # Already exiting
                            pass
                self.log.error("KeyboardInterrupt done killing tasks")
                raise SystemExit


if __name__ == '__main__':
    scheduler = Scheduler()
    scheduler.start_monitoring()
