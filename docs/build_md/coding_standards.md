### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](modules.md "bi_etl") |
-   [previous](config_ini.md "config.ini") |
-   [bi\_etl 0.5.3 documentation](index.md) »

Coding Standards<a href="#coding-standards" class="headerlink" title="Permalink to this headline">¶</a>
=======================================================================================================

docstrings<a href="#docstrings" class="headerlink" title="Permalink to this headline">¶</a>
-------------------------------------------------------------------------------------------

Each class method should have a docstring. It should follow the <a href="https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt" class="reference external">numpy</a> formatting standard. See <a href="http://sphinxcontrib-napoleon.readthedocs.org/en/latest/example_numpy.md" class="reference external">this example</a>

Rst files<a href="#rst-files" class="headerlink" title="Permalink to this headline">¶</a>
-----------------------------------------------------------------------------------------

These documenation files are reStructuredText formatted. They are processed into HTML using <a href="http://www.sphinx-doc.org/en/stable/rest.md" class="reference external">Sphinx</a>.

Building the HTML Version<a href="#building-the-html-version" class="headerlink" title="Permalink to this headline">¶</a>
=========================================================================================================================

From `.\doc` run the command:

    make.bat html

Check and fix the cause of any warnings or errors.

If you remove any .rst files you will need to run a clean build. From `.\doc` run the commands:

    make.bat clean
    make.bat html

reStructuredText Header Levels<a href="#restructuredtext-header-levels" class="headerlink" title="Permalink to this headline">¶</a>
===================================================================================================================================

We use the following formats for the different reStructuredText header levels:

    #######
    Level 1
    #######

    *******
    Level 2
    *******

    Level 3
    ~~~~~~~

    Level 4
    =======

    Level 5
    -------

    Level 6
    +++++++

### [Table Of Contents](index.md)

-   <a href="#" class="reference internal">Coding Standards</a>
    -   <a href="#docstrings" class="reference internal">docstrings</a>
    -   <a href="#rst-files" class="reference internal">Rst files</a>
-   <a href="#building-the-html-version" class="reference internal">Building the HTML Version</a>
-   <a href="#restructuredtext-header-levels" class="reference internal">reStructuredText Header Levels</a>

#### Previous topic

[config.ini](config_ini.md "previous chapter")

#### Next topic

[bi\_etl](modules.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](modules.md "bi_etl") |
-   [previous](config_ini.md "config.ini") |
-   [bi\_etl 0.5.3 documentation](index.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
