***************
Transformations
***************

Explicit in loop
~~~~~~~~~~~~~~~~

Source values can be transformed with an explicit assignment to the row.

.. code-block:: python

   for row in source_table:
      row['my_column'] = str2decimal( row['my_column'] )
      ## Do something with the row
      
Explicit in load methods
~~~~~~~~~~~~~~~~~~~~~~~~

Source values can also be transformed in the load method (upsert, insert, or update) using the ``source_transformations`` parameter.

The cleanest way to build explicit transformations is to use the ``Transformation`` and ``Conversion`` helper classes.  
In this case Transformation is the mapping of a column name to a conversion routine that changes the input value to a new output
value. **This the is preferred way of specifing transformations.**

.. code-block:: python

   ## Import the helper classes
   from bi_etl.conversions import Transformation
   from bi_etl.conversions import Conversion
   
   ## Using a list to hold the transforms 
   transformations = list() 
   transformations.append( Transformation('date_col',
                                           Conversion(str2date, '%Y-%m-%d') 
                                          )  
                         )
                       
   ## You can also create a single transform and apply it to many columns
   ymd_parse = Conversion(str2date, '%Y-%m-%d')
   
   ## Using the Transformation class
   transformations.append( Transformation('date2_col', ymd_parse) )
   
   ## Or a simple tuple
   transformations.append( ('date3_col', ymd_parse) )
   
   for row in source_table:
      target_table.upsert(row,  source_transformations= transformations)
      
``source_transformations`` can be a list of tuples. However, the parenthesis get hard to manage if you try to build 
the entire thing in a single static assignment.   

.. code-block:: python

   ## Using a list to hold the transforms
   my_source_transformations = [                    ## Tuple format alternatives
      ( 'my_column1', str2decimal ),                ## Simple name mapped to function
      ( 'my_column2', ( str2decimal ) ),            ## Name mapped to tuple with just function
      ( 'date_as_str', (nullif, ('00/00/0000')) )   ## Name mapped to tuple with function and arguments (as tuple)
      ( 'date2', Conversion(nullif, '00/00/0000') ) ## Name mapped to Conversion class
      ]

   for row in source_table:
      target_table.upsert(row,  source_transformations= my_source_transformations)
      
Instead you can make it a bit easier to read by building the list an item at a time. 
This code should be run only once before the loop so performance isn't really an issue.
However using the ``Conversion`` class would make this code easier to read.

.. code-block:: python

   ## Using a list to hold the transforms
   my_source_transformations = list()
   
   col1_transform = ( 'my_column1', str2decimal )   ## Simple name mapped to function
   my_source_transformations.append(col1_transform)
   
   col2_transform = ( 'my_column2', (str2decimal) ) ## Name mapped to tuple with just function (no args)
   my_source_transformations.append(col2_transform)
   
   nullif_transform = (nullif, ('00/00/0000'))
   col3_transform = ( 'date_as_str', nullif_transform) ## Name mapped to tuple with function and arguments (as tuple)
   my_source_transformations.append(col3_transform)
   
   nullif_conv_transform = Conversion(nullif, '00/00/0000')
   col4_transform = ( 'date2', nullif_conv_transform) ## Name mapped to Conversion class instance
   my_source_transformations.append(col4_transform)

   for row in source_table:
      target_table.upsert(row,  source_transformations= my_source_transformations)
      
``source_transformations`` can also be a dict but you loose control of the ordering of transforms. 

.. code-block:: python

   ## Using a dict to hold the transforms
   my_source_transformations = {                ## Dict value alternatives
      'my_column1': str2decimal,                ## Simple name mapped to function
      'my_column2': ( str2decimal ),            ## Name mapped to tuple with just function
      'date_as_str': (nullif, ('00/00/0000'))   ## Name mapped to tuple with function and arguments (as tuple)
      'date2': Conversion(nullif, '00/00/0000') ## Name mapped to Conversion class
      }

   for row in source_table:
      target_table.upsert(row,  source_transformations= my_source_transformations)                  
      
Implicit
~~~~~~~~

If the source and target datatypes are not the same, and no explicit transformation
is applied, the bi_etl framework will attempt to convert the value for you. It will 
generate Exceptions if it is unable to convert a value.

Dates require special care. The attribute :attr:`bi_etl.components.table.Table.default_date_format` 
has a reasonable default value (for US based dates) and can be used to do this implicit conversion. However, 
dates like 11/03/2015 and 03/11/2015 are ambiguous and will load successfully despite being potentially
wrong.       
