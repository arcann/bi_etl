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

Source and target components wit