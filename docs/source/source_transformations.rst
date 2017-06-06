***************
Transformations
***************

Source values can be transformed with an explicit assignment to the row.

.. code-block:: python

   for row in source_table:
      row['my_column'] = str2decimal( row['my_column'] )
      ## Do something with the row
      target_table.upsert(row)
      

They can also be passed to the row object.

.. code-block:: python

    for row in source_table:
       row.transform('my_column', str2decimal)
       row.transform('date', str2date, ('%Y-%m-%d') )
       row.transform('date_as_str', nullif, ('00/00/0000') )
       ## Do something with the row
       target_table.upsert(row)

      
``source_transformations`` can be a list of tuples. However, the parenthesis get hard to manage if you try to build 
the entire thing in a single static assignment.
      
Implicit
~~~~~~~~

If the source and target datatypes are not the same, and no explicit transformation
is applied, the bi_etl framework will attempt to convert the value for you. It will 
generate Exceptions if it is unable to convert a value.

Dates require special care. The attribute :attr:`bi_etl.components.table.Table.default_date_format` 
has a reasonable default value (for US based dates) and can be used to do this implicit conversion. However, 
dates like 11/03/2015 and 03/11/2015 are ambiguous and will load successfully despite being potentially
wrong.