#######################
Sequence of an ETL Task
#######################

The definition of an ETL Task will be a python class inheriting from :class:`bi_etl.scheduler.task.ETLTask`.
This documentation will henceforth refer to that class as simply ``ETLTask``.

To start the task, call the ``run`` method of ``ETLTask``. This a standard framework method. It will:

   a.	Initialize the task statistics (start times, etc.)
   b.	Call the :meth:`init <bi_etl.scheduler.task.ETLTask.init>` method that you *can* override in your class.
   c.	Call the :meth:`load <bi_etl.scheduler.task.ETLTask.load>` method that you **must** override in your class.
   d.	Call the :meth:`finish <bi_etl.scheduler.task.ETLTask.finish>` method that you *can* override in your class.
   e.	Finalize the statistics
   f.	Call any notifiers on failure.


***********
init method
***********

Implementing this method is optional. The only reason to do so is if you are creating a base class that
many other classes will inherit from, and you need to provide that base class with some common initialization
code.

***********
load method
***********

Implementing this method is **required**. This is the where the main logic of your task goes.
See :doc:`Examples <examples>`

*************
finish method
*************

Implementing this method is optional. The only reason to do so is if you are creating a base class that
many other classes will inherit from, and you need to provide that base class with some common close out
code.

***************
Task statistics
***************

Source and target components automatically gather timing and row count statistics as they
process records. At the end of the load it will dump a set of hierarchical log lines showing
all the statistics captured.

.. code-block:: text
  :caption: Example statistics

    INFO     etl.example.job statistics=
    example_target_table:
        AutoDiskLookup example_target_table.NK:
            Final Row Count: 887
            Memory Size: 280,292
            Disk Size: 0
        truncate:
            start time: 2024-03-01 16:15:46.739647
            stop  time: 2024-03-01 16:15:47.120763
            seconds elapsed: 0.381
            calls: 1
        AutoDiskLookup example_target_table.PK:
            Final Row Count: 887
            Memory Size: 280,292
            Disk Size: 0
        fill_cache:
            seconds elapsed: 0.140
            read:
                seconds elapsed: 0.138
                rows_read: 887
                first row seconds: 0.073 seconds
            build_row_safe:
                seconds elapsed: 0.011
                calls: 887
            rows in d_mer_measure_new.NK: 887
            rows in d_mer_measure_new.PK: 887

        upsert:
            start time: 2024-03-01 16:15:59.031678
            stop  time: 2024-03-01 16:16:03.055120
            seconds elapsed: 1.144
            upsert source row count: 11,201
            build_row_safe:
                seconds elapsed: 0.118
                calls: 11,201
            get_by_lookup:
                seconds elapsed: 0.166
                Found in cache: 11,201
            updated columns:
                source_srgt_key: 312
                example_column1: 4,425
                example_column2: 5,620
                example_column3: 5,620
            update:
                seconds elapsed: 0.274
        logically_delete_not_processed:
            seconds elapsed: 0.009
            rows read: 887
            updates count: 0
            read:
                seconds elapsed: 8.930
                rows_read: 887
                first row seconds: 0.000 seconds
    SQLQuery(source_query_name :sorted:):
        read:
            seconds elapsed: 4.487
            rows_read: 11,201
            first row seconds: 0.455 seconds
    Task Load:
        start time: 2024-03-01 16:15:41.670609
        stop time: 2024-03-01 16:16:11.993136
        seconds elapsed: 30.323 seconds
