"""
Created on Oct 9, 2015

@author: Derek Wood
"""
import io
from collections import defaultdict
from decimal import Context, ROUND_HALF_EVEN
from operator import itemgetter
from sys import stdout
from typing import Optional, Union

from bi_etl.components.etlcomponent import ETLComponent
from bi_etl.conversions import str2decimal, str2date
from bi_etl.scheduler.task import ETLTask
from bi_etl.utility import get_integer_places


# noinspection PyBroadException
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
    COLUMN_HEADERS_DICT = {
        'col': 'Column Name',
        'type': 'Data Type',
        'non_null_rows': 'Non-Null Rows',
        'cardinality': 'Cardinality',
        'msg': 'Message',
        'present': 'Rows with this column',
        'not_present_on_rows': 'Rows without this column',
        'most_common_value': 'Most Common Value',
    }
    COLUMN_HEADERS_FORMAT = "{col:45}  {type:20} {non_null_rows:>15} {cardinality:>15}   {msg}"
    COLUMN_HEADERS = COLUMN_HEADERS_FORMAT.format(**COLUMN_HEADERS_DICT)
    DEFAULT_FORMAT = "{col:45}  {type:20} {non_null_rows:15,} {cardinality:15,}   {msg}"
    EQUALS_FORMAT = "{col:45} type = {type:20} non_null_rows={non_null_rows:15,} cardinality={cardinality:15,} {msg}"
    PIPE_FORMAT = "{col}|{type}|{present}|{not_present_on_rows}|{non_null_rows}|{cardinality}|{most_common_value}|{msg}"
    PIPE_HEADERS = PIPE_FORMAT.format(**COLUMN_HEADERS_DICT)

    class DataType(object):
        def __init__(self, name, length=None, precision=None, fmt=None):
            self.name = name
            self.length = length
            self.precision = precision
            self.format = fmt

        def __repr__(self):
            return f"{self.name}({self.length},{self.precision},fmt={self.format})"

        def __str__(self):
            if self.length is None and self.format is None:
                return self.name
            if self.format is not None:
                return f"{self.name}({self.format})"
            elif self.precision is None:
                return f"{self.name}({self.length})"
            else:
                return f"{self.name}({self.length},{self.precision})"

    def __init__(self,
                 task: Optional[ETLTask] = None,
                 logical_name: str = 'DataAnalyzer',
                 **kwargs
                 ):
        # Don't pass kwargs up. They should be set here at the end
        super(DataAnalyzer, self).__init__(task=task, logical_name=logical_name)

        self.float_as_decimal = False

        self.rows_processed = 0
        self.column_names = list()
        self.column_valid_values = dict()
        self.column_data_types = dict()
        self.column_data_types_counts = dict()
        self.column_names_consistent = True
        self.new_columns_after_first_row = False
        self.column_present_count = dict()
        self.column_not_null = dict()
        self.duplicate_column_names = dict()
        # Row level storage
        self.row_column_name_set = set()

        # Should be the last call of every init
        self.set_kwattrs(**kwargs)

    def _reset_storage(self):
        self.rows_processed = 0
        self.column_names = list()
        self.column_valid_values = dict()
        self.column_data_types = dict()
        self.column_data_types_counts = dict()
        self.column_names_consistent = True
        self.new_columns_after_first_row = False
        self.column_present_count = dict()
        self.column_not_null = dict()
        self.duplicate_column_names = dict()
        # Row level storage
        self.row_column_name_set = set()

    def __iter__(self):
        return None

    def close(self, error: bool = False):
        if not self.is_closed:
            super(DataAnalyzer, self).close(error=error)
            self._reset_storage()

    def _type_from_value(self, value):
        if isinstance(value, str):
            # Look for numbers in text
            try:
                dec = str2decimal(value)
                # If the value has no fractional digits, return integer.
                # Note: We could use _isinteger() however that calls 1.0 an integer.
                # Whereas a file with 1.0 values indicates possible fractional values
                # Decimal('1.0').as_tuple().exponent returns -1
                # or 
                # Decimal('1.0')._exp returns -1
                (_, digits, exponent) = dec.as_tuple()
                if exponent >= 0:
                    return DataAnalyzer.DataType(name='Integer',
                                                 length=len(digits) + exponent,
                                                 )
                else:
                    return DataAnalyzer.DataType(name='Decimal',
                                                 length=max(len(digits),
                                                            abs(exponent)),
                                                 precision=abs(exponent),
                                                 )
            except Exception:
                pass

            # Look for date in text
            if '-' in value:
                if ':' in value:
                    for dt_format in [
                                      "%Y-%m-%d %H:%M", "%m-%d-%Y %H:%M", "%d-%m-%Y %H:%M",
                                      "%Y-%m-%d %H:%M:%S", "%m-%d-%Y %H:%M:%S", "%d-%m-%Y %H:%M:%S",
                                      "%Y-%m-%d %H:%M:%S.%f", "%m-%d-%Y %H:%M:%S.%f", "%d-%m-%Y %H:%M:%S.%f",
                                      "%Y-%m-%d %I:%M %p", "%m-%d-%Y %I:%M %p", "%d-%m-%Y %I:%M %p",
                                      "%Y-%m-%d %I:%M:%S %p", "%m-%d-%Y %I:%M:%S %p", "%d-%m-%Y %I:%M:%S %p",
                                      ]:
                        # noinspection PyBroadException
                        try:
                            _ = str2date(value, dt_format=dt_format)
                            dt_type = DataAnalyzer.DataType(name="Date")
                            dt_type.format = dt_format
                            dt_type.length = len(value)
                            return dt_type
                        except Exception:
                            pass
                else:  # No time in value
                    for dt_format in ["%Y-%m-%d", "%m-%d-%Y", "%d-%m-%Y"]:
                        try:
                            _ = str2date(value, dt_format=dt_format)
                            dt_type = DataAnalyzer.DataType(name="Date")
                            dt_type.format = dt_format
                            dt_type.length = len(value)
                            return dt_type
                        except Exception:
                            pass
            elif '/' in value:
                if ':' in value:
                    for dt_format in [
                                      "%Y/%m/%d %H:%M", "%m/%d/%Y %H:%M", "%d/%m/%Y %H:%M",
                                      "%Y/%m/%d %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S",
                                      "%Y/%m/%d %H:%M:%S.%f", "%m/%d/%Y %H:%M:%S.%f", "%d/%m/%Y %H:%M:%S.%f",
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
                else:  # No time in value
                    for dt_format in ["%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y"]:
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
            return DataAnalyzer.DataType(name='Integer', length=get_integer_places(value))
        elif isinstance(value, float):
            if self.float_as_decimal:
                dec = Context(prec=16, rounding=ROUND_HALF_EVEN).create_decimal_from_float(value).normalize()
                (_, digits, exponent) = dec.as_tuple()
                if exponent >= 0:
                    return DataAnalyzer.DataType(name='Integer',
                                                 length=len(digits) + exponent,
                                                 )
                else:
                    return DataAnalyzer.DataType(name='Decimal',
                                                 length=max(len(digits),
                                                            abs(exponent)
                                                            ),
                                                 precision=abs(exponent))

        return DataAnalyzer.DataType(name=type(value).__name__)

    def next_row(self):
        self.row_column_name_set = set()
        self.rows_processed += 1

    @staticmethod
    def null_safe_max(a: Union[int, None], b: Union[int, None]) -> Union[int, None]:
        if a is None:
            if b is None:
                return None
            else:
                return b
        else:
            if b is None:
                return a
            else:
                return max(a, b)

    def analyze_column(self, column_name, column_value, column_number=None):
        self.column_present_count[column_name] = self.column_present_count.get(column_name, 0) + 1

        # Process column names
        if column_number is not None:
            if len(self.column_names) < column_number:
                if column_name not in self.column_names:
                    self.column_names.append(column_name)
                else:
                    self.column_names_consistent = False
            else:
                if self.column_names[column_number - 1] != column_name:
                    self.column_names_consistent = False
                    if column_name not in self.column_names:
                        self.column_names.append(column_name)
        else:
            if column_name not in self.column_names:
                self.column_names.append(column_name)

        if column_name not in self.row_column_name_set:
            self.row_column_name_set.add(column_name)
        else:
            self.duplicate_column_names.get(column_name, set()).add(column_number)

        # Process column_valid_values
        if column_name not in self.column_valid_values:
            self.column_valid_values[column_name] = dict()
            if self.rows_processed > 0:
                self.new_columns_after_first_row = True
        value = column_value
        try:
            hash(column_value)
        except TypeError:  # un-hashable type
            value = str(column_value)

        self.column_valid_values[column_name][value] = self.column_valid_values[column_name].get(value, 0) + 1

        # Process column_data_types
        if column_value is not None:
            self.column_not_null[column_name] = self.column_not_null.get(column_name, 0) + 1

            existing_type = self.column_data_types.get(column_name)
            row_type = self._type_from_value(column_value)

            if column_name not in self.column_data_types_counts:
                self.column_data_types_counts[column_name] = defaultdict(int)
            self.column_data_types_counts[column_name][row_type.name] += 1

            new_type = existing_type
            if existing_type is None:
                new_type = row_type
            else:
                if existing_type.name in ['str', 'unicode', 'bytes']:
                    new_type.length = self.null_safe_max(row_type.length, existing_type.length)
                elif existing_type.name == 'Date':
                    if row_type.name == 'Date':
                        new_type.length = self.null_safe_max(row_type.length, existing_type.length)
                        if isinstance(existing_type.format, dict):
                            # Add one to the counter for this format
                            new_type.format[row_type.format] = new_type.format.get(row_type.format, 0) + 1
                        elif row_type.format != existing_type.format:
                            fmts = dict()
                            fmts[existing_type.format] = self.rows_processed - 1
                            fmts[row_type.format] = 1
                            new_type.format = fmts
                    elif row_type.name in ['str', 'unicode', 'bytes']:
                        new_type = row_type
                        new_type.length = self.null_safe_max(row_type.length, existing_type.length)
                elif existing_type.name == 'Integer':
                    if row_type.name == 'Integer':
                        new_type.length = self.null_safe_max(row_type.length, existing_type.length)
                    elif row_type.name == 'Decimal':
                        new_type = row_type
                        new_type.length = self.null_safe_max(row_type.length, existing_type.length)
                    else:
                        new_type = DataAnalyzer.DataType(name='str')
                        new_type.length = self.null_safe_max(row_type.length, existing_type.length)
                else:
                    if row_type.name != existing_type.name:
                        new_type = DataAnalyzer.DataType(name='str')
                        new_type.length = self.null_safe_max(row_type.length, existing_type.length)
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
                       columns_header: str = None,
                       columns_out_fmt: str = None
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
        columns_header:
            The table header for the columns list
        columns_out_fmt:
            The format to use for lines
        """
        if out is None:
            out = stdout

        if columns_out_fmt is None:
            columns_out_fmt = self.DEFAULT_FORMAT

        if columns_header is None:
            columns_header = self.COLUMN_HEADERS

        print(f"\nRows processed = {self.rows_processed:,}", file=out)
        if not self.column_names_consistent:
            print("**** COLUMN NAMES NOT CONSISTENT IN ALL ROWS", file=out)
        if self.new_columns_after_first_row:
            print("**** NEW COLUMN NAME APPEARED AFTER FIRST ROW", file=out)

        print("Columns:", file=out)
        print(columns_header, file=out)
        column_dict = dict()
        col_cnt = 0
        for col in self.column_names:
            col_cnt += 1

            if col not in column_dict:
                column_dict[col] = list()
            column_dict[col].append(col_cnt)

            msg = ""
            not_present_on_rows = self.rows_processed - self.column_present_count.get(col, 0)
            if not_present_on_rows > 0:
                msg += f" [Not present on {not_present_on_rows:,} rows]"

            most_common_value = None
            vv = self.column_valid_values.get(col)
            if vv is not None:
                vv_list = sorted(list(vv.items()), key=itemgetter(1), reverse=True)
                if len(vv_list) >= 1:
                    most_common_value = vv_list[0]

            print(columns_out_fmt.format(
                col=col,
                type=str(self.column_data_types.get(col)),
                present=self.column_present_count.get(col, 0),
                not_present_on_rows=self.rows_processed - self.column_present_count.get(col, 0),
                non_null_rows=self.column_not_null.get(col, 0),
                cardinality=len(self.column_valid_values.get(col, list())),
                most_common_value=most_common_value,
                msg=msg,
            ),
                file=out
            )

        print("", file=out)
        if len(self.duplicate_column_names) > 0:
            print("Duplicate column names:", file=out)
            for col_name, col_positions in self.duplicate_column_names.items():
                print(f"Column {col_name} appears in positions {col_positions}", file=out)

        print("", file=out)
        print("Columns Valid Values:", file=out)
        col_cnt = 0
        for col in self.column_names:
            col_cnt += 1
            if col_cnt > 1:
                print("", file=out)
            vv = self.column_valid_values.get(col)
            if vv is not None:
                vv_list = sorted(list(vv.items()), key=itemgetter(1), reverse=True)
                print(f"{col} (col {col_cnt}) Cardinality {len(vv):,} Apparent type {str(self.column_data_types.get(col))} Source Type {type(vv_list[0][0]).__name__} :", file=out)
                for (v, freq) in vv_list[:valid_value_limit]:
                    try:
                        v_str = str(v)
                        if len(v_str) <= 60:
                            print(f"\t{v_str:60}\tFreq = {freq:,}", file=out)
                        else:
                            print(f"\t{v_str[:60]}\tFreq = {freq:,} (Value truncated actual width = {len(v_str)} chars)", file=out)
                    except Exception as e:
                        print(e, file=out)
                        print(f"Freq = {freq:,}", file=out)
                if len(vv) > valid_value_limit:
                    print("\t--More values not printed--", file=out)
            else:
                print(f"{col} (col {col_cnt}) had no data values", file=out)

            print('', file=out)
            if col in self.column_data_types_counts:
                type_counts = self.column_data_types_counts[col]
                print("\tApparent Data Types:", file=out)
                for row_type, freq in sorted(list(type_counts.items()), key=itemgetter(1), reverse=True):
                    print(f'\t\t{freq:,} rows appear to be {row_type}', file=out)

    def get_analysis_str(self) -> str:
        analysis_block = io.StringIO()
        self.print_analysis(out=analysis_block)
        return analysis_block.getvalue()

    def log_analysis(self):
        self.log.info(self.get_analysis_str())
