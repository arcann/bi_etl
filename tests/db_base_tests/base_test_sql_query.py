"""
Created on Jan 22, 2016

@author: Derek Wood
"""
from unittest import TestSuite

from bi_etl.components.sqlquery import SQLQuery
from bi_etl.components.table import Table
from tests.db_base_tests.base_test_database import BaseTestDatabase


def load_tests(loader, standard_tests, pattern):
    # Filter out all
    suite = TestSuite()
    return suite


# pylint: disable=missing-docstring, protected-access


class BaseTestSQLQuery(BaseTestDatabase):

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
                print(sql_row.values())
                expected_row = expected_row.subset(keep_only=['id', 'text_col', 'date_col', 'float_col'])
                expected_row['date_col'] = self._sql_query_date_conv(expected_row['date_col'])
                print(expected_row.values())
                self._compare_rows(expected_row, actual_row=sql_row)
