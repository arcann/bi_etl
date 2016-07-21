#!/bin/bash

screen2 -S Scheduler -X select .
status=$?
if [ $status -ne 0 ]; then
    cd  ~obiinf/code_repositories/DBScripts/bi_etl/scheduler
    screen2 -d -m -S Scheduler bash -l -c ~obiinf/code_repositories/DBScripts/bi_etl/scheduler/run_scheduler.sh
    echo screen started status $?
    screen2 -list
else
    screen2 -list
    echo Already running.  Use screen -r to attach to it
fi
