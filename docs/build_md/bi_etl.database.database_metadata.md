### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.database.mock_connect.md "bi_etl.database.mock_connect module") |
-   [previous](bi_etl.database.connect.md "bi_etl.database.connect module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.database package](bi_etl.database.md) »

<span id="bi-etl-database-database-metadata-module"></span>
bi\_etl.database.database\_metadata module<a href="#module-bi_etl.database.database_metadata" class="headerlink" title="Permalink to this headline">¶</a>
=========================================================================================================================================================

Created on Dec 23, 2015

@author: woodd

 *class* `bi_etl.database.database_metadata.``DatabaseMetadata`<span class="sig-paren">(</span>*bind=None*, *reflect=False*, *schema=None*, *quote\_schema=None*, *naming\_convention=immutabledict({'ix': 'ix\_%(column\_0\_label)s'})*, *info=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/database/database_metadata.md#DatabaseMetadata" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.database.database_metadata.DatabaseMetadata" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: `sqlalchemy.sql.schema.MetaData`

A light wrapper over sqlalchemy.schema.MetaData

 `append_ddl_listener`<span class="sig-paren">(</span>*event\_name*, *listener*<span class="sig-paren">)</span><a href="#bi_etl.database.database_metadata.DatabaseMetadata.append_ddl_listener" class="headerlink" title="Permalink to this definition">¶</a>  
Append a DDL event listener to this `MetaData`.

<span class="versionmodified">Deprecated since version 0.7: </span>See `DDLEvents`.

 `bind`<a href="#bi_etl.database.database_metadata.DatabaseMetadata.bind" class="headerlink" title="Permalink to this definition">¶</a>  
An `Engine` or `Connection` to which this `MetaData` is bound.

Typically, a `Engine` is assigned to this attribute so that “implicit execution” may be used, or alternatively as a means of providing engine binding information to an ORM `Session` object:

    engine = create_engine("someurl://")
    metadata.bind = engine

See also

<span class="xref std std-ref">dbengine\_implicit</span> - background on “bound metadata”

 `clear`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.database.database_metadata.DatabaseMetadata.clear" class="headerlink" title="Permalink to this definition">¶</a>  
Clear all Table objects from this MetaData.

 `create_all`<span class="sig-paren">(</span>*bind=None*, *tables=None*, *checkfirst=True*<span class="sig-paren">)</span><a href="#bi_etl.database.database_metadata.DatabaseMetadata.create_all" class="headerlink" title="Permalink to this definition">¶</a>  
Create all tables stored in this metadata.

Conditional by default, will not attempt to recreate tables already present in the target database.

|             |                                                                                                                                  |
|-------------|----------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **bind** – A `Connectable` used to access the database; if None, uses the existing bind on this `MetaData`, if any.          
  -   **tables** – Optional list of `Table` objects, which is a subset of the total tables in the `MetaData` (others are ignored).  
  -   **checkfirst** – Defaults to True, don’t issue CREATEs for tables already present in the target database.                     |

 `dispatch` *= &lt;sqlalchemy.event.base.DDLEventsDispatch object&gt;*<a href="#bi_etl.database.database_metadata.DatabaseMetadata.dispatch" class="headerlink" title="Permalink to this definition">¶</a>  

 `drop_all`<span class="sig-paren">(</span>*bind=None*, *tables=None*, *checkfirst=True*<span class="sig-paren">)</span><a href="#bi_etl.database.database_metadata.DatabaseMetadata.drop_all" class="headerlink" title="Permalink to this definition">¶</a>  
Drop all tables stored in this metadata.

Conditional by default, will not attempt to drop tables not present in the target database.

|             |                                                                                                                                  |
|-------------|----------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **bind** – A `Connectable` used to access the database; if None, uses the existing bind on this `MetaData`, if any.          
  -   **tables** – Optional list of `Table` objects, which is a subset of the total tables in the `MetaData` (others are ignored).  
  -   **checkfirst** – Defaults to True, only issue DROPs for tables confirmed to be present in the target database.                |

 `execute`<span class="sig-paren">(</span>*sql*<span class="sig-paren">)</span><a href="_modules/bi_etl/database/database_metadata.md#DatabaseMetadata.execute" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.database.database_metadata.DatabaseMetadata.execute" class="headerlink" title="Permalink to this definition">¶</a>  

 `execute_direct`<span class="sig-paren">(</span>*sql*, *return\_results=False*<span class="sig-paren">)</span><a href="_modules/bi_etl/database/database_metadata.md#DatabaseMetadata.execute_direct" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.database.database_metadata.DatabaseMetadata.execute_direct" class="headerlink" title="Permalink to this definition">¶</a>  

 `execute_procedure`<span class="sig-paren">(</span>*procedure\_name*, *\*args*, *return\_results=False*<span class="sig-paren">)</span><a href="_modules/bi_etl/database/database_metadata.md#DatabaseMetadata.execute_procedure" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.database.database_metadata.DatabaseMetadata.execute_procedure" class="headerlink" title="Permalink to this definition">¶</a>  
Execute a stored procedure

|             |                                                                                                                                                                                       |
|-------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **procedure\_name** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The procedure to run. 
  -   **args** – The arguments to pass                                                                                                                                                   
  -   **return\_results** – Needs to be a keyword param. Should we try and get result rows from the procedure.                                                                           |
| Raises:     | -   sqlalchemy.exc.DBAPIError: – API error                                                                                                                                            
  -   sqlalchemy.exc.DatabaseError: – Proxy for database error                                                                                                                           |

 `get_children`<span class="sig-paren">(</span>*\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.database.database_metadata.DatabaseMetadata.get_children" class="headerlink" title="Permalink to this definition">¶</a>  
used to allow SchemaVisitor access

 `info`<a href="#bi_etl.database.database_metadata.DatabaseMetadata.info" class="headerlink" title="Permalink to this definition">¶</a>  
Info dictionary associated with the object, allowing user-defined data to be associated with this `SchemaItem`.

The dictionary is automatically generated when first accessed. It can also be specified in the constructor of some objects, such as <a href="bi_etl.components.table.md#bi_etl.components.table.Table" class="reference internal" title="bi_etl.components.table.Table"><code class="xref py py-class docutils literal">Table</code></a> and `Column`.

 `is_bound`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.database.database_metadata.DatabaseMetadata.is_bound" class="headerlink" title="Permalink to this definition">¶</a>  
True if this MetaData is bound to an Engine or Connection.

 `quote`<a href="#bi_etl.database.database_metadata.DatabaseMetadata.quote" class="headerlink" title="Permalink to this definition">¶</a>  
Return the value of the `quote` flag passed to this schema object, for those schema items which have a `name` field.

<span class="versionmodified">Deprecated since version 0.9: </span>Use `<obj>.name.quote`

 `reflect`<span class="sig-paren">(</span>*bind=None*, *schema=None*, *views=False*, *only=None*, *extend\_existing=False*, *autoload\_replace=True*, *\*\*dialect\_kwargs*<span class="sig-paren">)</span><a href="#bi_etl.database.database_metadata.DatabaseMetadata.reflect" class="headerlink" title="Permalink to this definition">¶</a>  
Load all available table definitions from the database.

Automatically creates `Table` entries in this `MetaData` for any table available in the database but not yet present in the `MetaData`. May be called multiple times to pick up tables recently added to the database, however no special action is taken if a table in this `MetaData` no longer exists in the database.

|             |                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **bind** – A `Connectable` used to access the database; if None, uses the existing bind on this `MetaData`, if any.                                                                                                                                                                                                                                                                                                                                      
  -   **schema** – Optional, query and reflect tables from an alterate schema. If None, the schema associated with this `MetaData` is used, if any.                                                                                                                                                                                                                                                                                                             
  -   **views** – If True, also reflect views.                                                                                                                                                                                                                                                                                                                                                                                                                  
  -   **only** –                                                                                                                                                                                                                                                                                                                                                                                                                                                
                                                                                                                                                                                                                                                                                                                                                                                                                                                                
      Optional. Load only a sub-set of available named tables. May be specified as a sequence of names or a callable.                                                                                                                                                                                                                                                                                                                                           
                                                                                                                                                                                                                                                                                                                                                                                                                                                                
      If a sequence of names is provided, only those tables will be reflected. An error is raised if a table is requested but not available. Named tables already present in this `MetaData` are ignored.                                                                                                                                                                                                                                                       
                                                                                                                                                                                                                                                                                                                                                                                                                                                                
      If a callable is provided, it will be used as a boolean predicate to filter the list of potential table names. The callable is called with a table name and this `MetaData` instance as positional arguments and should return a true value for any table to reflect.                                                                                                                                                                                     
                                                                                                                                                                                                                                                                                                                                                                                                                                                                
  -   **extend\_existing** –                                                                                                                                                                                                                                                                                                                                                                                                                                    
                                                                                                                                                                                                                                                                                                                                                                                                                                                                
      Passed along to each <a href="bi_etl.components.table.md#bi_etl.components.table.Table" class="reference internal" title="bi_etl.components.table.Table"><code class="xref py py-class docutils literal">Table</code></a> as [<span id="id2" class="problematic">:paramref:\`.Table.extend\_existing\`</span>](#id1).                                                                                                                                   
                                                                                                                                                                                                                                                                                                                                                                                                                                                                
      <span class="versionmodified">New in version 0.9.1.</span>                                                                                                                                                                                                                                                                                                                                                                                                
                                                                                                                                                                                                                                                                                                                                                                                                                                                                
  -   **autoload\_replace** –                                                                                                                                                                                                                                                                                                                                                                                                                                   
                                                                                                                                                                                                                                                                                                                                                                                                                                                                
      Passed along to each <a href="bi_etl.components.table.md#bi_etl.components.table.Table" class="reference internal" title="bi_etl.components.table.Table"><code class="xref py py-class docutils literal">Table</code></a> as [<span id="id4" class="problematic">:paramref:\`.Table.autoload\_replace\`</span>](#id3).                                                                                                                                  
                                                                                                                                                                                                                                                                                                                                                                                                                                                                
      <span class="versionmodified">New in version 0.9.1.</span>                                                                                                                                                                                                                                                                                                                                                                                                
                                                                                                                                                                                                                                                                                                                                                                                                                                                                
  -   **\*\*dialect\_kwargs** –                                                                                                                                                                                                                                                                                                                                                                                                                                 
                                                                                                                                                                                                                                                                                                                                                                                                                                                                
      Additional keyword arguments not mentioned above are dialect specific, and passed in the form `<dialectname>_<argname>`. See the documentation regarding an individual dialect at <span class="xref std std-ref">dialect\_toplevel</span> for detail on documented arguments.                                                                                                                                                                             
                                                                                                                                                                                                                                                                                                                                                                                                                                                                
      > <span class="versionmodified">New in version 0.9.2: </span>- Added [<span id="id6" class="problematic">:paramref:\`.MetaData.reflect.\*\*dialect\_kwargs\`</span>](#id5) to support dialect-level reflection options for all <a href="bi_etl.components.table.md#bi_etl.components.table.Table" class="reference internal" title="bi_etl.components.table.Table"><code class="xref py py-class docutils literal">Table</code></a> objects reflected.  |

 `remove`<span class="sig-paren">(</span>*table*<span class="sig-paren">)</span><a href="#bi_etl.database.database_metadata.DatabaseMetadata.remove" class="headerlink" title="Permalink to this definition">¶</a>  
Remove the given Table object from this MetaData.

 `sorted_tables`<a href="#bi_etl.database.database_metadata.DatabaseMetadata.sorted_tables" class="headerlink" title="Permalink to this definition">¶</a>  
Returns a list of <a href="bi_etl.components.table.md#bi_etl.components.table.Table" class="reference internal" title="bi_etl.components.table.Table"><code class="xref py py-class docutils literal">Table</code></a> objects sorted in order of foreign key dependency.

The sorting will place <a href="bi_etl.components.table.md#bi_etl.components.table.Table" class="reference internal" title="bi_etl.components.table.Table"><code class="xref py py-class docutils literal">Table</code></a> objects that have dependencies first, before the dependencies themselves, representing the order in which they can be created. To get the order in which the tables would be dropped, use the `reversed()` Python built-in.

Warning

The <a href="#bi_etl.database.database_metadata.DatabaseMetadata.sorted_tables" class="reference internal" title="bi_etl.database.database_metadata.DatabaseMetadata.sorted_tables"><code class="xref py py-attr docutils literal">sorted_tables</code></a> accessor cannot by itself accommodate automatic resolution of dependency cycles between tables, which are usually caused by mutually dependent foreign key constraints. To resolve these cycles, either the [<span id="id8" class="problematic">:paramref:\`.ForeignKeyConstraint.use\_alter\`</span>](#id7) parameter may be appled to those constraints, or use the `schema.sort_tables_and_constraints()` function which will break out foreign key constraints involved in cycles separately.

See also

`schema.sort_tables()`

`schema.sort_tables_and_constraints()`

`MetaData.tables`

`Inspector.get_table_names()`

`Inspector.get_sorted_table_and_fkc_names()`

 `tables` *= None*<a href="#bi_etl.database.database_metadata.DatabaseMetadata.tables" class="headerlink" title="Permalink to this definition">¶</a>  

#### Previous topic

[bi\_etl.database.connect module](bi_etl.database.connect.md "previous chapter")

#### Next topic

[bi\_etl.database.mock\_connect module](bi_etl.database.mock_connect.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.database.mock_connect.md "bi_etl.database.mock_connect module") |
-   [previous](bi_etl.database.connect.md "bi_etl.database.connect module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.database package](bi_etl.database.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
