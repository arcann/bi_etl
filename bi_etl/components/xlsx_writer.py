"""
Created on Apr 2, 2015
"""
from typing import Union

from openpyxl import load_workbook, Workbook

from bi_etl.components.row.row import Row
from bi_etl.components.xlsx_reader import XLSXReader
from bi_etl.scheduler.task import ETLTask
from bi_etl.statistics import Statistics

__all__ = ['XLSXWriter']


class XLSXWriter(XLSXReader):
    """
    XLSXReader will read rows from an Microsoft Excel XLSX formatted sheet.
    
    Parameters
    ----------
    task: ETLTask
        The  instance to register in (if not None)
    
    file_name: str
        The file_name to parse as xlsx.
        
    logical_name: str
        The logical name of this source. Used for log messages.

    Attributes
    ----------
    column_names: list
        The names to use for columns
        
    header_row: int
        The sheet row to read headers from. Default = 1.
    
    start_row: int
        The first row to parse for data. Default = header_row + 1 
    
    workbook: :class:`openpyxl.workbook.workbook.Workbook`
        The workbook that was opened.
        
    log_first_row : boolean
        Should we log progress on the the first row read. *Only applies if Table is used as a source.*
        (inherited from ETLComponent)
        
    max_rows : int, optional
        The maximum number of rows to read. *Only applies if Table is used as a source.*
        (inherited from ETLComponent)
        
    primary_key: list
        The name of the primary key column(s). Only impacts trace messages.  Default=None.
        (inherited from ETLComponent)
    
    progress_frequency: int
        How often (in seconds) to output progress messages. None for no progress messages.
        (inherited from ETLComponent)
    
    progress_message: str
        The progress message to print. Default is ``"{logical_name} row # {row_number}"``.
        Note ``logical_name`` and ``row_number`` subs.
        (inherited from ETLComponent)
        
    restkey: str
        Column name to catch long rows (extra values).
        
    restval: str
        The value to put in columns that are in the column_names but 
        not present in a given row (missing values).     
    """
    def __init__(self,
                 task: ETLTask,
                 file_name: str,
                 logical_name: str = None,
                 write_only: bool = True,
                 **kwargs
                 ):
        super().__init__(
            task=task,
            file_name=file_name,
            logical_name=logical_name,
        )
        self.headers_written = False
        self.write_only = write_only
        self._insert_cnt = 0
        self._insert_cnt_this_sheet = 0

        # Should be the last call of every init
        self.set_kwattrs(**kwargs)

    def __repr__(self):
        return "XLSXWriter({})".format(self.logical_name)

    @property
    def workbook(self):
        if self._workbook is None:
            if self.write_only:
                self._workbook = Workbook(write_only=True)
            else:
                self._workbook = load_workbook(filename=self.file_name, read_only=False)
        return self._workbook

    def set_active_worksheet_by_name(self, sheet_name):
        if sheet_name not in self.workbook:
            self._active_worksheet = self.workbook.create_sheet(sheet_name)
            self._insert_cnt_this_sheet = 0
        else:
            self._active_worksheet = self.workbook[sheet_name]
            self._column_names = None
            self._insert_cnt_this_sheet = 0

    def _obtain_column_names(self):
        raise ValueError(f'Column names must be explicitly set on {self}')

    def write_header(self):
        if self.column_names is None:
            raise ValueError("insert called before column_names set (or possibly column_names needs to be set after set_active_worksheet_by_name call.")
        self.active_worksheet.append(self.column_names)
        self.headers_written = True

    def insert_row(self,
                   source_row: Row,  # Must be a single row
                   stat_name: str = 'insert',
                   parent_stats: Statistics = None,
                   ):
        """
        Inserts a row into the database (batching rows as batch_size)

        Parameters
        ----------
        source_row
            The row with values to insert
        stat_name
        parent_stats

        Returns
        -------
        new_row
        """
        stats = self.get_stats_entry(stat_name, parent_stats=parent_stats)
        stats.timer.start()

        # row_values = [source_row[col] for col in self.column_names]

        if not self.headers_written:
            self.write_header()

        self.active_worksheet.append(source_row.values())

        self._insert_cnt += 1
        self._insert_cnt_this_sheet += 1

        stats.timer.stop()

    def insert(self,
               source_row: Union[Row, list],  # Could also be a whole list of rows
               parent_stats: Statistics = None,
               **kwargs
               ):
        """
        Insert a row or list of rows in the table.

        Parameters
        ----------
        source_row: :class:`Row` or list thereof
            Row(s) to insert
        parent_stats: bi_etl.statistics.Statistics
            Optional Statistics object to nest this steps statistics in.
            Default is to place statistics in the ETLTask level statistics.
        """

        if isinstance(source_row, list):
            for row in source_row:
                self.insert_row(
                    row,
                    parent_stats=parent_stats,
                    **kwargs
                )
        else:
            self.insert_row(
                 source_row,
                 parent_stats=parent_stats,
                 **kwargs
             )
            
    def close(self):
        if self.has_workbook_init():
            # add_table is not currently working.

            # table_range = CellRange(
            #     min_col=1, max_col=len(self.column_names),
            #     min_row=1, max_row=self._insert_cnt_this_sheet +1
            # )
            # table_name = f"{self.active_worksheet.title}_table".replace(' ', '_')
            # tab = Table(displayName=table_name, ref=table_range.coord)
            #
            # # Add a default style with striped rows and banded columns
            # style = TableStyleInfo(
            #     name='TableStyleMedium2',
            #     showRowStripes=True
            # )
            # tab.tableStyleInfo = style
            # self.active_worksheet.add_table(tab)

            self.workbook.save(filename=self.file_name)
        super().close()