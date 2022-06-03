"""
Created on Sep 18, 2014

@author: Derek Wood
"""
import sys
from argparse import ArgumentParser

from bi_etl.scheduler.scheduler_interface import SchedulerInterface
from bi_etl.scheduler.status import Status
from bi_etl.scheduler.task import run_task

if __name__ == '__main__':
    parser = ArgumentParser(description="Run ETL")
    parser.add_argument('--task', type=str, help='deprecated way of specifying the task' )
    parser.add_argument('--via_scheduler', action='store_true', help='Run the task via the scheduler (asynchronous unless --wait is specified)' )
    parser.add_argument('--wait', action='store_true', help='Wait for the scheduler to finish running the task (synchronous run)' )
    parser.add_argument('--config', type=str, help='path to config file or files (comma separated) (not supported for via_scheduler)' )
    parser.add_argument('--param', type=str, nargs='?', action='append', help='parameter to pass eg.: --param foo=bar \n All parameters will be passed as strings')
    parser.add_argument('tasks_to_run', type=str, nargs='*')
    args = parser.parse_args()
    
    # print(sys.argv)
    succeeded = False
    
    if args.task:
        print("task to run {} (Note: --task is deprecated)".format(args.task))
        succeeded =run_task(args.task)
    elif args.tasks_to_run:
        if args.via_scheduler:
            print("Running via scheduler")
            sched = SchedulerInterface()
        print("tasks to run {}".format(args.tasks_to_run))
        parameters = dict()
        if args.param is not None:
            print(("args.param = {}".format(args.param)))
            for parm in args.param:
                print(("parm = {}".format(parm)))
                (parm_name, parm_value) = parm.split("=")
                parameters[parm_name] = parm_value
        for task in args.tasks_to_run:
            if args.via_scheduler:
                task_id = sched.add_task_by_partial_name(partial_module_name=task, parameters=parameters)
                if args.wait:
                    status = sched.wait_for_task(task_id)
                    succeeded = status == Status.succeeded
                else:
                    succeeded = True
            else:
                succeeded = run_task(task, config=args.config, parameters=parameters)
                        
    else:
        parser.print_usage()
        succeeded = True
    
    # Exit code 0 == success so it's the inverse of succeeded
    # Make really sure to call sys.exit with an integer otherwise it doesn't work.
    if not succeeded:
        sys.exit(99)
    else:       
        sys.exit(0)
