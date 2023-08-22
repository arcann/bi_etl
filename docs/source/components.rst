**************************
Source / Target Components
**************************

Within a task you will use source / target components to extract and load the data.

.. contents:: Components


CSVReader
---------

Documentation Link: :class:`~bi_etl.components.csvreader.CSVReader`

Can read *any* delimited file (see ''delimiter'' parameter)
It is based on the Python csv module.
See https://docs.python.org/3.5/library/csv.html

Usable as Source: Yes

Usable as Target: No

CSVWriter
------------------------------------------------

Documentation Link: :class:`~bi_etl.components.csv_writer.CSVWriter`

Can write *any* delimited file (see ''delimiter'' parameter)
It is based on the Python csv module.
See https://docs.python.org/3.5/library/csv.html

Usable as Source: Yes, but does not support updates so use CSVReader instead

Usable as Target: Yes

XLSXReader
--------------------------------------------------

Documentation Link: :class:`~bi_etl.components.xlsx_reader.XLSXReader`

Reads from Excel files; although only those in xlsx format.

Usable as Source: Yes
Usable as Target: No

XLSXWriter
--------------------------------------------------

Documentation Link: :class:`~bi_etl.components.xlsx_writer.XLSXWriter`

Writes to Excel xlsx files (can also read/update files).

Usable as Source: Yes, including for updates

Usable as Target: Yes

SQLQuery
--------------------------------------------------

Documentation Link: :class:`~bi_etl.components.sqlquery.SQLQuery`

Reads from the result of a SQL query.

Usable as Source: Yes

Usable as Target: No

ReadOnlyTable
-------------------------------------------------------

Useful when reading all columns from a database table or view.
Rows can be filtered using the where method.

Usable as Source: Yes

Usable as Target: No

Table
-------------------------------------------------------

Documentation Link: :class:`~bi_etl.components.table.Table`

Inherits from ReadOnlyTable. Added features:
    * lookups, optional data cache
    * insert, update, delete and upsert
    * delete_not_in_set, and delete_not_processed
    * logically_delete_not_in_set, and not_processed
    * update_not_in_set, update_not_processed

Usable as Source: Yes

Usable as Target: Yes

HistoryTable
-------------------------------------------------------

Documentation Link: :class:`~bi_etl.components.hst_table.HistoryTable`

Inherits from **Table**. Adds the ability to correctly load versioned
tables. Supports both type 2 dimensions and date versioned
warehouse tables. Also has cleanup_versions method
to remove version rows that are not needed (due to being
redundant).

Usable as Source: Yes

Usable as Target: Yes


HistoryTableSourceBased
--------------------------------------------------------------------------

Documentation Link: :class:`~bi_etl.components.hst_table_source_based.HistoryTableSourceBased`

Inherits from **HistoryTable**. Changes the versioning
processing so that the source can restate the version
history as needed. Versions are not removed from the
target, but rather the values are changed to match the
active source version at that time.  This prevents "breaking"
any fact tables that refer to that version.

Usable as Source: Yes

Usable as Target: Yes


PyArrowDatasetReader
--------------------------------------------------------------------------

Documentation Link: :class:`~bi_etl.components.pyarrow_dataset_reader.PyArrowDatasetReader`

PyArrowDatasetReader will read rows using pyarrow.dataset functionality but presented
using the common bi_etl interface including Row objects.

Usable as Source: Yes

Usable as Target: No

W3CReader
--------------------------------------------------------------------------

Documentation Link: :class:`~bi_etl.components.w3c_reader.W3CReader`

Reads W3C based log files (web server logs).

Usable as Source: Yes

Usable as Target: No


DataAnalyzer
--------------------------------------------------------------------------

Documentation Link: :class:`~bi_etl.components.data_analyzer.DataAnalyzer`

Produces a summary of the columns in the data rows passed to the
:meth:`~bi_etl.components.data_analyzer.DataAnalyzer.analyze_row`
method.
The output currently goes to the task log.

Usable as Source: No

Usable as Target: Yes


Functionality common to all sources
-----------------------------------

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
