### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.conversions.md "bi_etl.conversions module") |
-   [previous](bi_etl.utility.ask.md "bi_etl.utility.ask module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »

<span id="bi-etl-bi-config-parser-module"></span>
bi\_etl.bi\_config\_parser module<a href="#module-bi_etl.bi_config_parser" class="headerlink" title="Permalink to this headline">¶</a>
======================================================================================================================================

Created on Apr 8, 2014

@author: woodd

 *class* `bi_etl.bi_config_parser.``BIConfigParser`<span class="sig-paren">(</span>*\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="_modules/bi_etl/bi_config_parser.md#BIConfigParser" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.bi_config_parser.BIConfigParser" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: `configparser.ConfigParser`

The basic configuration object. When defaults is given, it is initialized into the dictionary of intrinsic defaults. When dict\_type is given, it will be used to create the dictionary objects for the list of sections, for the options within a section, and for the default values. When allow\_no\_value is true (default: False), options without values are accepted; the value presented for these is None.

Adds a read\_config\_ini function to read bi\_etl\_configconfig.ini from C:, E:or Home directory Adds a read\_relative\_config function to search from pwd up to file the config file

 `BOOLEAN_STATES` *= {'1': True, 'yes': True, 'true': True, 'on': True, '0': False, 'no': False, 'false': False, 'off': False}*<a href="#bi_etl.bi_config_parser.BIConfigParser.BOOLEAN_STATES" class="headerlink" title="Permalink to this definition">¶</a>  

 `NONSPACECRE` *= re.compile('\\\\S')*<a href="#bi_etl.bi_config_parser.BIConfigParser.NONSPACECRE" class="headerlink" title="Permalink to this definition">¶</a>  

 `OPTCRE` *= re.compile('\\n (?P&lt;option&gt;.\*?) \# very permissive!\\n \\\\s\*(?P&lt;vi&gt;=|:)\\\\s\* \# any number of space/tab,\\n \# followed by any of t, re.VERBOSE)*<a href="#bi_etl.bi_config_parser.BIConfigParser.OPTCRE" class="headerlink" title="Permalink to this definition">¶</a>  

 `OPTCRE_NV` *= re.compile('\\n (?P&lt;option&gt;.\*?) \# very permissive!\\n \\\\s\*(?: \# any number of space/tab,\\n (?P&lt;vi&gt;=|:)\\\\s\* \# optionally followed , re.VERBOSE)*<a href="#bi_etl.bi_config_parser.BIConfigParser.OPTCRE_NV" class="headerlink" title="Permalink to this definition">¶</a>  

 `SECTCRE` *= re.compile('\\n \\\\\[ \# \[\\n (?P&lt;header&gt;\[^\]\]+) \# very permissive!\\n \\\\\] \# \]\\n ', re.VERBOSE)*<a href="#bi_etl.bi_config_parser.BIConfigParser.SECTCRE" class="headerlink" title="Permalink to this definition">¶</a>  

 `add_log_file_handler`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/bi_config_parser.md#BIConfigParser.add_log_file_handler" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.bi_config_parser.BIConfigParser.add_log_file_handler" class="headerlink" title="Permalink to this definition">¶</a>  

 `add_section`<span class="sig-paren">(</span>*section*<span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.add_section" class="headerlink" title="Permalink to this definition">¶</a>  
Create a new section in the configuration. Extends RawConfigParser.add\_section by validating if the section name is a string.

 `clear`<span class="sig-paren">(</span><span class="sig-paren">)</span> → None. Remove all items from D.<a href="#bi_etl.bi_config_parser.BIConfigParser.clear" class="headerlink" title="Permalink to this definition">¶</a>  

 `converters`<a href="#bi_etl.bi_config_parser.BIConfigParser.converters" class="headerlink" title="Permalink to this definition">¶</a>  

 `defaults`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.defaults" class="headerlink" title="Permalink to this definition">¶</a>  

 `get`<span class="sig-paren">(</span>*section*, *option*, *\**, *raw=False*, *vars=None*, *fallback=&lt;object object&gt;*<span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.get" class="headerlink" title="Permalink to this definition">¶</a>  
Get an option value for a given section.

If [<span id="id2" class="problematic">\`</span>](#id1)vars’ is provided, it must be a dictionary. The option is looked up in [<span id="id4" class="problematic">\`</span>](#id3)vars’ (if provided), [<span id="id6" class="problematic">\`</span>](#id5)section’, and in [<span id="id8" class="problematic">\`</span>](#id7)DEFAULTSECT’ in that order. If the key is not found and [<span id="id10" class="problematic">\`</span>](#id9)fallback’ is provided, it is used as a fallback value. [<span id="id12" class="problematic">\`</span>](#id11)None’ can be provided as a [<span id="id14" class="problematic">\`</span>](#id13)fallback’ value.

If interpolation is enabled and the optional argument [<span id="id16" class="problematic">\`</span>](#id15)raw’ is False, all interpolations are expanded in the return values.

Arguments [<span id="id18" class="problematic">\`</span>](#id17)raw’, [<span id="id20" class="problematic">\`</span>](#id19)vars’, and [<span id="id22" class="problematic">\`</span>](#id21)fallback’ are keyword only.

The section DEFAULT is special.

 `get_byte_size`<span class="sig-paren">(</span>*section: str*, *option: str*, *fallback: str = None*<span class="sig-paren">)</span> → int<a href="_modules/bi_etl/bi_config_parser.md#BIConfigParser.get_byte_size" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.bi_config_parser.BIConfigParser.get_byte_size" class="headerlink" title="Permalink to this definition">¶</a>  
Get a configuration option as a byte size or returns a default if that doesn’t exist. Both the option value and default will be parsed using <a href="bi_etl.conversions.md#bi_etl.conversions.str2bytes_size" class="reference internal" title="bi_etl.conversions.str2bytes_size"><code class="xref py py-func docutils literal">str2bytes_size()</code></a>

|             |                                                                                                                                                                                                                       |
|-------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **section** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The section to use.                                           
  -   **option** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The option value to get.                                        
  -   **fallback** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The default to return if the option or section is not found.  |

 `get_database_connection_tuple`<span class="sig-paren">(</span>*database\_name*, *user\_section=None*<span class="sig-paren">)</span><a href="_modules/bi_etl/bi_config_parser.md#BIConfigParser.get_database_connection_tuple" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.bi_config_parser.BIConfigParser.get_database_connection_tuple" class="headerlink" title="Permalink to this definition">¶</a>  
Gets a tuple (userid, password) of connection information for a given database name.

|             |                                                                                                                                                                                                                                                                                                                                                                   |
|-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **database\_name** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The name of the database to look for in the configuration.                                                                                                                                         
  -   **user\_section** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The name of the section to use for the user ID and password. Optional. If not provided, the method will look for a default\_user\_id value in the section named using the database\_name parameter.  |

 `get_log_file_name`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/bi_config_parser.md#BIConfigParser.get_log_file_name" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.bi_config_parser.BIConfigParser.get_log_file_name" class="headerlink" title="Permalink to this definition">¶</a>  
Gets the log file name defined in the config file. Uses `log_file_name` and `log_folder` from the `logging` section

    [logging]
    log_file_name=my_file_name
    log_folder=/my/log/path

 *static* `get_package_root`<span class="sig-paren">(</span>*obj: object = None*<span class="sig-paren">)</span> → str<a href="_modules/bi_etl/bi_config_parser.md#BIConfigParser.get_package_root" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.bi_config_parser.BIConfigParser.get_package_root" class="headerlink" title="Permalink to this definition">¶</a>  
Get the root path of a package given an object (default is this module).

|             |                                                                     |
|-------------|---------------------------------------------------------------------|
| Parameters: | **obj** – The object to inspect for package Defaults to this module |
| Returns:    | The root path of the package                                        |

 `getboolean`<span class="sig-paren">(</span>*section*, *option*, *\**, *raw=False*, *vars=None*, *fallback=&lt;object object&gt;*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.getboolean" class="headerlink" title="Permalink to this definition">¶</a>  

 `getfloat`<span class="sig-paren">(</span>*section*, *option*, *\**, *raw=False*, *vars=None*, *fallback=&lt;object object&gt;*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.getfloat" class="headerlink" title="Permalink to this definition">¶</a>  

 `getint`<span class="sig-paren">(</span>*section*, *option*, *\**, *raw=False*, *vars=None*, *fallback=&lt;object object&gt;*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.getint" class="headerlink" title="Permalink to this definition">¶</a>  

 `has_option`<span class="sig-paren">(</span>*section*, *option*<span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.has_option" class="headerlink" title="Permalink to this definition">¶</a>  
Check for the existence of a given option in a given section. If the specified [<span id="id24" class="problematic">\`</span>](#id23)section’ is None or an empty string, DEFAULT is assumed. If the specified [<span id="id26" class="problematic">\`</span>](#id25)section’ does not exist, returns False.

 `has_section`<span class="sig-paren">(</span>*section*<span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.has_section" class="headerlink" title="Permalink to this definition">¶</a>  
Indicate whether the named section is present in the configuration.

The DEFAULT section is not acknowledged.

 `items`<span class="sig-paren">(</span>*section=&lt;object object&gt;*, *raw=False*, *vars=None*<span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.items" class="headerlink" title="Permalink to this definition">¶</a>  
Return a list of (name, value) tuples for each option in a section.

All % interpolations are expanded in the return values, based on the defaults passed into the constructor, unless the optional argument [<span id="id28" class="problematic">\`</span>](#id27)raw’ is true. Additional substitutions may be provided using the [<span id="id30" class="problematic">\`</span>](#id29)vars’ argument, which must be a dictionary whose contents overrides any pre-existing defaults.

The section DEFAULT is special.

 `keys`<span class="sig-paren">(</span><span class="sig-paren">)</span> → a set-like object providing a view on D's keys<a href="#bi_etl.bi_config_parser.BIConfigParser.keys" class="headerlink" title="Permalink to this definition">¶</a>  

 `merge_parent`<span class="sig-paren">(</span>*directories*, *parent\_file*<span class="sig-paren">)</span><a href="_modules/bi_etl/bi_config_parser.md#BIConfigParser.merge_parent" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.bi_config_parser.BIConfigParser.merge_parent" class="headerlink" title="Permalink to this definition">¶</a>  

 `options`<span class="sig-paren">(</span>*section*<span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.options" class="headerlink" title="Permalink to this definition">¶</a>  
Return a list of option names for the given section name.

 `optionxform`<span class="sig-paren">(</span>*optionstr*<span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.optionxform" class="headerlink" title="Permalink to this definition">¶</a>  

 `pop`<span class="sig-paren">(</span>*k*<span class="optional">\[</span>, *d*<span class="optional">\]</span><span class="sig-paren">)</span> → v, remove specified key and return the corresponding value.<a href="#bi_etl.bi_config_parser.BIConfigParser.pop" class="headerlink" title="Permalink to this definition">¶</a>  
If key is not found, d is returned if given, otherwise KeyError is raised.

 `popitem`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.popitem" class="headerlink" title="Permalink to this definition">¶</a>  
Remove a section from the parser and return it as a (section\_name, section\_proxy) tuple. If no section is present, raise KeyError.

The section DEFAULT is never returned because it cannot be removed.

 `read`<span class="sig-paren">(</span>*filenames*, *encoding=None*<span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.read" class="headerlink" title="Permalink to this definition">¶</a>  
Read and parse a filename or a list of filenames.

Files that cannot be opened are silently ignored; this is designed so that you can specify a list of potential configuration file locations (e.g. current directory, user’s home directory, systemwide directory), and all existing configuration files in the list will be read. A single filename may also be given.

Return list of successfully read files.

 `read_config_ini`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/bi_config_parser.md#BIConfigParser.read_config_ini" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.bi_config_parser.BIConfigParser.read_config_ini" class="headerlink" title="Permalink to this definition">¶</a>  
Read the config file from any of the following locations (merging multiple files together if more than one exists.) \* C:bi\_etl\_configconfig.ini \* D:bi\_etl\_configconfig.ini \* E:bi\_etl\_configconfig.ini \* ~/bi\_etl\_configconfig.ini \* Current Directory

Where ~ is the users home directory.

 `read_dict`<span class="sig-paren">(</span>*dictionary*, *source='&lt;dict&gt;'*<span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.read_dict" class="headerlink" title="Permalink to this definition">¶</a>  
Read configuration from a dictionary.

Keys are section names, values are dictionaries with keys and values that should be present in the section. If the used dictionary type preserves order, sections and their keys will be added in order.

All types held in the dictionary are converted to strings during reading, including section names, option names and keys.

Optional second argument is the [<span id="id32" class="problematic">\`</span>](#id31)source’ specifying the name of the dictionary being read.

 `read_file`<span class="sig-paren">(</span>*f*, *source=None*<span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.read_file" class="headerlink" title="Permalink to this definition">¶</a>  
Like read() but the argument must be a file-like object.

The [<span id="id34" class="problematic">\`</span>](#id33)f’ argument must be iterable, returning one line at a time. Optional second argument is the [<span id="id36" class="problematic">\`</span>](#id35)source’ specifying the name of the file being read. If not given, it is taken from f.name. If [<span id="id38" class="problematic">\`</span>](#id37)f’ has no [<span id="id40" class="problematic">\`</span>](#id39)name’ attribute, [<span id="id42" class="problematic">\`</span>](#id41)&lt;???&gt;’ is used.

 `read_parents`<span class="sig-paren">(</span>*directories*<span class="sig-paren">)</span><a href="_modules/bi_etl/bi_config_parser.md#BIConfigParser.read_parents" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.bi_config_parser.BIConfigParser.read_parents" class="headerlink" title="Permalink to this definition">¶</a>  

 `read_relative_config`<span class="sig-paren">(</span>*config\_file\_name*, *start\_path='C:\\\\Program Files (x86)\\\\JetBrains\\\\PyCharm 2016.3\\\\bin'*<span class="sig-paren">)</span><a href="_modules/bi_etl/bi_config_parser.md#BIConfigParser.read_relative_config" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.bi_config_parser.BIConfigParser.read_relative_config" class="headerlink" title="Permalink to this definition">¶</a>  
Search from start\_path (default current directory) up to file the configuration file

|              |                                                                                                                                                                                                                                    |
|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters:  | -   **config\_file\_name** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The name of the config file to look for and read                
  -   **start\_path** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – Optional. The path to start looking in. Defaults to current directory.  |
| Returns:     | **files\_read** – list of successfully read files.                                                                                                                                                                                 |
| Return type: | list                                                                                                                                                                                                                               |

 `read_string`<span class="sig-paren">(</span>*string*, *source='&lt;string&gt;'*<span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.read_string" class="headerlink" title="Permalink to this definition">¶</a>  
Read configuration from a given string.

 `readfp`<span class="sig-paren">(</span>*fp*, *filename=None*<span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.readfp" class="headerlink" title="Permalink to this definition">¶</a>  
Deprecated, use read\_file instead.

 `remove_option`<span class="sig-paren">(</span>*section*, *option*<span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.remove_option" class="headerlink" title="Permalink to this definition">¶</a>  
Remove an option.

 `remove_section`<span class="sig-paren">(</span>*section*<span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.remove_section" class="headerlink" title="Permalink to this definition">¶</a>  
Remove a file section.

 `sections`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.sections" class="headerlink" title="Permalink to this definition">¶</a>  
Return a list of section names, excluding \[DEFAULT\]

 `set`<span class="sig-paren">(</span>*section*, *option*, *value=None*<span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.set" class="headerlink" title="Permalink to this definition">¶</a>  
Set an option. Extends RawConfigParser.set by validating type and interpolation syntax on the value.

 `set_dated_log_file_name`<span class="sig-paren">(</span>*prefix=''*, *suffix=''*, *date\_time\_format='\_%Y\_%m\_%d\_at\_%H\_%M\_%S'*<span class="sig-paren">)</span><a href="_modules/bi_etl/bi_config_parser.md#BIConfigParser.set_dated_log_file_name" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.bi_config_parser.BIConfigParser.set_dated_log_file_name" class="headerlink" title="Permalink to this definition">¶</a>  
Sets the log file name in the config (memory copy only) using the current date and time. Specifically that is `log_file_name` in the `logging` section.

|             |                                                                                                                                                                                                                                                      |
|-------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **prefix** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The part of the log file name before the date                                                 
  -   **suffix** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – The part of the log file name after the date                                                   
  -   **date\_time\_format** (<a href="https://docs.python.org/2/library/functions.md#str" class="reference external" title="(in Python v2.7)"><em>str</em></a>) – Optional. The date time format to use. Defaults to ‘\_%Y\_%m\_%d\_at\_%H\_%M\_%S’  |

 `set_log_file_name`<span class="sig-paren">(</span>*log\_file\_name*<span class="sig-paren">)</span><a href="_modules/bi_etl/bi_config_parser.md#BIConfigParser.set_log_file_name" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.bi_config_parser.BIConfigParser.set_log_file_name" class="headerlink" title="Permalink to this definition">¶</a>  
Sets the log file name in the config (memory copy only) Specifically that is `log_file_name` in the `logging` section

 `setdefault`<span class="sig-paren">(</span>*k*<span class="optional">\[</span>, *d*<span class="optional">\]</span><span class="sig-paren">)</span> → D.get(k,d), also set D\[k\]=d if k not in D<a href="#bi_etl.bi_config_parser.BIConfigParser.setdefault" class="headerlink" title="Permalink to this definition">¶</a>  

 `setup_log_levels`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/bi_config_parser.md#BIConfigParser.setup_log_levels" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.bi_config_parser.BIConfigParser.setup_log_levels" class="headerlink" title="Permalink to this definition">¶</a>  

 `setup_logging`<span class="sig-paren">(</span>*console\_output=None*, *use\_log\_file\_setting=True*<span class="sig-paren">)</span><a href="_modules/bi_etl/bi_config_parser.md#BIConfigParser.setup_logging" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.bi_config_parser.BIConfigParser.setup_logging" class="headerlink" title="Permalink to this definition">¶</a>  
Setup logging configuration.

Based on the \[logging\] and \[loggers\] sections of the configuration file.

 `update`<span class="sig-paren">(</span><span class="optional">\[</span>*E*, <span class="optional">\]</span>*\*\*F*<span class="sig-paren">)</span> → None. Update D from mapping/iterable E and F.<a href="#bi_etl.bi_config_parser.BIConfigParser.update" class="headerlink" title="Permalink to this definition">¶</a>  
If E present and has a .keys() method, does: for k in E: D\[k\] = E\[k\] If E present and lacks .keys() method, does: for (k, v) in E: D\[k\] = v In either case, this is followed by: for k, v in F.items(): D\[k\] = v

 `values`<span class="sig-paren">(</span><span class="sig-paren">)</span> → an object providing a view on D's values<a href="#bi_etl.bi_config_parser.BIConfigParser.values" class="headerlink" title="Permalink to this definition">¶</a>  

 `write`<span class="sig-paren">(</span>*fp*, *space\_around\_delimiters=True*<span class="sig-paren">)</span><a href="#bi_etl.bi_config_parser.BIConfigParser.write" class="headerlink" title="Permalink to this definition">¶</a>  
Write an .ini-format representation of the configuration state.

If [<span id="id44" class="problematic">\`</span>](#id43)space\_around\_delimiters’ is True (the default), delimiters between keys and values are surrounded by spaces.

<!-- -->

 `bi_etl.bi_config_parser.``build_example`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/bi_config_parser.md#build_example" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.bi_config_parser.build_example" class="headerlink" title="Permalink to this definition">¶</a>  
Builds an example config file from the currently active one in the users folder

#### Previous topic

[bi\_etl.utility.ask module](bi_etl.utility.ask.md "previous chapter")

#### Next topic

[bi\_etl.conversions module](bi_etl.conversions.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.conversions.md "bi_etl.conversions module") |
-   [previous](bi_etl.utility.ask.md "bi_etl.utility.ask module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
