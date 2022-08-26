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