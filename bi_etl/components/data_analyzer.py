"""
Created on Oct 9, 2015

@author: woodd
"""
import io
from sys import stdout
from decimal import Context, ROUND_HALF_EVEN

from bi_etl.components.etlcomponent import ETLComponent
from bi_etl.conversions import str2decimal, str2date
from bi_etl.utility import getIntegerPlaces
from operator import itemgetter


class DataAnalyzer(ETLComponent):
    """
    Class that analyzes the data rows passed to it. 
    * Tracks distinct columns passed in
    * Tracks datatype of each column
    * Tracks valid values of each column
    
    Parameters
    ----------
    task: ETLTask
        The  instance to register in (if not None)
    logical_name: str
        The logical name of this source. Used for log messages.
    """
    
    DEFAULT_FORMAT = "{col:30} type = {type:20} non_null_rows={non_null_rows:15,} cardinality={cardinality:15,}{msg}"
    PIPE_FORMAT = "{col}|{type}|{present}|{not_present_on_rows}|{non_null_rows}|{cardinality}|{most_common_value}|{msg}"
    
    class DataType(object):
        def __init__(self, name, length=None, precision=None, fmt=None):
            self.name = name
            self.length = length
            self.precision = precision 
            self.format = fmt
           
        def __repr__(self):
            return "{}({},{},fmt={})".format(self.name, self.length, self.precision, self.format)    
            
        def __str__(self):
            if self.length is None and self.format is None:
                return self.name
            if self.format is not None:
                return "{}({})".format(self.name, self.format) 
            elif self.precision is None: 
                return "{}({})".format(self.name, self.length)
            else:
                return "{}({},{})".format(self.name, self.length, self.precision)
    
    def __init__(self,
                 task = None,
                 logical_name = 'DataAnalyzer',
                 **kwargs
                 ):
        ## Don't pass kwargs up. They should be set here at the end
        super(DataAnalyzer, self).__init__(task=task, logical_name=logical_name) 
        self._init_storage()
        self.float_as_decimal = False
        
        ## Should be the last call of every init            
        self.set_kwattrs(**kwargs)
        
    def _init_storage(self):
        self.rows_processed = 0
        self.column_names = list()
        self.column_valid_values = dict()
        self.column_data_types = dict()        
        self.column_names_consistent = True
        self.new_columns_after_first_row = False
        self.column_present_count = dict()
        self.column_not_null = dict()        
        self.duplicate_column_names = dict()
        ## Row level storage
        self.row_column_name_set = set()
    
    def __iter__(self):
        return None    
        
    def close(self):        
        super(DataAnalyzer, self).close()
        self._init_storage()
        
    def _type_from_value(self, value):
        if isinstance(value, str):            
            ## Look for numbers in text
            try:
                dec = str2decimal(value)
                ## If the value has no fractional digits, return integer.
                ## Note: We could use _isinteger() however that calls 1.0 an integer. 
                ## Whereas a file with 1.0 values indicates possible fractional values
                # Decimal('1.0').as_tuple().exponent returns -1
                # or 
                # Decimal('1.0')._exp returns -1
                (_, digits, exponent) = dec.as_tuple() 
                if exponent >= 0:
                    return DataAnalyzer.DataType(name='Integer', length= len(digits) + exponent)                                  
                else:
                    return DataAnalyzer.DataType(name='Decimal', length= max(len(digits),abs(exponent)), precision= abs(exponent))
            except Exception:
                pass
            
            ## Look for date in text            
            if '-' in value:
                for dt_format in ["%Y-%m-%d", "%m-%d-%Y", "%d-%m-%Y", 
                                  "%Y-%m-%d %H:%M", "%m-%d-%Y %H:%M", "%d-%m-%Y %H:%M",
                                  "%Y-%m-%d %H:%M:%S", "%m-%d-%Y %H:%M:%S", "%d-%m-%Y %H:%M:%S",
                                  "%Y-%m-%d %I:%M %p", "%m-%d-%Y %I:%M %p", "%d-%m-%Y %I:%M %p",
                                  "%Y-%m-%d %I:%M:%S %p", "%m-%d-%Y %I:%M:%S %p", "%d-%m-%Y %I:%M:%S %p",
                                 ]:
                    try:
                        _ = str2date(value, dt_format=dt_format)
                        dt_type = DataAnalyzer.DataType(name="Date")
                        dt_type.format = dt_format
                        dt_type.length = len(value)
                        return dt_type 
                    except Exception:
                        pass          
            if '/' in value:
                for dt_format in ["%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y", 
                                  "%Y/%m/%d %H:%M", "%m/%d/%Y %H:%M", "%d/%m/%Y %H:%M",
                                  "%Y/%m/%d %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S",
                                  "%Y/%m/%d %I:%M %p", "%m/%d/%Y %I:%M %p", "%d/%m/%Y %I:%M %p",
                                  "%Y/%m/%d %I:%M:%S %p", "%m/%d/%Y %I:%M:%S %p", "%d/%m/%Y %I:%M:%S %p",
                                 ]:
                    try:
                        _ = str2date(value, dt_format=dt_format)
                        dt_type = DataAnalyzer.DataType(name="Date")
                        dt_type.format = dt_format
                        dt_type.length = len(value)
                        return dt_type 
                    except Exception:
                        pass  
            # Else it's an actual string
            return DataAnalyzer.DataType(name=type(value).__name__, length=len(value))
        elif isinstance(value, int):
            return DataAnalyzer.DataType(name='Integer', length= getIntegerPlaces(value))
        elif isinstance(value, float):
            if self.float_as_decimal:
                dec = Context(prec=16, rounding=ROUND_HALF_EVEN).create_decimal_from_float(value).normalize()
                (_, digits, exponent) = dec.as_tuple()
                if exponent >= 0:
                    return DataAnalyzer.DataType(name='Integer', length= len(digits) + exponent)                                  
                else:
                    return DataAnalyzer.DataType(name='Decimal', length= max(len(digits),abs(exponent)), precision= abs(exponent))
        
        return DataAnalyzer.DataType(name=type(value).__name__)

    def next_row(self):
        self.row_column_name_set = set()
        self.rows_processed += 1
        
    def analyze_column(self, column_name, column_value, column_number=None):
        self.column_present_count[column_name] = self.column_present_count.get(column_name,0) + 1
            
        # Process column names
        if column_number is not None:
            if len(self.column_names) < column_number:
                self.column_names.append(column_name)
            else:
                if self.column_names[column_number-1] != column_name:
                    self.column_names_consistent = False
        else:
            if column_name not in self.column_names:
                self.column_names.append(column_name)
        
        if column_name not in self.row_column_name_set:
            self.row_column_name_set.add(column_name)
        else:
            self.duplicate_column_names.get(column_name,set()).add(column_number)                
              
        # Process column_valid_values
        if column_name not in self.column_valid_values:
            self.column_valid_values[column_name] = dict()
            if self.rows_processed != 1:
                self.new_columns_after_first_row = True
        value = column_value
        try:
            hash(column_value)
        except TypeError:  # unhashable type
            value = str(column_value)
        
        self.column_valid_values[column_name][value] = self.column_valid_values[column_name].get(value,0) + 1
        
        ## Process column_data_types
        if column_value is not None:
            self.column_not_null[column_name] = self.column_not_null.get(column_name,0) + 1
            
            existing_type = self.column_data_types.get(column_name)
            row_type = self._type_from_value(column_value)
            new_type = existing_type
            if existing_type is None:
                new_type = row_type
            else:
                if existing_type.name in ['str','unicode','bytes']:
                    new_type.length = max(row_type.length, existing_type.length)
                elif existing_type.name == 'Date':
                    if row_type.name == 'Date':
                        new_type.length = max(row_type.length, existing_type.length)
                        if isinstance(existing_type.format, dict):
                            ## Add one to the counter for this format
                            new_type.format[row_type.format] = new_type.format.get(row_type.format,0) + 1
                        elif row_type.format != existing_type.format:
                            fmts = dict()
                            fmts[existing_type.format] = self.rows_processed - 1
                            fmts[row_type.format] = 1
                            new_type.format = fmts
                    elif row_type.name in ['str','unicode','bytes']:
                        new_type = row_type
                        new_type.length = max(row_type.length, existing_type.length)
                elif existing_type.name == 'Integer':
                    if row_type.name == 'Integer':
                        new_type.length = max(row_type.length, existing_type.length)
                    elif row_type.name == 'Decimal':
                        new_type = row_type
                        new_type.length = max(row_type.length, existing_type.length)
                    else:
                        new_type = DataAnalyzer.DataType(name='str')
                        new_type.length = max(row_type.length, existing_type.length)
                else:
                    if row_type.name != existing_type.name:
                        new_type = DataAnalyzer.DataType(name='str')
                        new_type.length = max(row_type.length, existing_type.length)
            self.column_data_types[column_name] = new_type
        
    def analyze_row(self, row):
        """
        Analyze the data row passed in. Call this for all the rows that should be analyzed.
        """
        stats = self.get_stats_entry(stats_id='analyze_row')
        stats.timer.start()
                
        
        stats['rows processed'] = self.rows_processed
        column_number = 0
        for column_name in row.columns_in_order:
            column_number += 1
            column_value = row[column_name]
            self.analyze_column(column_name=column_name,
                                column_value=column_value,
                                column_number=column_number,
                                )
        self.next_row()            
        stats.timer.stop()

    def print_analysis(self,
                       out: io.TextIOBase = None,
                       valid_value_limit: int = 10,
                       out_fmt: str = DEFAULT_FORMAT
                       ):
        """
        Print the data analysis results.

        Parameters
        ----------
        out:
            The File to write the results to. Default=``stdout``
            valid_value_limit (int): How many valid values should be printed.
        valid_value_limit:
            The number of valid values to output
        out_fmt:
            The format to use for lines
        """
        if out is None:
            out = stdout
            
        print("\nRows processed = {}".format(self.rows_processed), file=out)
        if not self.column_names_consistent:
            print("**** COLUMN NAMES NOT CONSISTENT IN ALL ROWS", file=out)
        if self.new_columns_after_first_row:
            print("**** NEW COLUMN NAME APPEARED AFTER FIRST ROW", file=out)
        
        print("Columns:", file=out)
        column_dict = dict()
        col_cnt = 0
        for c in self.column_names:
            col_cnt += 1
            
            if c not in column_dict:
                column_dict[c] = list()
            column_dict[c].append(col_cnt)
            
            msg = ""
            not_present_on_rows = self.rows_processed - self.column_present_count.get(c,0)            
            if not_present_on_rows > 0:
                msg += " [Not present on {:,} rows]".format(not_present_on_rows) 
                    
            most_common_value=None
            vv = self.column_valid_values.get(c)                                            
            if vv is not None:
                vv_list = sorted(list(vv.items()), key=itemgetter(1), reverse= True)
                if len(vv_list) >= 1:                                       
                    most_common_value=vv_list[0]
                    
            
            print(out_fmt.format(col=c, 
                                 type=str(self.column_data_types.get(c)),
                                 present=self.column_present_count.get(c,0),
                                 not_present_on_rows = self.rows_processed - self.column_present_count.get(c,0),
                                 non_null_rows=self.column_not_null.get(c,0),
                                 cardinality=len(self.column_valid_values.get(c,list())),
                                 most_common_value=most_common_value,
                                 msg=msg,
                                 )
                  ,file=out
                 )

        print("", file=out)
        if len(self.duplicate_column_names) > 0:            
            print("Duplicate column names:", file=out)
            for col_name, col_positions in self.duplicate_column_names.items():
                print("Column {} appears in positions {}".format(col_name, col_positions), file=out)
        
        print("", file=out)
        print("Columns Valid Values:", file=out)
        col_cnt = 0            
        for c in self.column_names:
            col_cnt += 1
            if col_cnt > 1:
                print("", file=out)
            vv = self.column_valid_values.get(c)                                            
            if vv is not None:                
                print("{} (col {}) cardinality {}:".format(c, col_cnt, len(vv)), file=out)
                vv_list = sorted(list(vv.items()), key=itemgetter(1), reverse= True)
                for (v,freq) in vv_list[:valid_value_limit]:
                    try:
                        print("\t{}\tFreq={}".format(v, freq), file=out)
                    except Exception as e:
                        print(e, file=out)
                        print("Freq={}".format(freq), file=out)
                if len(vv) > valid_value_limit:
                    print("\t--More values not printed--", file=out)
            else:
                print("{} (col {}) had no data values".format(c, col_cnt), file=out)
            
        
        