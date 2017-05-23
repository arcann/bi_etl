### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.exceptions.md "bi_etl.exceptions package") |
-   [previous](bi_etl.database.mock_connect.md "bi_etl.database.mock_connect module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.database package](bi_etl.database.md) »

<span id="bi-etl-database-mock-database-metadata-module"></span>
bi\_etl.database.mock\_database\_metadata module<a href="#module-bi_etl.database.mock_database_metadata" class="headerlink" title="Permalink to this headline">¶</a>
====================================================================================================================================================================

Created on Dec 23, 2015

@author: woodd

 *class* `bi_etl.database.mock_database_metadata.``MockDatabaseMetadata`<a href="_modules/bi_etl/database/mock_database_metadata.md#MockDatabaseMetadata" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.database.mock_database_metadata.MockDatabaseMetadata" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="https://docs.python.org/2/library/functions.md#object" class="reference external" title="(in Python v2.7)"><code class="xref py py-class docutils literal">object</code></a>

Mock testing of sqlalchemy metadata

 `execute`<span class="sig-paren">(</span>*sql*<span class="sig-paren">)</span><a href="_modules/bi_etl/database/mock_database_metadata.md#MockDatabaseMetadata.execute" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.database.mock_database_metadata.MockDatabaseMetadata.execute" class="headerlink" title="Permalink to this definition">¶</a>  

 `execute_procedure`<span class="sig-paren">(</span>*procedure\_name*<span class="sig-paren">)</span><a href="_modules/bi_etl/database/mock_database_metadata.md#MockDatabaseMetadata.execute_procedure" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.database.mock_database_metadata.MockDatabaseMetadata.execute_procedure" class="headerlink" title="Permalink to this definition">¶</a>  
Execute a stored procedure

|             |                                                                                                                                                                                   |
|-------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | **procedure\_name** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The procedure to run. |
| Raises:     | -   sqlalchemy.exc.DBAPIError: – API error                                                                                                                                        
  -   sqlalchemy.exc.DatabaseError: – Maybe?                                                                                                                                         |

#### Previous topic

[bi\_etl.database.mock\_connect module](bi_etl.database.mock_connect.md "previous chapter")

#### Next topic

[bi\_etl.exceptions package](bi_etl.exceptions.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.exceptions.md "bi_etl.exceptions package") |
-   [previous](bi_etl.database.mock_connect.md "bi_etl.database.mock_connect module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.database package](bi_etl.database.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
