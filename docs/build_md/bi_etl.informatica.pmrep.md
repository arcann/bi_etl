### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.lookups.md "bi_etl.lookups package") |
-   [previous](bi_etl.informatica.pmcmd_task.md "bi_etl.informatica.pmcmd_task module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.informatica package](bi_etl.informatica.md) »

<span id="bi-etl-informatica-pmrep-module"></span>
bi\_etl.informatica.pmrep module<a href="#module-bi_etl.informatica.pmrep" class="headerlink" title="Permalink to this headline">¶</a>
======================================================================================================================================

Created on May 4, 2015

@author: woodd

 *class* `bi_etl.informatica.pmrep.``PMREP`<span class="sig-paren">(</span>*config=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="https://docs.python.org/2/library/functions.md#object" class="reference external" title="(in Python v2.7)"><code class="xref py py-class docutils literal">object</code></a>

 `SETTINGS_SECTION` *= 'INFORMATICA'*<a href="#bi_etl.informatica.pmrep.PMREP.SETTINGS_SECTION" class="headerlink" title="Permalink to this definition">¶</a>  

 `attributesString`<span class="sig-paren">(</span>*element*<span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.attributesString" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.attributesString" class="headerlink" title="Permalink to this definition">¶</a>  

 `cleanup`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.cleanup" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.cleanup" class="headerlink" title="Permalink to this definition">¶</a>  

 `connect`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.connect" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.connect" class="headerlink" title="Permalink to this definition">¶</a>  

 `deleteObject`<span class="sig-paren">(</span>*objectDict*<span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.deleteObject" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.deleteObject" class="headerlink" title="Permalink to this definition">¶</a>  

 `domain`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.domain" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.domain" class="headerlink" title="Permalink to this definition">¶</a>  

 `exportObject`<span class="sig-paren">(</span>*objectDict*, *dependents*, *outputPath*<span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.exportObject" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.exportObject" class="headerlink" title="Permalink to this definition">¶</a>  

 `exportObjectAutoDependents`<span class="sig-paren">(</span>*objectDict*, *outputPath*<span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.exportObjectAutoDependents" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.exportObjectAutoDependents" class="headerlink" title="Permalink to this definition">¶</a>  

 `exportObjectList`<span class="sig-paren">(</span>*objectList*<span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.exportObjectList" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.exportObjectList" class="headerlink" title="Permalink to this definition">¶</a>  

 `folder`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.folder" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.folder" class="headerlink" title="Permalink to this definition">¶</a>  

 `getFileName`<span class="sig-paren">(</span>*objectDict*<span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.getFileName" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.getFileName" class="headerlink" title="Permalink to this definition">¶</a>  

 `getFolderName`<span class="sig-paren">(</span>*objectDict*<span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.getFolderName" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.getFolderName" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_objects`<span class="sig-paren">(</span>*object\_type*, *folder\_name*<span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.get_objects" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.get_objects" class="headerlink" title="Permalink to this definition">¶</a>  

 `get_objects_from_query`<span class="sig-paren">(</span>*query\_name*<span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.get_objects_from_query" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.get_objects_from_query" class="headerlink" title="Permalink to this definition">¶</a>  

 `importFile`<span class="sig-paren">(</span>*folderName*, *fileName*<span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.importFile" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.importFile" class="headerlink" title="Permalink to this definition">¶</a>  

 `importFileObj`<span class="sig-paren">(</span>*fileObj*<span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.importFileObj" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.importFileObj" class="headerlink" title="Permalink to this definition">¶</a>  

 `importXMLFile`<span class="sig-paren">(</span>*path*, *control\_file*<span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.importXMLFile" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.importXMLFile" class="headerlink" title="Permalink to this definition">¶</a>  

 `informatica_bin_dir`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.informatica_bin_dir" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.informatica_bin_dir" class="headerlink" title="Permalink to this definition">¶</a>  

 `informatica_pmrep`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.informatica_pmrep" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.informatica_pmrep" class="headerlink" title="Permalink to this definition">¶</a>  

 `password`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.password" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.password" class="headerlink" title="Permalink to this definition">¶</a>  

 `repository`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.repository" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.repository" class="headerlink" title="Permalink to this definition">¶</a>  

 `set_password_in_env`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.set_password_in_env" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.set_password_in_env" class="headerlink" title="Permalink to this definition">¶</a>  

 `setup_inf_path`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.setup_inf_path" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.setup_inf_path" class="headerlink" title="Permalink to this definition">¶</a>  

 `specifizeControlFile`<span class="sig-paren">(</span>*controlFile*, *workingControlFile*<span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.specifizeControlFile" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.specifizeControlFile" class="headerlink" title="Permalink to this definition">¶</a>  

 `user_id`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.user_id" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.user_id" class="headerlink" title="Permalink to this definition">¶</a>  

 `validateObject`<span class="sig-paren">(</span>*objectDict*<span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.validateObject" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.validateObject" class="headerlink" title="Permalink to this definition">¶</a>  

 `validateObjectList`<span class="sig-paren">(</span>*objectList*<span class="sig-paren">)</span><a href="_modules/bi_etl/informatica/pmrep.md#PMREP.validateObjectList" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.informatica.pmrep.PMREP.validateObjectList" class="headerlink" title="Permalink to this definition">¶</a>  

#### Previous topic

[bi\_etl.informatica.pmcmd\_task module](bi_etl.informatica.pmcmd_task.md "previous chapter")

#### Next topic

[bi\_etl.lookups package](bi_etl.lookups.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.lookups.md "bi_etl.lookups package") |
-   [previous](bi_etl.informatica.pmcmd_task.md "bi_etl.informatica.pmcmd_task module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.informatica package](bi_etl.informatica.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
