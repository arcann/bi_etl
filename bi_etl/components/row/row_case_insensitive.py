
"""
Created on Sep 17, 2014

@author: Derek Wood
"""
from bi_etl.components.row.row_status import RowStatus

from bi_etl.components.row.row_iteration_header import RowIterationHeader
from bi_etl.utility import dict_to_str
from bi_etl.components.row.row import Row
from sqlalchemy.sql.schema import Column


class RowCaseInsensitive(Row):
    """
    Replacement for core SQL Alchemy, CSV or other dictionary based rows.
    Handles converting column names (keys) between upper and lower case.
    Handles column names (keys) that are SQL Alchemy column objects.
    Keeps order of the columns (see columns_in_order) 
    """
    # For performance with the Column to str conversion we keep a cache of converted values
    # The dict lookup tests as twice as fast as just the lower function
    __name_map_db = dict()

    def __init__(self,
                 iteration_header: RowIterationHeader,
                 data=None,
                 status: RowStatus = None,
                 allocate_space=True):
        super().__init__(data=data,
                         iteration_header=iteration_header,
                         status=status,
                         allocate_space=allocate_space
                         )

    @staticmethod
    def _get_name(input_name):
        if input_name in RowCaseInsensitive.__name_map_db:
            return RowCaseInsensitive.__name_map_db[input_name]
        else:
            # If the input_name is an SA Column use it's name.
            # In Python 2.7 to 3.4, isinstance is a lot faster than try-except or hasattr (which does a try)
            if isinstance(input_name, str):
                out_name = input_name.lower()
            elif isinstance(input_name, Column):
                out_name = input_name.name.lower()
            else:
                raise ValueError("Row column name must be str, unicode, or Column. Got {}".format(type(input_name)))
            RowCaseInsensitive.__name_map_db[input_name] = out_name
            return out_name

    def __repr__(self):
        return 'RowCaseInsensitive(name={},status={},primary_key={},\n{}'.format(self.name, self.status, self.primary_key, dict_to_str(self))
