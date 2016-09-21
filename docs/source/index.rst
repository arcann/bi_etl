.. bi_etl documentation master file, created by
   sphinx-quickstart on Fri Nov 06 14:18:50 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

################################
BI ETL Python Framework (bi_etl)
################################


*******************
Configuration Files
*******************

.. toctree::
   :hidden:

   config_ini
   coding_standards
   modules

======================== ================================================
File                     Contents                                       
======================== ================================================
:doc:`config_ini`        This is the main configuration file for the
						 bi_etl module. By default the module will look
						 for the file in your user directory.
						 \
======================== ================================================
	
To configure the bi_etl system you **must** setup :doc:`config_ini`
	
***********************
Sequence of an ETL Task
***********************

The definition of an ETL Task will be a python class inheriting from :class:`bi_etl.scheduler.task.ETLTask`. 
This documentation will henceforth refer to that class as simply ``ETLTask``.

To run a task you use :func:`bi_etl.scheduler.task.run_task`.  When ``run_task`` is called it is given a module name. It will:

1. Load the configuration file using :class:`bi_etl.bi_config_parser.BIConfigParser`.

2. Setup a file based log using task_name via :meth:`config.set_dated_log_file_name` using the module name passed into run_task.

3. Search for that a module named task_name in the ``PYTHONPATH``.
   
   * It looks for the module under the package (folder) ``etl_jobs``. For example ``run_task('my_table')`` would match *any* of:
   
		 * ``etl_jobs.my_table``
		 * ``etl_jobs.foo.my_table``
		 * ``etl_jobs.foo.bar.my_table``
		 * ``etl_jobs.not_my_table`` (which might be a problem)

4. After finding the module, look for a class based on ``ETLTask`` in that module.  
**By default it will fail if there is more than one such class.** You can add an optional parameter ``class_name`` to 
the ``run_task`` function to have it use a specific class and thus not fail if there is more than one.

5. Start the ``run`` method of ``ETLTask``. This a standard framework method. It will:

	a.	Initialize the task statistics (start times, etc.)
	b.	Call the :meth:`init <bi_etl.scheduler.task.ETLTask.init>` method that you can override in your class.
	c.	Call the :meth:`load <bi_etl.scheduler.task.ETLTask.load>` method that you must override in your class.
	d.	Call the :meth:`finish <bi_etl.scheduler.task.ETLTask.finish>` method that you can override in your class.
	e.	Finalize the statistics
	f.	Send an e-mail on failure (see configuration file section ``SMTP`` item ``distro_list``)


**************************
Source / Target Components
**************************

Within a task you will use source / target components to extract and load the data. 

=================================================================== ========== ========== ====================================================================
Component Class                                                     Usable as  Usable as  Notes
																	Source     Target
=================================================================== ========== ========== ====================================================================
:class:`~bi_etl.components.csvreader.CSVReader`                     Yes        No         Can read *any* delimited file (see ''delimiter'' parameter) 
																						  It is based on the Python csv module.
																						  See https://docs.python.org/3.5/library/csv.html
:class:`~bi_etl.components.xlsx_reader.XLSXReader`                  Yes        No         Reads from Excel files; although only those in xlsx format.
:class:`~bi_etl.components.sqlquery.SQLQuery`                       Yes        No         Reads from the result of a SQL query.
:class:`~bi_etl.components.readonlytable.ReadOnlyTable`             Yes        No         Useful when reading all columns from a database table or view.
																						  Rows can be filtered using the where method.
:class:`~bi_etl.components.table.Table`                             Yes        Yes        Inherits from ReadOnlyTable. Added features:                                                                                 
																						  * lookups, optional data cache
																						  * insert, update, delete and upsert
																						  * delete_not_in_set, and delete_not_processed
																						  * logically_delete_not_in_set, and not_processed
																						  * update_not_in_set, update_not_processed
:class:`~bi_etl.components.hst_table.Hst_Table`                     Yes        Yes        Inherits from Table. Adds ability to correctly load versioned
																						  tables. Supports both type 2 dimensions and date versioned
																						  warehouse tables. Also has cleanup_spurious_versions method
																						  to remove version rows that are not needed (due to being
																						  redundant).
:class:`~bi_etl.components.data_analyzer.DataAnalyzer`              No         Yes        Produces a summary of the columns in the data rows passed to the
																						  :meth:`~bi_etl.components.data_analyzer.DataAnalyzer.analyze_row`
																						  method.
																						  The output currently goes to the task log.
=================================================================== ========== ========== ====================================================================                                                                                          

.. note::                                                                                          
   There are not yet components for *writing* delimited files or Excel files.
   
   However, csv.DictWriter works well for writing delimited files. The added statistics tracking features of an ETLComponent do not seem critical.
   
   openpyxl can be used for directly writing Excel files. 

Functionality common to all sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All source components share the following common functionality.

The source can output progress messages to the task log every X
seconds. This defaults to every 10 seconds with the message format
being ``"{logical_name} current row # {row_number:,}"``. See parameters
``progress_frequency``, and ``progress_message``.

They can limit the number of rows to process. See parameter ``max_rows``
(Default None)

They can print a debug trace of all rows processed. See class property
``trace_data`` (default False).

They can print a debug trace of the first row processed. See parameter
and class property ``log_first_row`` (default False).

They track statistics on how long it took to retrieve the first row
and all rows. The read timer is starts and stops as rows are passed
onto other code, so it should represent just the read elapsed time.

.. include:: source_transformations.rst


*********************
Coding Standards Used
*********************

Please see :doc:`coding_standards`


********
Examples
********


Example task definition - Simple Table Truncate and Load
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from bi_etl.scheduler.task import ETLTask
   from bi_etl.components.csvreader import CSVReader
   from bi_etl.components.table import Table
   
   
   class STAGE_TABLE(ETLTask):

	   def load( self):
		   ## get_database is a method of ETLTask that will get a connected
		   ## database instance. See docs.
		   target_database = self.get_database('EXAMPLE_DB')
   
		   ## Make an ETL Component to read the source file
		   with CSVReader(self,
						  filedata = r"E:\Data\training\ExampleData1-a.csv",
						  ) as source_file:
   
			   ## Make an ETL Component to write the target dimension data.
			   with Table(task= self,
						  database= target_database,
						  table_name= 'example_1',
						  ) as target_table:
   
				   ## Truncate the table before load
				   target_table.truncate()
   
				   ## Start looping through source data
				   for row in source_file:
					   target_table.insert(row)
   
				   ## Issue a commit at the end.
				   ## If your database needs more frequent commits, that can be done as well.
				   target_table.commit()
   
				   self.log.info("Done")
   
   ### Code to run the load when run directly
   if __name__ == '__main__':
	   ## Should only be invoked directly when testing code.
	   ## So don't send error e-mails.
	   STAGE_TABLE().run(no_mail = True)

If you do need to commit in smaller batches you can add these lines inside the ``for row in source`` file loop

.. code-block:: python

   if source_file.rows_read % 10000 == 0:
	  source_file.commit()

Example task definition - Simple Table Load with Update/Insert
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example will start and end the same as the Truncate and Load example.  
So the code block below is only the contents of the two ``with`` blocks.  

.. code-block:: python

		 with Table...
			   ## <-- Removed truncate from here

			   ## Start looping through source data
			   for row in source_file:
				   target_tbl.upsert(row)  ### <-- changed to upsert instead of insert

			   ## Issue a commit at the end
			   target_table.commit()

			   self.log.info("Done")


In summary:
1) We removed the call to the ``truncate`` command
2) We changed the  ``insert`` call to an :meth:`~bi_etl.components.table.Table.upsert` call.

The :meth:`~bi_etl.components.table.Table.upsert` command will look for an existing row in the target table 
(using the primary key lookup if no alternate lookup name is provided). If no existing row is found, an insert
will be generated. If an existing row is found, it will be compared to the row passed in. If changes are found,
an update will be generated.  


Example task definition - Simple Dimension Load
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this example we add in features to
1) Generate a surrogate key
2) Lookup using the natural key (not the primar key)
3) Logically delete rows that were not in the source 

.. code-block:: python

   from bi_etl.scheduler.task import ETLTask   
   from bi_etl.components.readonlytable import ReadOnlyTable   
   from bi_etl.components.table import Table
   
   class D_WBS(ETLTask):
	  def load( self):
		 ## get_database is a method of ETLTask that will get a connected
		 ## database instance. See docs.
		 source_database = self.get_database('WAREHOUSE')
		 target_database = self.get_database('DATAMART')

		 ## Make an ETL Component to read the source view.
		 with ReadOnlyTable(task= self,
							database= source_database,
							table_name= 'd_wbs_src_vw',
							) as source_data:

			## Make an ETL Component to write
			## the target dimension data.
			with Table(task= self,
					   database= target_database,
					   table_name= 'd_wbs',
					   ) as target_table:

			   ## Enable option to generate a surrogate key value for
			   ## the primary key
			   target_table.auto_generate_key= True

			   ## Specify the column to get the last update
			   ## date value (from system date)
			   target_table.last_update_date= 'last_update_date'

			   ## Specify the column to get Y/N delete flag values.
			   target_table.delete_flag = 'delete_flag'

			   ## Track rows processed for logically_delete_not_processed
			   target_table.track_source_rows=True

			   ## Define an alternate key lookup using the
			   ## natural key column. If we don't, the
			   ## upsert process would try and use the primary key
			   ## which is the surrogate key.
			   target_table.define_lookup('AK',['wbs_natural_key'])

			   ## Fill the cache to improve performance
			   target_table.fill_cache()

			   ## Log entry
			   self.log.info("Processing rows from {}".format(source_data))

			   ## Start looping through source data
			   for row in source_data:
				  ## Upsert (Update else Insert) each source row
				  target_table.upsert(row,
									  ## Use the alternate key define above
									  ## to perform lookup for existing row
									  lookup_name = 'AK'
									  )
			   target_table.commit()

			   self.log.info("Processing deletes from {}".format(target_table))
			   target_table.logically_delete_not_processed()
			   target_table.commit()

			   self.log.info("Done")

   ### Code to run the load when run directly
   if __name__ == '__main__':
	  ## Should only be invoked directly when testing code.
	  ## So don't send error e-mails.
	  D_WBS().run(no_mail = True)


************
Modules APIs
************
.. toctree::
   :maxdepth: 5

   source_transformations
   bi_etl   

******************
Indices and tables
******************

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

