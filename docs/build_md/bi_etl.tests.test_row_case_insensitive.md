### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.tests.test_scheduler.md "bi_etl.tests.test_scheduler module") |
-   [previous](bi_etl.tests.test_row.md "bi_etl.tests.test_row module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.tests package](bi_etl.tests.md) »

<span id="bi-etl-tests-test-row-case-insensitive-module"></span>
bi\_etl.tests.test\_row\_case\_insensitive module<a href="#module-bi_etl.tests.test_row_case_insensitive" class="headerlink" title="Permalink to this headline">¶</a>
=====================================================================================================================================================================

Created on Mar 26, 2015

@author: woodd

 *class* `bi_etl.tests.test_row_case_insensitive.``TestRowCaseInsensitive`<span class="sig-paren">(</span>*methodName='runTest'*<span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive" class="headerlink" title="Permalink to this definition">¶</a>  
Bases: <a href="bi_etl.tests.test_row.md#bi_etl.tests.test_row.TestRow" class="reference internal" title="bi_etl.tests.test_row.TestRow"><code class="xref py py-class docutils literal">bi_etl.tests.test_row.TestRow</code></a>

 `addCleanup`<span class="sig-paren">(</span>*function*, *\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.addCleanup" class="headerlink" title="Permalink to this definition">¶</a>  
Add a function, with arguments, to be called when the test is completed. Functions added are called on a LIFO basis and are called after tearDown on test failure or success.

Cleanup items are called even if setUp fails (unlike tearDown).

 `addTypeEqualityFunc`<span class="sig-paren">(</span>*typeobj*, *function*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.addTypeEqualityFunc" class="headerlink" title="Permalink to this definition">¶</a>  
Add a type specific assertEqual style function to compare a type.

This method is for use by TestCase subclasses that need to register their own type equality functions to provide nicer error messages.

|             |                                                                                                                                                                                        |
|-------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **typeobj** – The data type to call this function on when both values are of the same type in assertEqual().                                                                       
  -   **function** – The callable taking two arguments and an optional msg= argument that raises self.failureException with a useful error message when the two arguments are not equal.  |

 `assertAlmostEqual`<span class="sig-paren">(</span>*first*, *second*, *places=None*, *msg=None*, *delta=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertAlmostEqual" class="headerlink" title="Permalink to this definition">¶</a>  
Fail if the two objects are unequal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero, or by comparing that the between the two objects is more than the given delta.

Note that decimal places (from zero) are usually not the same as significant digits (measured from the most significant digit).

If the two objects compare equal then they will automatically compare almost equal.

 `assertAlmostEquals`<span class="sig-paren">(</span>*\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertAlmostEquals" class="headerlink" title="Permalink to this definition">¶</a>  

 `assertCountEqual`<span class="sig-paren">(</span>*first*, *second*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertCountEqual" class="headerlink" title="Permalink to this definition">¶</a>  
An unordered sequence comparison asserting that the same elements, regardless of order. If the same element occurs more than once, it verifies that the elements occur the same number of times.

> > self.assertEqual(Counter(list(first)),  
> > Counter(list(second)))
>
> Example:  
> -   \[0, 1, 1\] and \[1, 0, 1\] compare equal.
> -   \[0, 0, 1\] and \[0, 1\] compare unequal.

 `assertDictContainsSubset`<span class="sig-paren">(</span>*subset*, *dictionary*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertDictContainsSubset" class="headerlink" title="Permalink to this definition">¶</a>  
Checks whether dictionary is a superset of subset.

 `assertDictEqual`<span class="sig-paren">(</span>*d1*, *d2*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertDictEqual" class="headerlink" title="Permalink to this definition">¶</a>  

 `assertEqual`<span class="sig-paren">(</span>*first*, *second*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertEqual" class="headerlink" title="Permalink to this definition">¶</a>  
Fail if the two objects are unequal as determined by the ‘==’ operator.

 `assertEquals`<span class="sig-paren">(</span>*\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertEquals" class="headerlink" title="Permalink to this definition">¶</a>  

 `assertFalse`<span class="sig-paren">(</span>*expr*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertFalse" class="headerlink" title="Permalink to this definition">¶</a>  
Check that the expression is false.

 `assertGreater`<span class="sig-paren">(</span>*a*, *b*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertGreater" class="headerlink" title="Permalink to this definition">¶</a>  
Just like self.assertTrue(a &gt; b), but with a nicer default message.

 `assertGreaterEqual`<span class="sig-paren">(</span>*a*, *b*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertGreaterEqual" class="headerlink" title="Permalink to this definition">¶</a>  
Just like self.assertTrue(a &gt;= b), but with a nicer default message.

 `assertIn`<span class="sig-paren">(</span>*member*, *container*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertIn" class="headerlink" title="Permalink to this definition">¶</a>  
Just like self.assertTrue(a in b), but with a nicer default message.

 `assertIs`<span class="sig-paren">(</span>*expr1*, *expr2*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertIs" class="headerlink" title="Permalink to this definition">¶</a>  
Just like self.assertTrue(a is b), but with a nicer default message.

 `assertIsInstance`<span class="sig-paren">(</span>*obj*, *cls*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertIsInstance" class="headerlink" title="Permalink to this definition">¶</a>  
Same as self.assertTrue(isinstance(obj, cls)), with a nicer default message.

 `assertIsNone`<span class="sig-paren">(</span>*obj*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertIsNone" class="headerlink" title="Permalink to this definition">¶</a>  
Same as self.assertTrue(obj is None), with a nicer default message.

 `assertIsNot`<span class="sig-paren">(</span>*expr1*, *expr2*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertIsNot" class="headerlink" title="Permalink to this definition">¶</a>  
Just like self.assertTrue(a is not b), but with a nicer default message.

 `assertIsNotNone`<span class="sig-paren">(</span>*obj*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertIsNotNone" class="headerlink" title="Permalink to this definition">¶</a>  
Included for symmetry with assertIsNone.

 `assertLess`<span class="sig-paren">(</span>*a*, *b*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertLess" class="headerlink" title="Permalink to this definition">¶</a>  
Just like self.assertTrue(a &lt; b), but with a nicer default message.

 `assertLessEqual`<span class="sig-paren">(</span>*a*, *b*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertLessEqual" class="headerlink" title="Permalink to this definition">¶</a>  
Just like self.assertTrue(a &lt;= b), but with a nicer default message.

 `assertListEqual`<span class="sig-paren">(</span>*list1*, *list2*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertListEqual" class="headerlink" title="Permalink to this definition">¶</a>  
A list-specific equality assertion.

|             |                                                                                    |
|-------------|------------------------------------------------------------------------------------|
| Parameters: | -   **list1** – The first list to compare.                                         
  -   **list2** – The second list to compare.                                         
  -   **msg** – Optional message to use on failure instead of a list of differences.  |

 `assertLogs`<span class="sig-paren">(</span>*logger=None*, *level=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertLogs" class="headerlink" title="Permalink to this definition">¶</a>  
Fail unless a log message of level *level* or higher is emitted on *logger\_name* or its children. If omitted, *level* defaults to INFO and *logger* defaults to the root logger.

This method must be used as a context manager, and will yield a recording object with two attributes: output and records. At the end of the context manager, the output attribute will be a list of the matching formatted log messages and the records attribute will be a list of the corresponding LogRecord objects.

Example:

    with self.assertLogs('foo', level='INFO') as cm:
        logging.getLogger('foo').info('first message')
        logging.getLogger('foo.bar').error('second message')
    self.assertEqual(cm.output, ['INFO:foo:first message',
                                 'ERROR:foo.bar:second message'])

 `assertMultiLineEqual`<span class="sig-paren">(</span>*first*, *second*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertMultiLineEqual" class="headerlink" title="Permalink to this definition">¶</a>  
Assert that two multi-line strings are equal.

 `assertNotAlmostEqual`<span class="sig-paren">(</span>*first*, *second*, *places=None*, *msg=None*, *delta=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertNotAlmostEqual" class="headerlink" title="Permalink to this definition">¶</a>  
Fail if the two objects are equal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero, or by comparing that the between the two objects is less than the given delta.

Note that decimal places (from zero) are usually not the same as significant digits (measured from the most significant digit).

Objects that are equal automatically fail.

 `assertNotAlmostEquals`<span class="sig-paren">(</span>*\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertNotAlmostEquals" class="headerlink" title="Permalink to this definition">¶</a>  

 `assertNotEqual`<span class="sig-paren">(</span>*first*, *second*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertNotEqual" class="headerlink" title="Permalink to this definition">¶</a>  
Fail if the two objects are equal as determined by the ‘!=’ operator.

 `assertNotEquals`<span class="sig-paren">(</span>*\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertNotEquals" class="headerlink" title="Permalink to this definition">¶</a>  

 `assertNotIn`<span class="sig-paren">(</span>*member*, *container*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertNotIn" class="headerlink" title="Permalink to this definition">¶</a>  
Just like self.assertTrue(a not in b), but with a nicer default message.

 `assertNotIsInstance`<span class="sig-paren">(</span>*obj*, *cls*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertNotIsInstance" class="headerlink" title="Permalink to this definition">¶</a>  
Included for symmetry with assertIsInstance.

 `assertNotRegex`<span class="sig-paren">(</span>*text*, *unexpected\_regex*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertNotRegex" class="headerlink" title="Permalink to this definition">¶</a>  
Fail the test if the text matches the regular expression.

 `assertNotRegexpMatches`<span class="sig-paren">(</span>*\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertNotRegexpMatches" class="headerlink" title="Permalink to this definition">¶</a>  

 `assertRaises`<span class="sig-paren">(</span>*expected\_exception*, *\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertRaises" class="headerlink" title="Permalink to this definition">¶</a>  
Fail unless an exception of class expected\_exception is raised by the callable when invoked with specified positional and keyword arguments. If a different type of exception is raised, it will not be caught, and the test case will be deemed to have suffered an error, exactly as for an unexpected exception.

If called with the callable and arguments omitted, will return a context object used like this:

    with self.assertRaises(SomeException):
        do_something()

An optional keyword argument ‘msg’ can be provided when assertRaises is used as a context object.

The context manager keeps a reference to the exception as the ‘exception’ attribute. This allows you to inspect the exception after the assertion:

    with self.assertRaises(SomeException) as cm:
        do_something()
    the_exception = cm.exception
    self.assertEqual(the_exception.error_code, 3)

 `assertRaisesRegex`<span class="sig-paren">(</span>*expected\_exception*, *expected\_regex*, *\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertRaisesRegex" class="headerlink" title="Permalink to this definition">¶</a>  
Asserts that the message in a raised exception matches a regex.

|             |                                                                                                                               |
|-------------|-------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **expected\_exception** – Exception class expected to be raised.                                                          
  -   **expected\_regex** – Regex (re pattern object or string) expected to be found in error message.                           
  -   **args** – Function to be called and extra positional args.                                                                
  -   **kwargs** – Extra kwargs.                                                                                                 
  -   **msg** – Optional message used in case of failure. Can only be used when assertRaisesRegex is used as a context manager.  |

 `assertRaisesRegexp`<span class="sig-paren">(</span>*\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertRaisesRegexp" class="headerlink" title="Permalink to this definition">¶</a>  

 `assertRegex`<span class="sig-paren">(</span>*text*, *expected\_regex*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertRegex" class="headerlink" title="Permalink to this definition">¶</a>  
Fail the test unless the text matches the regular expression.

 `assertRegexpMatches`<span class="sig-paren">(</span>*\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertRegexpMatches" class="headerlink" title="Permalink to this definition">¶</a>  

 `assertSequenceEqual`<span class="sig-paren">(</span>*seq1*, *seq2*, *msg=None*, *seq\_type=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertSequenceEqual" class="headerlink" title="Permalink to this definition">¶</a>  
An equality assertion for ordered sequences (like lists and tuples).

For the purposes of this function, a valid ordered sequence type is one which can be indexed, has a length, and has an equality operator.

|             |                                                                                                        |
|-------------|--------------------------------------------------------------------------------------------------------|
| Parameters: | -   **seq1** – The first sequence to compare.                                                          
  -   **seq2** – The second sequence to compare.                                                          
  -   **seq\_type** – The expected datatype of the sequences, or None if no datatype should be enforced.  
  -   **msg** – Optional message to use on failure instead of a list of differences.                      |

 `assertSetEqual`<span class="sig-paren">(</span>*set1*, *set2*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertSetEqual" class="headerlink" title="Permalink to this definition">¶</a>  
A set-specific equality assertion.

|             |                                                                                    |
|-------------|------------------------------------------------------------------------------------|
| Parameters: | -   **set1** – The first set to compare.                                           
  -   **set2** – The second set to compare.                                           
  -   **msg** – Optional message to use on failure instead of a list of differences.  |

assertSetEqual uses ducktyping to support different types of sets, and is optimized for sets specifically (parameters must support a difference method).

 `assertTrue`<span class="sig-paren">(</span>*expr*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertTrue" class="headerlink" title="Permalink to this definition">¶</a>  
Check that the expression is true.

 `assertTupleEqual`<span class="sig-paren">(</span>*tuple1*, *tuple2*, *msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertTupleEqual" class="headerlink" title="Permalink to this definition">¶</a>  
A tuple-specific equality assertion.

|             |                                                                                    |
|-------------|------------------------------------------------------------------------------------|
| Parameters: | -   **tuple1** – The first tuple to compare.                                       
  -   **tuple2** – The second tuple to compare.                                       
  -   **msg** – Optional message to use on failure instead of a list of differences.  |

 `assertWarns`<span class="sig-paren">(</span>*expected\_warning*, *\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertWarns" class="headerlink" title="Permalink to this definition">¶</a>  
Fail unless a warning of class warnClass is triggered by the callable when invoked with specified positional and keyword arguments. If a different type of warning is triggered, it will not be handled: depending on the other warning filtering rules in effect, it might be silenced, printed out, or raised as an exception.

If called with the callable and arguments omitted, will return a context object used like this:

    with self.assertWarns(SomeWarning):
        do_something()

An optional keyword argument ‘msg’ can be provided when assertWarns is used as a context object.

The context manager keeps a reference to the first matching warning as the ‘warning’ attribute; similarly, the ‘filename’ and ‘lineno’ attributes give you information about the line of Python code from which the warning was triggered. This allows you to inspect the warning after the assertion:

    with self.assertWarns(SomeWarning) as cm:
        do_something()
    the_warning = cm.warning
    self.assertEqual(the_warning.some_attribute, 147)

 `assertWarnsRegex`<span class="sig-paren">(</span>*expected\_warning*, *expected\_regex*, *\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assertWarnsRegex" class="headerlink" title="Permalink to this definition">¶</a>  
Asserts that the message in a triggered warning matches a regexp. Basic functioning is similar to assertWarns() with the addition that only warnings whose messages also match the regular expression are considered successful matches.

|             |                                                                                                                              |
|-------------|------------------------------------------------------------------------------------------------------------------------------|
| Parameters: | -   **expected\_warning** – Warning class expected to be triggered.                                                          
  -   **expected\_regex** – Regex (re pattern object or string) expected to be found in error message.                          
  -   **args** – Function to be called and extra positional args.                                                               
  -   **kwargs** – Extra kwargs.                                                                                                
  -   **msg** – Optional message used in case of failure. Can only be used when assertWarnsRegex is used as a context manager.  |

 `assert_`<span class="sig-paren">(</span>*\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.assert_" class="headerlink" title="Permalink to this definition">¶</a>  

 `countTestCases`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.countTestCases" class="headerlink" title="Permalink to this definition">¶</a>  

 `create_performance_iterations` *= 50000*<a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.create_performance_iterations" class="headerlink" title="Permalink to this definition">¶</a>  

 `debug`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.debug" class="headerlink" title="Permalink to this definition">¶</a>  
Run the test without collecting errors in a TestResult

 `defaultTestResult`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.defaultTestResult" class="headerlink" title="Permalink to this definition">¶</a>  

 `doCleanups`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.doCleanups" class="headerlink" title="Permalink to this definition">¶</a>  
Execute all cleanup functions. Normally called for you after tearDown.

 `fail`<span class="sig-paren">(</span>*msg=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.fail" class="headerlink" title="Permalink to this definition">¶</a>  
Fail immediately, with the given message.

 `failIf`<span class="sig-paren">(</span>*\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.failIf" class="headerlink" title="Permalink to this definition">¶</a>  

 `failIfAlmostEqual`<span class="sig-paren">(</span>*\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.failIfAlmostEqual" class="headerlink" title="Permalink to this definition">¶</a>  

 `failIfEqual`<span class="sig-paren">(</span>*\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.failIfEqual" class="headerlink" title="Permalink to this definition">¶</a>  

 `failUnless`<span class="sig-paren">(</span>*\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.failUnless" class="headerlink" title="Permalink to this definition">¶</a>  

 `failUnlessAlmostEqual`<span class="sig-paren">(</span>*\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.failUnlessAlmostEqual" class="headerlink" title="Permalink to this definition">¶</a>  

 `failUnlessEqual`<span class="sig-paren">(</span>*\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.failUnlessEqual" class="headerlink" title="Permalink to this definition">¶</a>  

 `failUnlessRaises`<span class="sig-paren">(</span>*\*args*, *\*\*kwargs*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.failUnlessRaises" class="headerlink" title="Permalink to this definition">¶</a>  

 `failureException`<a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.failureException" class="headerlink" title="Permalink to this definition">¶</a>  
alias of `AssertionError`

 `get_performance_iterations` *= 1000000*<a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.get_performance_iterations" class="headerlink" title="Permalink to this definition">¶</a>  

 `id`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.id" class="headerlink" title="Permalink to this definition">¶</a>  

 `longMessage` *= True*<a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.longMessage" class="headerlink" title="Permalink to this definition">¶</a>  

 `maxDiff` *= 640*<a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.maxDiff" class="headerlink" title="Permalink to this definition">¶</a>  

 `run`<span class="sig-paren">(</span>*result=None*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.run" class="headerlink" title="Permalink to this definition">¶</a>  

 `setUp`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.setUp" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.setUp" class="headerlink" title="Permalink to this definition">¶</a>  

 `setUpClass`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.setUpClass" class="headerlink" title="Permalink to this definition">¶</a>  
Hook method for setting up class fixture before running tests in the class.

 `set_existing_performance_iterations` *= 500000*<a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.set_existing_performance_iterations" class="headerlink" title="Permalink to this definition">¶</a>  

 `set_new_performance_columns` *= 50*<a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.set_new_performance_columns" class="headerlink" title="Permalink to this definition">¶</a>  

 `set_new_performance_rows` *= 5000*<a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.set_new_performance_rows" class="headerlink" title="Permalink to this definition">¶</a>  

 `shortDescription`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.shortDescription" class="headerlink" title="Permalink to this definition">¶</a>  
Returns a one-line description of the test, or None if no description has been provided.

The default implementation of this method returns the first line of the specified test method’s docstring.

 `skipTest`<span class="sig-paren">(</span>*reason*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.skipTest" class="headerlink" title="Permalink to this definition">¶</a>  
Skip this test.

 `subTest`<span class="sig-paren">(</span>*msg=&lt;object object&gt;*, *\*\*params*<span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.subTest" class="headerlink" title="Permalink to this definition">¶</a>  
Return a context manager that will return the enclosed block of code in a subtest identified by the optional message and keyword parameters. A failure in the subtest marks the test case as failed but resumes execution at the end of the enclosed block, allowing further test code to be executed.

 `tearDown`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.tearDown" class="headerlink" title="Permalink to this definition">¶</a>  

 `tearDownClass`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.tearDownClass" class="headerlink" title="Permalink to this definition">¶</a>  
Hook method for deconstructing the class fixture after running all tests in the class.

 `test_SA_init`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_SA_init" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_SA_init" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_as_dict`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_as_dict" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_by_position`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_by_position" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_by_position" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_column_count`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_column_count" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_columns_in_order`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_columns_in_order" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_columns_in_order" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_from_pandas`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_from_pandas" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_getter_fail_1`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_getter_fail_1" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_getter_lower_case`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_getter_lower_case" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_getter_lower_case" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_getter_mixed_case`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_getter_mixed_case" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_getter_mixed_case" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_getter_mixed_case_lower`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_getter_mixed_case_lower" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_getter_mixed_case_lower" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_getter_mixed_case_upper`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_getter_mixed_case_upper" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_getter_mixed_case_upper" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_getter_upper_case`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_getter_upper_case" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_getter_upper_case" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_init_iter_zip`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_init_iter_zip" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_init_iter_zip_b`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_init_iter_zip_b" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_init_iter_zip_b_columns`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_init_iter_zip_b_columns" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_performance_create`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_performance_create" class="headerlink" title="Permalink to this definition">¶</a>  
Establish a baseline of init performance to make sure it doesn’t get worse

 `test_performance_get`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_performance_get" class="headerlink" title="Permalink to this definition">¶</a>  
Establish a baseline of get performance to make sure it doesn’t get worse. We expect the extra checks we do here to make Row slower than OrderedDict.

 `test_performance_set_existing`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_performance_set_existing" class="headerlink" title="Permalink to this definition">¶</a>  
Establish a baseline of set existing value performance to make sure it doesn’t get worse We expect the extra checks we do here to make Row slower than OrderedDict.

 `test_performance_set_new`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_performance_set_new" class="headerlink" title="Permalink to this definition">¶</a>  
Establish a baseline of set new value performance to make sure it doesn’t get worse. We expect the extra checks we do here to make Row slower than OrderedDict.

 `test_remove_columns`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_remove_columns" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_remove_columns" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_rename_column`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_rename_column" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_rename_column" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_rename_columns`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_rename_columns" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_rename_columns" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_setter_lower_case`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_setter_lower_case" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_setter_lower_case" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_setter_mixed_case`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_setter_mixed_case" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_setter_mixed_case" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_setter_upper_case`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_setter_upper_case" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_setter_upper_case" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_subset_and_columns`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_subset_and_columns" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_subset_and_columns" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_transform_lower_case`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_transform_lower_case" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_transform_lower_case" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_transform_mixed_case`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_transform_mixed_case" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_transform_mixed_case" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_transform_mixed_case_lower`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_transform_mixed_case_lower" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_transform_mixed_case_lower" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_transform_mixed_case_upper`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_transform_mixed_case_upper" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_transform_mixed_case_upper" class="headerlink" title="Permalink to this definition">¶</a>  

 `test_transform_upper_case`<span class="sig-paren">(</span><span class="sig-paren">)</span><a href="_modules/bi_etl/tests/test_row_case_insensitive.md#TestRowCaseInsensitive.test_transform_upper_case" class="reference internal"><span class="viewcode-link">[source]</span></a><a href="#bi_etl.tests.test_row_case_insensitive.TestRowCaseInsensitive.test_transform_upper_case" class="headerlink" title="Permalink to this definition">¶</a>  

#### Previous topic

[bi\_etl.tests.test\_row module](bi_etl.tests.test_row.md "previous chapter")

#### Next topic

[bi\_etl.tests.test\_scheduler module](bi_etl.tests.test_scheduler.md "next chapter")

### Quick search

### Navigation

-   [index](genindex.md "General Index")
-   [modules](py-modindex.md "Python Module Index") |
-   [next](bi_etl.tests.test_scheduler.md "bi_etl.tests.test_scheduler module") |
-   [previous](bi_etl.tests.test_row.md "bi_etl.tests.test_row module") |
-   [bi\_etl 0.5.3 documentation](index.md) »
-   [bi\_etl](modules.md) »
-   [bi\_etl package](bi_etl.md) »
-   [bi\_etl.tests package](bi_etl.tests.md) »

© Copyright 2015, Derek Wood. Created using [Sphinx](http://sphinx-doc.org/) 1.5.4.
