"""
Created on Jan 22, 2016

@author: Derek Wood
"""
import enum
import logging
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from decimal import Decimal
from unittest import mock

import sqlalchemy
from sqlalchemy import exc
from sqlalchemy.exc import DatabaseError
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import BOOLEAN
from sqlalchemy.sql.sqltypes import Date
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.sql.sqltypes import Enum
from sqlalchemy.sql.sqltypes import Float
from sqlalchemy.sql.sqltypes import Integer
from sqlalchemy.sql.sqltypes import Interval
from sqlalchemy.sql.sqltypes import LargeBinary
from sqlalchemy.sql.sqltypes import NUMERIC
from sqlalchemy.sql.sqltypes import Numeric
from sqlalchemy.sql.sqltypes import REAL
from sqlalchemy.sql.sqltypes import String
from sqlalchemy.sql.sqltypes import TEXT
from sqlalchemy.sql.sqltypes import Time

from bi_etl.components.row.row import Row
from bi_etl.components.row.row_iteration_header import RowIterationHeader
from bi_etl.components.sqlquery import SQLQuery
from bi_etl.components.table import Table
from bi_etl.utility import dict_to_str
from tests.db_base_tests._test_base_database import _TestBaseDatabase


# pylint: disable=missing-docstring, protected-access


class _TestSQLQuery(_TestBaseDatabase):

    def testInsertAndQuery(self):
        tbl_name = self._get_table_name('testInsertAndQuery')

        self._create_table_1(tbl_name)

        rows_to_insert = 20
        rows_to_select = 10
        with Table(
            self.task,
            self.mock_database,
            table_name=tbl_name
        ) as tbl:
            expected_rows = list()
            for row in self._gen_src_rows_1(rows_to_insert):
                tbl.insert_row(row)
                if row['id'] <= rows_to_select:
                    expected_rows.append(row)
            tbl.commit()
        del row

        with SQLQuery(
            self.task,
            self.mock_database,
            f"""
            SELECT
                id,
                text_col,
                date_col,
                float_col
            FROM "{tbl_name}"
            WHERE id <= {rows_to_select}
            ORDER BY id desc
            """
        ) as sql:
            expected_rows = reversed(expected_rows)

            # Validate data
            for sql_row, expected_row in zip(sql, expected_rows):
                print(sql_row.values_in_order())
                expected_row = expected_row.subset(keep_only=['id', 'text_col', 'date_col', 'float_col'])
                expected_row['date_col'] = self._sql_query_date_conv(expected_row['date_col'])
                print(expected_row.values_in_order())
                self._compare_rows(expected_row, actual_row=sql_row)
