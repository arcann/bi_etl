********
Examples
********

.. contents:: Table of Contents
    :depth: 2

Example task definition - Simple Table Truncate and Load
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: stage_table.py
    :language: python


The batch_size property of Table controls how many rows are sent to the database at once.
However, by default all rows are committed in a single transaction.
If you do need to commit in smaller batches you can add these lines inside the ``for row in source`` file loop

.. code-block:: python

   if source_file.rows_read % 10000 == 0:
      source_file.commit()

Example task definition - Simple Table Load with Update/Insert
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example will start and end the same as the Truncate and Load example.
So the code block below is only the contents of the two ``with`` blocks.

.. code-block:: python
    :emphasize-lines: 2,6

         with Table...
               # <-- Removed truncate from here

               # Start looping through source data
               for row in source_file:
                   target_tbl.upsert(row)  # <-- changed to upsert instead of insert

               # Issue a commit at the end
               target_table.commit()

               self.log.info("Done")


In summary:

    1) We removed the call to the :meth:`~bi_etl.components.table.Table.truncate` command
    2) We changed the  :meth:`~bi_etl.components.table.Table.insert` call to an :meth:`~bi_etl.components.table.Table.upsert` call.

The :meth:`~bi_etl.components.table.Table.upsert` command will look for an existing row in the target table
(using the primary key lookup if no alternate lookup name is provided). If no existing row is found, an insert
will be generated. If an existing row is found, it will be compared to the row passed in. If changes are found,
an update will be generated.


Example task definition - Simple Dimension Load
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this example we add in features to:

    1) Generate a surrogate key
    2) Lookup using the natural key (not the primary key)
    3) Logically delete rows that were not in the source


.. literalinclude:: d_wbs.py
    :language: python
    :emphasize-lines: 31,41,47,67
