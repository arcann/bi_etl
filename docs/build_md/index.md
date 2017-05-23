### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](config_ini.md "config.ini") |
-   [bi\_etl 0.5.3 documentation](#) »

BI ETL Python Framework (bi\_etl)<a href="#bi-etl-python-framework-bi-etl" class="headerlink" title="Permalink to this headline">¶</a>
======================================================================================================================================

Python based ETL (Extract Transform Load) framework geared towards BI databases in particular. The goal of the project is to create reusable objects with typical technical transformations used in loading dimension tables.

Configuration Files<a href="#configuration-files" class="headerlink" title="Permalink to this headline">¶</a>
-------------------------------------------------------------------------------------------------------------

<table>
<colgroup>
<col width="33%" />
<col width="67%" />
</colgroup>
<thead>
<tr class="header">
<th>File</th>
<th>Contents</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><a href="config_ini.md" class="reference internal"><span class="doc">config.ini</span></a></td>
<td>This is the main configuration file for the bi_etl module. By default the module will look for the file in your user directory.</td>
</tr>
</tbody>
</table>

To configure the bi\_etl system you **must** setup <a href="config_ini.md" class="reference internal"><span class="doc">config.ini</span></a>

Sequence of an ETL Task<a href="#sequence-of-an-etl-task" class="headerlink" title="Permalink to this headline">¶</a>
---------------------------------------------------------------------------------------------------------------------

The definition of an ETL Task will be a python class inheriting from <a href="bi_etl.scheduler.task.md#bi_etl.scheduler.task.ETLTask" class="reference internal" title="bi_etl.scheduler.task.ETLTask"><code class="xref py py-class docutils literal">bi_etl.scheduler.task.ETLTask</code></a>. This documentation will henceforth refer to that class as simply `ETLTask`.

To run a task you use <a href="bi_etl.scheduler.task.md#bi_etl.scheduler.task.run_task" class="reference internal" title="bi_etl.scheduler.task.run_task"><code class="xref py py-func docutils literal">bi_etl.scheduler.task.run_task()</code></a>. When `run_task` is called it is given a module name. It will:

1.  Load the configuration file using <a href="bi_etl.bi_config_parser.md#bi_etl.bi_config_parser.BIConfigParser" class="reference internal" title="bi_etl.bi_config_parser.BIConfigParser"><code class="xref py py-class docutils literal">bi_etl.bi_config_parser.BIConfigParser</code></a>.

2.  Setup a file based log using task\_name via `config.set_dated_log_file_name()` using the module name passed into run\_task.

3.  Search for that a module named task\_name in the `PYTHONPATH`.

    -   It looks for the module under the package (folder) `etl_jobs`. For example `run_task('my_table')` would match *any* of:

        > -   `etl_jobs.my_table`
        > -   `etl_jobs.foo.my_table`
        > -   `etl_jobs.foo.bar.my_table`
        > -   `etl_jobs.not_my_table` (which might be a problem)

4. After finding the module, look for a class based on `ETLTask` in that module. **By default it will fail if there is more than one such class.** You can add an optional parameter `class_name` to the `run_task` function to have it use a specific class and thus not fail if there is more than one.

1.  Start the `run` method of `ETLTask`. This a standard framework method. It will:
    1.  Initialize the task statistics (start times, etc.)
    2.  Call the <a href="bi_etl.scheduler.task.md#bi_etl.scheduler.task.ETLTask.init" class="reference internal" title="bi_etl.scheduler.task.ETLTask.init"><code class="xref py py-meth docutils literal">init</code></a> method that you can override in your class.
    3.  Call the <a href="bi_etl.scheduler.task.md#bi_etl.scheduler.task.ETLTask.load" class="reference internal" title="bi_etl.scheduler.task.ETLTask.load"><code class="xref py py-meth docutils literal">load</code></a> method that you must override in your class.
    4.  Call the <a href="bi_etl.scheduler.task.md#bi_etl.scheduler.task.ETLTask.finish" class="reference internal" title="bi_etl.scheduler.task.ETLTask.finish"><code class="xref py py-meth docutils literal">finish</code></a> method that you can override in your class.
    5.  Finalize the statistics
    6.  Send an e-mail on failure (see configuration file section `SMTP` item `distro_list`)

Source / Target Components<a href="#source-target-components" class="headerlink" title="Permalink to this headline">¶</a>
-------------------------------------------------------------------------------------------------------------------------

Within a task you will use source / target components to extract and load the data.

<table style="width:207%;">
<colgroup>
<col width="43%" />
<col width="60%" />
<col width="60%" />
<col width="44%" />
</colgroup>
<thead>
<tr class="header">
<th>Component Class</th>
<th>Usable as Source</th>
<th>Usable as Target</th>
<th>Notes</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><a href="bi_etl.components.csvreader.md#bi_etl.components.csvreader.CSVReader" class="reference internal" title="bi_etl.components.csvreader.CSVReader"><code class="xref py py-class docutils literal">CSVReader</code></a></td>
<td>Yes</td>
<td>No</td>
<td>Can read <em>any</em> delimited file (see ‘’delimiter’’ parameter) It is based on the Python csv module. See <a href="https://docs.python.org/3.5/library/csv.md" class="uri" class="reference external">https://docs.python.org/3.5/library/csv.md</a></td>
</tr>
<tr class="even">
<td><a href="bi_etl.components.xlsx_reader.md#bi_etl.components.xlsx_reader.XLSXReader" class="reference internal" title="bi_etl.components.xlsx_reader.XLSXReader"><code class="xref py py-class docutils literal">XLSXReader</code></a></td>
<td>Yes</td>
<td>No</td>
<td>Reads from Excel files; although only those in xlsx format.</td>
</tr>
<tr class="odd">
<td><a href="bi_etl.components.sqlquery.md#bi_etl.components.sqlquery.SQLQuery" class="reference internal" title="bi_etl.components.sqlquery.SQLQuery"><code class="xref py py-class docutils literal">SQLQuery</code></a></td>
<td>Yes</td>
<td>No</td>
<td>Reads from the result of a SQL query.</td>
</tr>
<tr class="even">
<td><a href="bi_etl.components.readonlytable.md#bi_etl.components.readonlytable.ReadOnlyTable" class="reference internal" title="bi_etl.components.readonlytable.ReadOnlyTable"><code class="xref py py-class docutils literal">ReadOnlyTable</code></a></td>
<td>Yes</td>
<td>No</td>
<td>Useful when reading all columns from a database table or view. Rows can be filtered using the where method.</td>
</tr>
<tr class="odd">
<td><a href="bi_etl.components.table.md#bi_etl.components.table.Table" class="reference internal" title="bi_etl.components.table.Table"><code class="xref py py-class docutils literal">Table</code></a></td>
<td>Yes</td>
<td>Yes</td>
<td>Inherits from ReadOnlyTable. Added features: * lookups, optional data cache * insert, update, delete and upsert * delete_not_in_set, and delete_not_processed * logically_delete_not_in_set, and not_processed * update_not_in_set, update_not_processed</td>
</tr>
<tr class="even">
<td><code class="xref py py-class docutils literal">Hst_Table</code></td>
<td>Yes</td>
<td>Yes</td>
<td>Inherits from Table. Adds ability to correctly load versioned tables. Supports both type 2 dimensions and date versioned warehouse tables. Also has cleanup_spurious_versions method to remove version rows that are not needed (due to being redundant).</td>
</tr>
<tr class="odd">
<td><a href="bi_etl.components.data_analyzer.md#bi_etl.components.data_analyzer.DataAnalyzer" class="reference internal" title="bi_etl.components.data_analyzer.DataAnalyzer"><code class="xref py py-class docutils literal">DataAnalyzer</code></a></td>
<td>No</td>
<td>Yes</td>
<td>Produces a summary of the columns in the data rows passed to the <a href="bi_etl.components.data_analyzer.md#bi_etl.components.data_analyzer.DataAnalyzer.analyze_row" class="reference internal" title="bi_etl.components.data_analyzer.DataAnalyzer.analyze_row"><code class="xref py py-meth docutils literal">analyze_row()</code></a> method. The output currently goes to the task log.</td>
</tr>
</tbody>
</table>

Note

There are not yet components for *writing* delimited files or Excel files.

However, csv.DictWriter works well for writing delimited files. The added statistics tracking features of an ETLComponent do not seem critical.

openpyxl can be used for directly writing Excel files.

### Functionality common to all sources<a href="#functionality-common-to-all-sources" class="headerlink" title="Permalink to this headline">¶</a>

All source components share the following common functionality.

The source can output progress messages to the task log every X seconds. This defaults to every 10 seconds with the message format being `"{logical_name} current row # {row_number:,}"`. See parameters `progress_frequency`, and `progress_message`.

They can limit the number of rows to process. See parameter `max_rows` (Default None)

They can print a debug trace of all rows processed. See class property `trace_data` (default False).

They can print a debug trace of the first row processed. See parameter and class property `log_first_row` (default False).

They track statistics on how long it took to retrieve the first row and all rows. The read timer is starts and stops as rows are passed onto other code, so it should represent just the read elapsed time.

Transformations<a href="#transformations" class="headerlink" title="Permalink to this headline">¶</a>
-----------------------------------------------------------------------------------------------------

### Explicit in loop<a href="#explicit-in-loop" class="headerlink" title="Permalink to this headline">¶</a>

Source values can be transformed with an explicit assignment to the row.

    for row in source_table:
       row['my_column'] = str2decimal( row['my_column'] )
       ## Do something with the row

### Explicit in load methods<a href="#explicit-in-load-methods" class="headerlink" title="Permalink to this headline">¶</a>

Source values can also be transformed in the load method (upsert, insert, or update) using the `source_transformations` parameter.

The cleanest way to build explicit transformations is to use the `Transformation` and `Conversion` helper classes. In this case Transformation is the mapping of a column name to a conversion routine that changes the input value to a new output value. **This the is preferred way of specifing transformations.**

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

`source_transformations` can be a list of tuples. However, the parenthesis get hard to manage if you try to build the entire thing in a single static assignment.

    ## Using a list to hold the transforms
    my_source_transformations = [                    ## Tuple format alternatives
       ( 'my_column1', str2decimal ),                ## Simple name mapped to function
       ( 'my_column2', ( str2decimal ) ),            ## Name mapped to tuple with just function
       ( 'date_as_str', (nullif, ('00/00/0000')) )   ## Name mapped to tuple with function and arguments (as tuple)
       ( 'date2', Conversion(nullif, '00/00/0000') ) ## Name mapped to Conversion class
       ]

    for row in source_table:
       target_table.upsert(row,  source_transformations= my_source_transformations)

Instead you can make it a bit easier to read by building the list an item at a time. This code should be run only once before the loop so performance isn’t really an issue. However using the `Conversion` class would make this code easier to read.

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

`source_transformations` can also be a dict but you loose control of the ordering of transforms.

    ## Using a dict to hold the transforms
    my_source_transformations = {                ## Dict value alternatives
       'my_column1': str2decimal,                ## Simple name mapped to function
       'my_column2': ( str2decimal ),            ## Name mapped to tuple with just function
       'date_as_str': (nullif, ('00/00/0000'))   ## Name mapped to tuple with function and arguments (as tuple)
       'date2': Conversion(nullif, '00/00/0000') ## Name mapped to Conversion class
       }

    for row in source_table:
       target_table.upsert(row,  source_transformations= my_source_transformations)

### Implicit<a href="#implicit" class="headerlink" title="Permalink to this headline">¶</a>

If the source and target datatypes are not the same, and no explicit transformation is applied, the bi\_etl framework will attempt to convert the value for you. It will generate Exceptions if it is unable to convert a value.

Dates require special care. The attribute <a href="bi_etl.components.table.md#bi_etl.components.table.Table.default_date_format" class="reference internal" title="bi_etl.components.table.Table.default_date_format"><code class="xref py py-attr docutils literal">bi_etl.components.table.Table.default_date_format</code></a> has a reasonable default value (for US based dates) and can be used to do this implicit conversion. However, dates like 11/03/2015 and 03/11/2015 are ambiguous and will load successfully despite being potentially wrong.

Coding Standards Used<a href="#coding-standards-used" class="headerlink" title="Permalink to this headline">¶</a>
-----------------------------------------------------------------------------------------------------------------

Please see <a href="coding_standards.md" class="reference internal"><span class="doc">Coding Standards</span></a>

Examples<a href="#examples" class="headerlink" title="Permalink to this headline">¶</a>
---------------------------------------------------------------------------------------

### Example task definition - Simple Table Truncate and Load<a href="#example-task-definition-simple-table-truncate-and-load" class="headerlink" title="Permalink to this headline">¶</a>

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

If you do need to commit in smaller batches you can add these lines inside the `for row in source` file loop

    if source_file.rows_read % 10000 == 0:
       source_file.commit()

### Example task definition - Simple Table Load with Update/Insert<a href="#example-task-definition-simple-table-load-with-update-insert" class="headerlink" title="Permalink to this headline">¶</a>

This example will start and end the same as the Truncate and Load example. So the code block below is only the contents of the two `with` blocks.

    with Table...
          ## <-- Removed truncate from here

          ## Start looping through source data
          for row in source_file:
              target_tbl.upsert(row)  ### <-- changed to upsert instead of insert

          ## Issue a commit at the end
          target_table.commit()

          self.log.info("Done")

In summary: 1) We removed the call to the `truncate` command 2) We changed the `insert` call to an <a href="bi_etl.components.table.md#bi_etl.components.table.Table.upsert" class="reference internal" title="bi_etl.components.table.Table.upsert"><code class="xref py py-meth docutils literal">upsert()</code></a> call.

The <a href="bi_etl.components.table.md#bi_etl.components.table.Table.upsert" class="reference internal" title="bi_etl.components.table.Table.upsert"><code class="xref py py-meth docutils literal">upsert()</code></a> command will look for an existing row in the target table (using the primary key lookup if no alternate lookup name is provided). If no existing row is found, an insert will be generated. If an existing row is found, it will be compared to the row passed in. If changes are found, an update will be generated.

### Example task definition - Simple Dimension Load<a href="#example-task-definition-simple-dimension-load" class="headerlink" title="Permalink to this headline">¶</a>

In this example we add in features to 1) Generate a surrogate key 2) Lookup using the natural key (not the primar key) 3) Logically delete rows that were not in the source

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

Modules APIs<a href="#modules-apis" class="headerlink" title="Permalink to this headline">¶</a>
-----------------------------------------------------------------------------------------------

-   <a href="source_transformations.md" class="reference internal">Transformations</a>
    -   <a href="source_transformations.md#explicit-in-loop" class="reference internal">Explicit in loop</a>
    -   <a href="source_transformations.md#explicit-in-load-methods" class="reference internal">Explicit in load methods</a>
    -   <a href="source_transformations.md#implicit" class="reference internal">Implicit</a>
-   <a href="bi_etl.md" class="reference internal">bi_etl package</a>
    -   <a href="bi_etl.md#subpackages" class="reference internal">Subpackages</a>
        -   <a href="bi_etl.components.md" class="reference internal">bi_etl.components package</a>
            -   <a href="bi_etl.components.md#subpackages" class="reference internal">Subpackages</a>
                -   <a href="bi_etl.components.row_package.md" class="reference internal">bi_etl.components.row package</a>
            -   <a href="bi_etl.components.md#submodules" class="reference internal">Submodules</a>
                -   <a href="bi_etl.components.csvreader.md" class="reference internal">bi_etl.components.csvreader module</a>
                -   <a href="bi_etl.components.data_analyzer.md" class="reference internal">bi_etl.components.data_analyzer module</a>
                -   <a href="bi_etl.components.etlcomponent.md" class="reference internal">bi_etl.components.etlcomponent module</a>
                -   <a href="bi_etl.components.hst_table.md" class="reference internal">bi_etl.components.hst_table module</a>
                -   <a href="bi_etl.components.readonlytable.md" class="reference internal">bi_etl.components.readonlytable module</a>
                -   <a href="bi_etl.components.row_package.md" class="reference internal">bi_etl.components.row package</a>
                -   <a href="bi_etl.components.sqlquery.md" class="reference internal">bi_etl.components.sqlquery module</a>
                -   <a href="bi_etl.components.table.md" class="reference internal">bi_etl.components.table module</a>
                -   <a href="bi_etl.components.xlsx_reader.md" class="reference internal">bi_etl.components.xlsx_reader module</a>
            -   <a href="bi_etl.components.md#module-bi_etl.components" class="reference internal">Module contents</a>
        -   <a href="bi_etl.database.md" class="reference internal">bi_etl.database package</a>
            -   <a href="bi_etl.database.md#submodules" class="reference internal">Submodules</a>
                -   <a href="bi_etl.database.connect.md" class="reference internal">bi_etl.database.connect module</a>
                -   <a href="bi_etl.database.database_metadata.md" class="reference internal">bi_etl.database.database_metadata module</a>
                -   <a href="bi_etl.database.mock_connect.md" class="reference internal">bi_etl.database.mock_connect module</a>
                -   <a href="bi_etl.database.mock_database_metadata.md" class="reference internal">bi_etl.database.mock_database_metadata module</a>
            -   <a href="bi_etl.database.md#module-bi_etl.database" class="reference internal">Module contents</a>
        -   <a href="bi_etl.exceptions.md" class="reference internal">bi_etl.exceptions package</a>
            -   <a href="bi_etl.exceptions.md#module-bi_etl.exceptions" class="reference internal">Module contents</a>
        -   <a href="bi_etl.informatica.md" class="reference internal">bi_etl.informatica package</a>
            -   <a href="bi_etl.informatica.md#submodules" class="reference internal">Submodules</a>
                -   <a href="bi_etl.informatica.exceptions.md" class="reference internal">bi_etl.informatica.exceptions module</a>
                -   <a href="bi_etl.informatica.pmcmd.md" class="reference internal">bi_etl.informatica.pmcmd module</a>
                -   <a href="bi_etl.informatica.pmcmd_task.md" class="reference internal">bi_etl.informatica.pmcmd_task module</a>
                -   <a href="bi_etl.informatica.pmrep.md" class="reference internal">bi_etl.informatica.pmrep module</a>
            -   <a href="bi_etl.informatica.md#module-bi_etl.informatica" class="reference internal">Module contents</a>
        -   <a href="bi_etl.lookups.md" class="reference internal">bi_etl.lookups package</a>
            -   <a href="bi_etl.lookups.md#submodules" class="reference internal">Submodules</a>
                -   <a href="bi_etl.lookups.autodisk_lookup.md" class="reference internal">bi_etl.lookups.autodisk_lookup module</a>
                -   <a href="bi_etl.lookups.autodisk_range_lookup.md" class="reference internal">bi_etl.lookups.autodisk_range_lookup module</a>
                -   <a href="bi_etl.lookups.disk_lookup.md" class="reference internal">bi_etl.lookups.disk_lookup module</a>
                -   <a href="bi_etl.lookups.disk_range_lookup.md" class="reference internal">bi_etl.lookups.disk_range_lookup module</a>
                -   <a href="bi_etl.lookups.lookup.md" class="reference internal">bi_etl.lookups.lookup module</a>
                -   <a href="bi_etl.lookups.range_lookup.md" class="reference internal">bi_etl.lookups.range_lookup module</a>
                -   <a href="bi_etl.lookups.sqlite_lookup.md" class="reference internal">bi_etl.lookups.sqlite_lookup module</a>
                -   <a href="bi_etl.lookups.sqlite_range_lookup.md" class="reference internal">bi_etl.lookups.sqlite_range_lookup module</a>
            -   <a href="bi_etl.lookups.md#module-bi_etl.lookups" class="reference internal">Module contents</a>
        -   <a href="bi_etl.notifiers.md" class="reference internal">bi_etl.notifiers package</a>
            -   <a href="bi_etl.notifiers.md#submodules" class="reference internal">Submodules</a>
                -   <a href="bi_etl.notifiers.email.md" class="reference internal">bi_etl.notifiers.email module</a>
                -   <a href="bi_etl.notifiers.notifier.md" class="reference internal">bi_etl.notifiers.notifier module</a>
            -   <a href="bi_etl.notifiers.md#module-bi_etl.notifiers" class="reference internal">Module contents</a>
        -   <a href="bi_etl.parameters.md" class="reference internal">bi_etl.parameters package</a>
            -   <a href="bi_etl.parameters.md#submodules" class="reference internal">Submodules</a>
                -   <a href="bi_etl.parameters.file_parameter.md" class="reference internal">bi_etl.parameters.file_parameter module</a>
            -   <a href="bi_etl.parameters.md#module-bi_etl.parameters" class="reference internal">Module contents</a>
        -   <a href="bi_etl.scheduler.md" class="reference internal">bi_etl.scheduler package</a>
            -   <a href="bi_etl.scheduler.md#subpackages" class="reference internal">Subpackages</a>
                -   <a href="bi_etl.scheduler.scheduler_etl_jobs.md" class="reference internal">bi_etl.scheduler.scheduler_etl_jobs package</a>
            -   <a href="bi_etl.scheduler.md#submodules" class="reference internal">Submodules</a>
                -   <a href="bi_etl.scheduler.dependent_reasons.md" class="reference internal">bi_etl.scheduler.dependent_reasons module</a>
                -   <a href="bi_etl.scheduler.etl_task_status_cd.md" class="reference internal">bi_etl.scheduler.etl_task_status_cd module</a>
                -   <a href="bi_etl.scheduler.exceptions.md" class="reference internal">bi_etl.scheduler.exceptions module</a>
                -   <a href="bi_etl.scheduler.messages.md" class="reference internal">bi_etl.scheduler.messages module</a>
                -   <a href="bi_etl.scheduler.models.md" class="reference internal">bi_etl.scheduler.models module</a>
                -   <a href="bi_etl.scheduler.queue_io.md" class="reference internal">bi_etl.scheduler.queue_io module</a>
                -   <a href="bi_etl.scheduler.scheduler.md" class="reference internal">bi_etl.scheduler.scheduler module</a>
                -   <a href="bi_etl.scheduler.scheduler_interface.md" class="reference internal">bi_etl.scheduler.scheduler_interface module</a>
                -   <a href="bi_etl.scheduler.sdtout_queue.md" class="reference internal">bi_etl.scheduler.sdtout_queue module</a>
                -   <a href="bi_etl.scheduler.special_tasks.md" class="reference internal">bi_etl.scheduler.special_tasks module</a>
                -   <a href="bi_etl.scheduler.status.md" class="reference internal">bi_etl.scheduler.status module</a>
                -   <a href="bi_etl.scheduler.task.md" class="reference internal">bi_etl.scheduler.task module</a>
            -   <a href="bi_etl.scheduler.md#module-bi_etl.scheduler" class="reference internal">Module contents</a>
        -   <a href="bi_etl.tests.md" class="reference internal">bi_etl.tests package</a>
            -   <a href="bi_etl.tests.md#subpackages" class="reference internal">Subpackages</a>
                -   <a href="bi_etl.tests.etl_jobs.md" class="reference internal">bi_etl.tests.etl_jobs package</a>
            -   <a href="bi_etl.tests.md#submodules" class="reference internal">Submodules</a>
                -   <a href="bi_etl.tests.debug_sa_objects.md" class="reference internal">bi_etl.tests.debug_sa_objects module</a>
                -   <a href="bi_etl.tests.dummy_etl_component.md" class="reference internal">bi_etl.tests.dummy_etl_component module</a>
                -   <a href="bi_etl.tests.mock_metadata.md" class="reference internal">bi_etl.tests.mock_metadata module</a>
                -   <a href="bi_etl.tests.test_autodisk_lookup.md" class="reference internal">bi_etl.tests.test_autodisk_lookup module</a>
                -   <a href="bi_etl.tests.test_autodisk_range_lookup.md" class="reference internal">bi_etl.tests.test_autodisk_range_lookup module</a>
                -   <a href="bi_etl.tests.test_bi_config_parser.md" class="reference internal">bi_etl.tests.test_bi_config_parser module</a>
                -   <a href="bi_etl.tests.test_csvreader.md" class="reference internal">bi_etl.tests.test_csvreader module</a>
                -   <a href="bi_etl.tests.test_dict_to_str.md" class="reference internal">bi_etl.tests.test_dict_to_str module</a>
                -   <a href="bi_etl.tests.test_disk_lookup.md" class="reference internal">bi_etl.tests.test_disk_lookup module</a>
                -   <a href="bi_etl.tests.test_disk_range_lookup.md" class="reference internal">bi_etl.tests.test_disk_range_lookup module</a>
                -   <a href="bi_etl.tests.test_hst_table.md" class="reference internal">bi_etl.tests.test_hst_table module</a>
                -   <a href="bi_etl.tests.test_lookup.md" class="reference internal">bi_etl.tests.test_lookup module</a>
                -   <a href="bi_etl.tests.test_range_lookup.md" class="reference internal">bi_etl.tests.test_range_lookup module</a>
                -   <a href="bi_etl.tests.test_row.md" class="reference internal">bi_etl.tests.test_row module</a>
                -   <a href="bi_etl.tests.test_row_case_insensitive.md" class="reference internal">bi_etl.tests.test_row_case_insensitive module</a>
                -   <a href="bi_etl.tests.test_scheduler.md" class="reference internal">bi_etl.tests.test_scheduler module</a>
                -   <a href="bi_etl.tests.test_scheduler_live.md" class="reference internal">bi_etl.tests.test_scheduler_live module</a>
                -   <a href="bi_etl.tests.test_statistics.md" class="reference internal">bi_etl.tests.test_statistics module</a>
                -   <a href="bi_etl.tests.test_table.md" class="reference internal">bi_etl.tests.test_table module</a>
                -   <a href="bi_etl.tests.test_task.md" class="reference internal">bi_etl.tests.test_task module</a>
            -   <a href="bi_etl.tests.md#module-bi_etl.tests" class="reference internal">Module contents</a>
        -   <a href="bi_etl.utility.md" class="reference internal">bi_etl.utility package</a>
            -   <a href="bi_etl.utility.md#submodules" class="reference internal">Submodules</a>
                -   <a href="bi_etl.utility.ask.md" class="reference internal">bi_etl.utility.ask module</a>
            -   <a href="bi_etl.utility.md#module-bi_etl.utility" class="reference internal">Module contents</a>
    -   <a href="bi_etl.md#submodules" class="reference internal">Submodules</a>
        -   <a href="bi_etl.bi_config_parser.md" class="reference internal">bi_etl.bi_config_parser module</a>
        -   <a href="bi_etl.conversions.md" class="reference internal">bi_etl.conversions module</a>
        -   <a href="bi_etl.memory_size.md" class="reference internal">bi_etl.memory_size module</a>
        -   <a href="bi_etl.statement_queue.md" class="reference internal">bi_etl.statement_queue module</a>
        -   <a href="bi_etl.statistics.md" class="reference internal">bi_etl.statistics module</a>
        -   <a href="bi_etl.timer.md" class="reference internal">bi_etl.timer module</a>
    -   <a href="bi_etl.md#module-bi_etl" class="reference internal">Module contents</a>

Indices and tables<a href="#indices-and-tables" class="headerlink" title="Permalink to this headline">¶</a>
-----------------------------------------------------------------------------------------------------------

-   <a href="genindex.md" class="reference internal"><span class="std std-ref">Index</span></a>
-   <a href="py-modindex.md" class="reference internal"><span class="std std-ref">Module Index</span></a>
-   <a href="search.md" class="reference internal"><span class="std std-ref">Search Page</span></a>

### [Table Of Contents](#)

-   <a href="#" class="reference internal">BI ETL Python Framework (bi_etl)</a>
    -   <a href="#configuration-files" class="reference internal">Configuration Files</a>
    -   <a href="#sequence-of-an-etl-task" class="reference internal">Sequence of an ETL Task</a>
    -   <a href="#source-target-components" class="reference internal">Source / Target Components</a>
        -   <a href="#functionality-common-to-all-sources" class="reference internal">Functionality common to all sources</a>
    -   <a href="#transformations" class="reference internal">Transformations</a>
        -   <a href="#explicit-in-loop" class="reference internal">Explicit in loop</a>
        -   <a href="#explicit-in-load-methods" class="reference internal">Explicit in load methods</a>
        -   <a href="#implicit" class="reference internal">Implicit</a>
    -   <a href="#coding-standards-used" class="reference internal">Coding Standards Used</a>
    -   <a href="#examples" class="reference internal">Examples</a>
        -   <a href="#example-task-definition-simple-table-truncate-and-load" class="reference internal">Example task definition - Simple Table Truncate and Load</a>
        -   <a href="#example-task-definition-simple-table-load-with-update-insert" class="reference internal">Example task definition - Simple Table Load with Update/Insert</a>
        -   <a href="#example-task-definition-simple-dimension-load" class="reference internal">Example task definition - Simple Dimension Load</a>
    -   <a href="#modules-apis" class="reference internal">Modules APIs</a>
    -   <a href="#indices-and-tables" class="reference internal">Indices and tables</a>

#### Next topic

[config.ini](config_ini.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](config_ini.md "config.ini") |
-   [bi\_etl 0.5.3 documentation](#) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
