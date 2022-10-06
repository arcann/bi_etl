################################
BI ETL Python Framework (bi_etl)
################################

Python based data engineering framework. The bi_etl framework is geared towards BI databases in particular.
The goal of the project is to create reusable objects with typical technical transformations
used in loading dimension tables.

For simple staging of data with little to no transformation, bi_etl helps with some
abstraction layers over the database bulk loader tools.

For dimension loading bi_etl offers components that perform SCD type 1 and type 2 upsert (update / insert)
operations. Unlike other tools, bi_etl automates as much of the "technical" transformation as possible. Your code
performs the main "business" transformation in SQL or Python code without worrying about the upsert logic. The
bi_etl component then accepts those records, matches source column names to target column names, checks for existing
rows, and either updates them (type 1 or 2 updates), updates the metadata columns (e.g. date of last update), or
inserts a new row.

For configuration of the bi_etl framework itself as well as, optionally, your ETL jobs
please see `config_wrangler <https://bietl.dev/config_wrangler/>`_

This project on PyPI: `bi-etl <https://pypi.org/project/bi-etl/>`_

*************************
Guiding Design Principles
*************************

1. Don't Repeat Yourself (DRY).

   - The source or target of an ETL owns the metadata (list of columns and data types).
     The ETL generally has no reason to define those again unless the ETL requires a change.

   - If a datatype must be changed, only that one column's new type should be specified.

   - If source & target column names differ, only the column names that differ should be specified
     as mapping to a new name. All column names that match should flow through with no extra code.
     With bi_etl we map input columns to output columns by renaming any input columns that do not
     match to the output column name
     (not renamed in the input system, but inside the ETL task itself).

2. Data Quality is the top priority

   Data quality is more important than performance.  For example, the process should fail before truncating data
   contents (e.g. loading 6 characters into a 5 character field) even if that means sacrificing some load performance.

3. Give helpful error messages.

4. Make it as easy as possible to create re-usable modules.

5. SQL is a very powerful transformation language. The data pipelines that support SQL as the transformation language
   should be supported.

    - **Extract Load Transform (ELT)** - Data is loaded with no transformation (or as little as possible) into the BI database
      in a staging area. SQL jobs are then used to transform the data for both dimension and fact tables. For dimensions,
      especially type-2 slowly changing dimensions, the technical transformations in the upsert (update or insert) logic
      is handled in re-usable Python classes that are part of the bi_etl framework.

    - **Transform Extract Load (TEL)** - The data is transformed using the source systems SQL engine. It then follows a
      similar pattern to the ELT model. This model is not often used since it puts a lot of computational strain on the
      source system.  However, if the transformation yields a much smaller data volume (e.g. aggregation) then it might
      be more efficient than extracting & loading all the details.

    - **Extract Transform Load (ETL)** - ETL, the most traditional approach does **not** use SQL for the transformation.
      This framework does support ETL with transformations done in the Python code. However, Python transformations are
      often slower than SQL transformations. Python transformations are also accessible to a smaller audience than SQL
      transformations are.

6. As much as possible, all sources & targets should behave the same.  For example, replacing a CSV source with an
   Excel source (with the same data content) should not require changing any code other than the source declaration.
   The bi_etl framework attempts to provide a common interface to all source and target components.

   There are, of course, places where we need to provide additional functionality to specific components. For example,
   an Excel source can have multiple worksheets, so that component provides unique functionality for switching between
   worksheets.

   There are also features of certain targets that don't make sense to support. For example, CSV targets support
   insert_row but not upsert (update / insert). We have not seen a use-case for upserts or even updates on a CSV target.

********
Features
********

Sources supported:
~~~~~~~~~~~~~~~~~~

* Database tables
* Database SQL Queries
* Delimited text files
* Excel files
* W3C web logs

Targets supported:
~~~~~~~~~~~~~~~~~~

* Database tables
  -  Works with any database supported by `SQL Alchemy <https://www.sqlalchemy.org/>`_
* Delimited text files
* Excel files


Load types supported:
~~~~~~~~~~~~~~~~~~~~~

* Truncate
* Insert
* Upsert (Update if row with matching key is present, else insert)

  - Works best in conjunction with a Lookup which is an indexed RAM / Disk storage of the existing rows
  - Optional addition of a surrogate key (`SCD type 1 <https://en.wikipedia.org/wiki/Slowly_changing_dimension#Type_1:_overwrite>`_)

* Upsert with `SCD Type 2 versioning <https://en.wikipedia.org/wiki/Slowly_changing_dimension#Type_2:_add_new_row>`_

  - Generating both type 2 and type 1 surrogate keys if desired.

* Bulk loading the results of any of the methods above

Transformations supported:
~~~~~~~~~~~~~~~~~~~~~~~~~~

Anything you can do in SQL or in Python -- including with the hundreds of thousands of Python libraries.

****************
Areas to Work on
****************

* Scheduling.

  An event based job sequencing tool exists. It does not yet support time based triggers.

  It was also designed for an environment where the web interface or event triggering server may
  not be able to communicate directly to the ETL execution server. So all communication is done
  via the database.

* Performance.

  There is a limit to how much performance is possible with Python. However, we have found that
  Python makes it easier to write "smarter" loads that limit the scope of the load to gain
  performance rather than quickly hammering in the data with few quality checks the way some ETL
  tools do it.

  Multi-threaded insert/updates appear to provide some good benefit on certain database platforms
  (e.g. SQL Server).

*******************
Details
*******************

.. toctree::
    :maxdepth: 1

    etl_task
    components
    source_transformations
    examples
    config_ini
    documentation_standards
    bi_etl

******************
Indices and tables
******************

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

------------

.. [*] Beetle icon from <a href="https://www.freeiconspng.com/img/28142">Beetle For Windows Icons</a>