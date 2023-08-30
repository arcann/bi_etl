"""
Created on Sep 17, 2014

"""
import csv
import logging
import os
import typing

from sqlalchemy import Column

from bi_etl.components.etlcomponent import ETLComponent
from bi_etl.components.row.row import Row
from bi_etl.scheduler.task import ETLTask
from bi_etl.statistics import Statistics

__all__ = ['W3CReader']

# Only quote none is really needed here, QUOTE_MINIMAL is the default.
# The other quoting levels are only relevant to the Writer
QUOTE_NONE = csv.QUOTE_NONE
QUOTE_MINIMAL = csv.QUOTE_MINIMAL


class W3CReader(ETLComponent):
    """
    W3CReader reads W3c based log files

    Args:
        task: The  instance to register in (if not None)

        filedata:
            The file to parse as delimited. If str then it's assumed to be a filename.
            Otherwise it's assumed to be a file object.

        encoding:
            The encoding to use when opening the file,
            if it was a filename and not already opened.
            Default is None which becomes the Python default encoding

        errors:
            The error handling to use when opening the file
            (if it was a filename and not already opened)
            Default is 'strict'
            See above for valid errors values.

        logical_name:
            The logical name of this source. Used for log messages.

    Attributes:
        column_names: list
            The names to use for columns
    """

    def __init__(self,
                 task: ETLTask,
                 filedata: typing.Union[typing.TextIO, str],
                 encoding: str = None,
                 errors: str = 'strict',
                 logical_name: str = None,
                 **kwargs
                 ):

        self.log = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

        self.__close_file = False

        # We have to check / open the file here to get the name for the logical name
        if isinstance(filedata, str):
            self.log.info(f"Opening file {filedata}")
            self.file = open(filedata,
                             mode='rt',
                             newline='',
                             encoding=encoding,
                             errors=errors
                             )
            self.__close_file = True
        else:
            self.log.info(f"Treating input as file object {filedata}")
            self.file = filedata

        if logical_name is None:
            try:
                logical_name = os.path.basename(self.file.name)
            except AttributeError:
                logical_name = str(self.file)

        self.read_all = True
        self._file_read = False

        self._line_num = 0
        self._pending_lines = list()

        # Don't pass kwargs up. They should be set here at the end
        super().__init__(
            task=task,
            logical_name=logical_name,
        )

        # Should be the last call of every init
        self.set_kwattrs(**kwargs)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(task={self.task},logical_name={self.logical_name}," 
            f"filedata={self.file},primary_key={self.primary_key},column_names={self.column_names})"
        )

    @property
    def line_num(self):
        """
        The current line number in the source file.
        line_num differs from rows_read in that rows_read deals with rows that would be returned to the caller
        """
        return self._line_num

    def _read_line(self) -> typing.Union[str, None]:
        if len(self._pending_lines) == 0:
            if self.read_all:
                self._pending_lines = self.file.readlines()
                if self._pending_lines:
                    line = self._pending_lines.pop(0)
                    self._line_num += 1
                    return line.strip()
                else:
                    return None
            else:
                line = self.file.readline()
                if line:
                    self._line_num += 1
                return line.strip()
        else:
            return self._pending_lines.pop(0).strip()

    def _read_line_no_comments(self) -> typing.Union[str, None]:
        line = self._read_line()
        while line is not None and line[0] == '#':
            line = self._read_line()
        return line

    def _obtain_column_names(self):
        """
        Get the column names from the file. ETLComponent only call this if self._column_names is None:
        """
        header_found = False
        while not header_found:
            line = self._read_line()
            if line is None:
                raise ValueError("EOF found before column names")
            if line.startswith('#Fields:'):
                self.column_names = line.split(' ')[1:]
                header_found = True
            elif not line.startswith('#'):
                raise ValueError("Data lines started before column names")
        if self.trace_data:
            self.log.debug(f"Column names read: {self.column_names}")

    def where(
            self,
            criteria_list: typing.Optional[list] = None,
            criteria_dict: typing.Optional[dict] = None,
            order_by: typing.Optional[list] = None,
            column_list: typing.List[typing.Union[Column, str]] = None,
            exclude_cols: typing.List[typing.Union[Column, str]] = None,
            use_cache_as_source: typing.Optional[bool] = None,
            progress_frequency: typing.Optional[int] = None,
            stats_id: typing.Optional[str] = None,
            parent_stats: typing.Optional[Statistics] = None,
    ) -> typing.Iterable[Row]:
        """

        Parameters
        ----------
        criteria_list:
            *Not Supported for this component.*
        criteria_dict:
            Dict keys should be column names, values are checked for equality with the column on each row.
        order_by:
            *Not Supported for this component.*
        column_list:
            List of columns names
        exclude_cols
        use_cache_as_source
        progress_frequency
        stats_id
        parent_stats

        Returns
        -------
        rows

        """
        return super().where(
            criteria_list=criteria_list,
            criteria_dict=criteria_dict,
            order_by=order_by,
            column_list=column_list,
            exclude_cols=exclude_cols,
            use_cache_as_source=use_cache_as_source,
            progress_frequency=progress_frequency,
            stats_id=stats_id,
            parent_stats=parent_stats,
        )

    def _raw_rows(self):
        len_column_names = len(self.column_names)
        try:
            this_iteration_header = self.full_iteration_header
            # noinspection PyTypeChecker
            done = False
            while not done:
                line = self._read_line_no_comments()
                if line is None:
                    done = True
                else:
                    if line != '':
                        # Convert empty strings to None to be consistent with DB reads
                        row = line.split(' ')
                        d = self.Row(data=row[:len_column_names], iteration_header=this_iteration_header)

                        len_row = len(row)
                        if len_column_names < len_row:
                            raise ValueError(
                                f'Row {self.line_num} has extra columns Row has {len_row} > Header has {len_column_names}: "{line}"')
                        elif len_column_names > len_row:
                            if self.warnings_issued < self.warnings_limit:
                                self.warnings_issued += 1
                                self.log.warning(
                                    f'Row {self.line_num} is missing columns. Row has {len_row} < Header has {len_column_names}: "{line}"')
                            for key in self.column_names[len_row:]:
                                d[key] = None
                        yield d
        finally:
            pass

    def close(self, error: bool = False):
        """
        Close the file
        """
        if not self.is_closed:
            if self.__close_file:
                self.file.close()
            super().close(error=error)
