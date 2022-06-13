"""
Created on Jan 27, 2016
"""
import os
import typing
import unittest
from datetime import timedelta, datetime
from enum import Enum

import sqlalchemy
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.schema import Index
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.sql.sqltypes import Integer
from sqlalchemy.sql.sqltypes import TEXT

from bi_etl.components.csvreader import CSVReader
from bi_etl.components.hst_table import HistoryTable
from bi_etl.components.row.row import Row
from bi_etl.components.table import Table
from bi_etl.conversions import str2datetime, str2date, str2time, str2int, str2decimal, str2float
from tests.db_base_tests._test_base_database import _TestBaseDatabase


class BeginDateSource(Enum):
    SYSTEM_TIME = 1
    IN_ROW = 2
    PARAMETER = 3


class _TestHstTable(_TestBaseDatabase):
    SUPPORTS_DECIMAL = False
    TABLE_PREFIX = 'hst_'
    TEST_COMPONENT = HistoryTable
    TEST_DATA_PATH = 'test_hst_table_data'

    # Override  _check_table_rows with a version that processes versioned records
    def _check_table_rows(
            self,
            expected_row_generator: typing.Iterator[Row],
            target_table: HistoryTable,
            special_check_values: typing.Dict[str, typing.Dict] = None,
            key_list: list = None,
            log_rows_found: bool = True,
            msg: str = None,
    ):
        if msg is None:
            msg = ''

        if key_list is None:
            key_list = target_table.natural_key
            if key_list is None:
                key_list = target_table.primary_key.copy()
                if target_table.begin_date_column in key_list:
                    key_list.remove(target_table.begin_date_column)
                if target_table.end_date_column in key_list:
                    key_list.remove(target_table.end_date_column)
            self.assertIsNotNone(
                key_list,
                f"Test definition error. key_list not provided and table {target_table} has no natural_key key"
            )

        rows_dict = dict()
        rows_cnt_dict = dict()
        actual_count = 0
        order_by_list = key_list.copy()
        order_by_list.append(target_table.begin_date_column)
        for row in target_table.order_by(order_by_list):
            actual_count += 1
            key = tuple([row[col] for col in key_list])

            if key in rows_dict:
                last_row = rows_dict[key][-1]
                rows_dict[key].append(row)
                rows_cnt_dict[key] += 1

                self.assertEqual(
                    timedelta(seconds=1),
                    row[target_table.begin_date_column] - last_row[target_table.end_date_column],
                    f"For key {key} row end dt {last_row[target_table.end_date_column]} "
                    f"is followed by begin dt {row[target_table.begin_date_column]} which is not 1 second later"
                )
            else:
                rows_dict[key] = [row]
                rows_cnt_dict[key] = 1

            if log_rows_found:
                if actual_count == 1:
                    self.log.debug(f"{target_table} result cols = | {'|'.join(row.columns_in_order)}")
                self.log.debug(f"{target_table} result row = | {'|'.join([str(s) for s in row.values_in_order()])}")

        self.assertEqual(
            sum(rows_cnt_dict.values()),
            actual_count,
            f"Test definition error. "
            f"Read {actual_count} rows but key based dict has {sum(rows_cnt_dict.values())} {msg}"
        )

        expected_count = 0
        for expected_row in expected_row_generator:
            expected_count += 1
            key = tuple([expected_row[col] for col in key_list])
            self.assertIn(key, rows_dict, f"\nKey combo {key} not found in actual table results")

            actual_row_list = rows_dict[key]
            self.assertGreater(
                len(actual_row_list), 0,
                f"No remaining actual rows to match with for key {key} {msg} (more versions expected than found)"
            )

            actual_row = actual_row_list.pop(0)
            try:
                self._compare_rows(
                    expected_row,
                    actual_row,
                    special_check_values,
                    msg=f"row key={key} {actual_row[target_table.begin_date_column]} {msg}"
                )
            except AssertionError as e:
                msg_parts = [e.args[0]]
                if len(actual_row_list) > 0:
                    msg_parts.append('-' * 80)
                    msg_parts.append(f"Remaining rows for {key} are:")
                    for row in actual_row_list:
                        msg_parts.append(f"{row}")
                        try:
                            self._compare_rows(
                                expected_row,
                                row,
                                special_check_values,
                                msg=f"row key={key} {actual_row[target_table.begin_date_column]} {msg}"
                            )
                            msg_parts.append(f"  No diffs to expected row!!")
                        except AssertionError as other_row_diffs:
                            other_diffs_str = '\n'.join([f"    {line}" for line in str(other_row_diffs).split('\n')])
                            msg_parts.append(f"  Diffs to expected row = {other_diffs_str}")
                else:
                    msg_parts.append(f"No other actual rows for {key}")
                e.args = ("\n".join(msg_parts),)
                raise

        self.assertEqual(
            expected_count,
            actual_count,
            f"Test result error. Read {actual_count} rows but expected {expected_count} rows {msg}"
        )

    def _get_column_list_table_1(
            self,
            use_type1: bool = False,
            use_type2: bool = False,
    ) -> typing.List[Column]:
        col_list = super()._get_column_list_table_1()
        if use_type1:
            col_list.extend([
                Column('type_1_srgt', Integer),
            ])
        if use_type2:
            col_list.extend([
                Column('type_2_srgt', Integer),
            ])
        col_list.extend([
            Column('nk_col1', Integer),
            Column('begin_date', DateTime, primary_key=True),
            Column('end_date', DateTime),
        ])
        return col_list

    def _create_index_table_1(self, sa_table) -> typing.List[sqlalchemy.schema.Index]:
        idx_1 = Index(
            f"{sa_table.name}_idx1",
            sa_table.c.id,
            sa_table.c.begin_date,
            unique=True
        )
        idx_1.create()

        idx_2 = Index(
            f"{sa_table.name}_idx2",
            sa_table.c.nk_col1,
            sa_table.c.begin_date,
            unique=True
        )
        idx_2.create()

        return [idx_1, idx_2]

    def _gen_src_rows_1(self, int_range: typing.Union[range, int]) -> typing.Iterator[Row]:
        for row in super()._gen_src_rows_1(int_range):
            yield row

    def _get_column_list_table_2(
            self,
            use_type1: bool = False,
            use_type2: bool = False,
    ) -> typing.List[Column]:
        col_list = super()._get_column_list_table_1()
        if use_type1:
            col_list.extend([
                Column('type_1_srgt', Integer),
            ])
        if use_type2:
            col_list.extend([
                Column('type_2_srgt', Integer),
            ])
        col_list.extend([
            Column('nk_col1', Integer),
            Column('nk_col2', TEXT),
            Column('begin_date', DateTime, primary_key=True),
            Column('end_date', DateTime),
        ])
        return col_list

    def _create_table_2(
            self,
            tbl_name,
            use_type1: bool = False,
            use_type2: bool = False,
    ) -> sqlalchemy.schema.Table:
        self.mock_database.drop_table_if_exists(tbl_name)
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            *self._get_column_list_table_2(
                use_type1,
                use_type2,
            )
        )
        sa_table.create()

        self._create_index_table_2(sa_table)

        return sa_table

    def _create_index_table_2(self, sa_table) -> typing.List[sqlalchemy.schema.Index]:
        idx_list = list()
        idx_1 = Index(
            f"{sa_table.name}_idx1",
            sa_table.c.id,
            sa_table.c.begin_date,
            unique=True
        )
        idx_1.create()
        idx_list.append(idx_1)

        idx_2 = Index(
            f"{sa_table.name}_idx2",
            sa_table.c.nk_col1,
            sa_table.c.nk_col2,
            sa_table.c.begin_date,
            unique=True
        )
        idx_2.create()
        idx_list.append(idx_2)

        return idx_list

    def _gen_src_rows_2(self, int_range: typing.Union[range, int]) -> typing.Iterator[Row]:
        for row in super()._gen_src_rows_1(int_range):
            row['nk_col1'] = row['id'] * 10
            row['nk_col2'] = f"AB_{row['id']}"
            yield row

    def testInsertAndIterate(self):
        tbl_name = self._get_table_name('testInsertAndIterate')

        self._create_table_1(tbl_name)

        rows_to_insert = 10

        with self.TEST_COMPONENT(
                self.task,
                self.mock_database,
                table_name=tbl_name) as tbl:
            tbl.begin_date_column = 'begin_date'
            tbl.end_date_column = 'end_date'
            for row in self._gen_src_rows_1(rows_to_insert):
                tbl.insert(row)
            tbl.commit()

            def gen_expected_rows() -> typing.Iterator[Row]:
                for new_row in self._gen_src_rows_1(rows_to_insert):
                    new_row['begin_date'] = tbl.default_begin_date
                    new_row['end_date'] = tbl.default_end_date
                    yield new_row

            # Validate data
            self._check_table_rows(
                expected_row_generator=gen_expected_rows(),
                target_table=tbl,
            )

        self.mock_database.drop_table_if_exists(tbl_name)

    def _transform_csv_row(self, csv_row: Row):
        if self.SUPPORTS_DECIMAL:
            csv_row.transform('numeric13_col', str2decimal, raise_on_not_exist=False)
            csv_row.transform('num_col', str2decimal, raise_on_not_exist=False)
        else:
            csv_row.transform('numeric13_col', str2float, raise_on_not_exist=False)
            csv_row.transform('num_col', str2float, raise_on_not_exist=False)
        csv_row.transform('id', str2int)
        csv_row.transform('int_col_2', str2int)
        csv_row.transform('datetime_col', str2datetime, '%Y-%m-%d %H:%M:%S')
        csv_row.transform('date_col', str2date, '%Y-%m-%d', raise_on_not_exist=False)
        csv_row.transform('time_col', str2time, '%H:%M:%S', raise_on_not_exist=False)
        large_binary_col = 'large_binary_col'
        if large_binary_col in csv_row:
            val = csv_row[large_binary_col]
            if val is not None:
                csv_row[large_binary_col] = val.encode('utf8')

    def _gen_rows_from_csv(
            self,
            csv_file: str,
            path: str = None,
            transform: bool = True,
    ) -> typing.Iterator[Row]:
        if path is None:
            path = self.TEST_DATA_PATH
        with CSVReader(
                self.task,
                os.path.join(self.get_package_path(), path, csv_file),
                encoding='utf-8',
        ) as test1_insert_expected:
            for row in test1_insert_expected:
                if transform:
                    self._transform_csv_row(row)
                yield row

    def _testInsertAndUpsert(
            self,
            load_cache: bool,
            tbl_name: str,
            use_type1: bool,
            use_type2: bool,
            check_for_deletes: bool,
            begin_date_source: BeginDateSource = BeginDateSource.SYSTEM_TIME,
    ):
        self._create_table_2(
            tbl_name,
            use_type1,
            use_type2,
        )

        with self.TEST_COMPONENT(
                self.task,
                self.mock_database,
                table_name=tbl_name) as tbl:
            tbl.begin_date_column = 'begin_date'
            tbl.end_date_column = 'end_date'
            tbl.delete_flag = 'delete_flag'
            if check_for_deletes:
                tbl.track_source_rows = True

            if use_type2:
                tbl.primary_key = ['type_2_srgt']
                tbl.auto_generate_key = True
                tbl.natural_key = ['text_col']
            if use_type1:
                tbl.type_1_surrogate = 'type_1_srgt'

            if load_cache:
                tbl.fill_cache()

            with CSVReader(
                self.task,
                os.path.join(self.get_package_path(), self.TEST_DATA_PATH, 'test1_insert.csv'),
            ) as insert_file:
                for source_row in insert_file:
                    self._transform_csv_row(source_row)
                    tbl.insert_row(source_row)
            tbl.commit()

            # Validate data
            self._check_table_rows(
                expected_row_generator=self._gen_rows_from_csv('test1_insert_expected.csv'),
                target_table=tbl,
                special_check_values=dict(
                    begin_date=dict(
                        default_begin_dt=tbl.default_begin_date,
                    ),
                    end_date=dict(
                        default_end_dt=tbl.default_end_date,
                    ),
                ),
                msg=f"{tbl_name} insert_expected_rows check",
            )

            # Upsert stage
            if load_cache:
                tbl.fill_cache()

            update_time = datetime(2001, 5, 23, 7, 59, 21)
            if begin_date_source == BeginDateSource.SYSTEM_TIME:
                # Mock get_current_time so that it returns a time we can predict
                tbl.get_current_time = lambda: update_time

            for source_row in self._gen_rows_from_csv('test1_upsert.csv', transform=False):
                self._transform_csv_row(source_row)
                if begin_date_source == BeginDateSource.IN_ROW:
                    source_row['begin_date'] = update_time

                if begin_date_source in {BeginDateSource.IN_ROW, BeginDateSource.SYSTEM_TIME}:
                    tbl.upsert(source_row)
                else:
                    tbl.upsert(source_row, effective_date=update_time)

            if check_for_deletes:
                # Note: For deletes IN_ROW is not really a valid source for the effective date
                #       We'll pass the parameter instead
                if begin_date_source in {BeginDateSource.SYSTEM_TIME}:
                    tbl.delete_not_processed()
                else:  # Parameter
                    tbl.delete_not_processed(effective_date=update_time)

            tbl.commit()

            # Validate data
            if check_for_deletes:
                upsert_expected_file = 'test1_upsert_expected_with_deletes.csv'
            else:
                upsert_expected_file = 'test1_upsert_expected_no_deletes.csv'
            self._check_table_rows(
                expected_row_generator=self._gen_rows_from_csv(upsert_expected_file),
                target_table=tbl,
                special_check_values=dict(
                    begin_date={
                        'default_begin_dt': tbl.default_begin_date,
                        'upsert_dt': update_time,
                    },
                    end_date={
                        'upsert_dt-1sec': update_time - timedelta(seconds=1),
                        'default_end_dt': tbl.default_end_date,
                    },
                ),
                msg=f"{tbl_name} upsert_expected_rows check",
            )

        self.mock_database.drop_table_if_exists(tbl_name)

    ###############################################################
    # InsertAndUpsert Test block
    #
    # Note: We could loop over all these test parameters.
    # However, using methods for each allows for parallel testing.

    def test_insert_and_update_t2_t1_del_systime(self):
        tbl_name_base = self._get_table_name("test_insert_and_update_t2_t1_del_systime")
        for load_cache in [True, False]:
            tbl_part2 = '_Cache' if load_cache else '_NoChc'
            tbl_name = tbl_name_base + tbl_part2
            self._testInsertAndUpsert(
                load_cache=load_cache,
                use_type2=True,
                use_type1=True,
                check_for_deletes=True,
                tbl_name=tbl_name,
                begin_date_source=BeginDateSource.SYSTEM_TIME,
            )

    def test_insert_and_update_t2_t1_del_timeinrow(self):
        tbl_name_base = self._get_table_name("test_insert_and_update_t2_t1_del_timeinrow")
        for load_cache in [True, False]:
            tbl_part2 = '_Cache' if load_cache else '_NoChc'
            tbl_name = tbl_name_base + tbl_part2
            self._testInsertAndUpsert(
                load_cache=load_cache,
                use_type2=True,
                use_type1=True,
                check_for_deletes=True,
                tbl_name=tbl_name,
                begin_date_source=BeginDateSource.IN_ROW,
            )

    def test_insert_and_update_t2_t1_del_param(self):
        tbl_name_base = self._get_table_name("test_insert_and_update_t2_t1_del_param")
        for load_cache in [True, False]:
            tbl_part2 = '_Cache' if load_cache else '_NoChc'
            tbl_name = tbl_name_base + tbl_part2
            self._testInsertAndUpsert(
                load_cache=load_cache,
                use_type2=True,
                use_type1=True,
                check_for_deletes=True,
                tbl_name=tbl_name,
                begin_date_source=BeginDateSource.PARAMETER,
            )

    def test_insert_and_update_t2_not1_del(self):
        tbl_name_base = self._get_table_name("test_insert_and_update_t2_not1_del")
        for load_cache in [True, False]:
            tbl_part2 = '_Cache' if load_cache else '_NoChc'
            tbl_name = tbl_name_base + tbl_part2
            self._testInsertAndUpsert(
                load_cache=load_cache,
                use_type2=True,
                use_type1=False,
                check_for_deletes=True,
                tbl_name=tbl_name,
            )

    def test_insert_and_update_nosrgt_del(self):
        tbl_name_base = self._get_table_name("test_insert_and_update_nosrgt_del")
        for load_cache in [True, False]:
            tbl_part2 = '_Cache' if load_cache else '_NoChc'
            tbl_name = tbl_name_base + tbl_part2
            self._testInsertAndUpsert(
                load_cache=load_cache,
                use_type2=False,
                use_type1=False,
                check_for_deletes=True,
                tbl_name=tbl_name,
            )

    def test_insert_and_update_odd_duck(self):
        tbl_name_base = self._get_table_name("test_insert_and_update_odd_duck")
        for load_cache in [True, False]:
            tbl_part2 = '_Cache' if load_cache else '_NoChc'
            tbl_name = tbl_name_base + tbl_part2
            self._testInsertAndUpsert(
                load_cache=load_cache,
                use_type2=False,
                use_type1=True,
                check_for_deletes=True,
                tbl_name=tbl_name,
            )

    def test_insert_and_update_t2_t1_nodel(self):
        tbl_name_base = self._get_table_name("test_insert_and_update_t2_t1_nodel")
        for load_cache in [True, False]:
            tbl_part2 = '_Cache' if load_cache else '_NoChc'
            tbl_name = tbl_name_base + tbl_part2
            self._testInsertAndUpsert(
                load_cache=load_cache,
                use_type2=True,
                use_type1=True,
                check_for_deletes=False,
                tbl_name=tbl_name,
            )

    def test_insert_and_update_t2_not1_nodel(self):
        tbl_name_base = self._get_table_name("test_insert_and_update_t2_not1_nodel")
        for load_cache in [True, False]:
            tbl_part2 = '_Cache' if load_cache else '_NoChc'
            tbl_name = tbl_name_base + tbl_part2
            self._testInsertAndUpsert(
                load_cache=load_cache,
                use_type2=True,
                use_type1=False,
                check_for_deletes=False,
                tbl_name=tbl_name,
            )

    def test_insert_and_update_nosrgt_nodel(self):
        tbl_name_base = self._get_table_name("test_insert_and_update_nosrgt_nodel")
        for load_cache in [True, False]:
            tbl_part2 = '_Cache' if load_cache else '_NoChc'
            tbl_name = tbl_name_base + tbl_part2
            self._testInsertAndUpsert(
                load_cache=load_cache,
                use_type2=False,
                use_type1=False,
                check_for_deletes=False,
                tbl_name=tbl_name,
            )

    # End InsertAndUpsert Test block
    ###############################################################

    def test_upsert_override_autogen_pk(self):
        tbl_name = self._get_table_name('test_hst_upsert_override_autogen_pk')
        self._create_table_1(tbl_name)

        rows_to_insert = 10
        with self.TEST_COMPONENT(
            self.task,
            self.mock_database,
            table_name=tbl_name,
            auto_generate_key=True,
            primary_key=['id'],
            natural_key=['text_col'],
            begin_date_column='begin_date',
            end_date_column='end_date',
            delete_flag='delete_flag',
        ) as tbl:
            for row in self._gen_src_rows_1(rows_to_insert):
                tbl.upsert(row)
            tbl.commit()

        self.mock_database.drop_table_if_exists(tbl_name)

    def _testInsertAndSQLUpsert(
            self,
            tbl_name: str,
            use_type1: bool,
            use_type2: bool,
            check_for_deletes: bool,
    ):
        self._create_table_2(
            tbl_name,
            use_type1,
            use_type2,
        )

        with self.TEST_COMPONENT(
                self.task,
                self.mock_database,
                table_name=tbl_name) as tbl:
            tbl.begin_date_column = 'begin_date'
            tbl.end_date_column = 'end_date'
            tbl.delete_flag = 'delete_flag'
            if check_for_deletes:
                tbl.track_source_rows = True

            if use_type2:
                tbl.primary_key = ['type_2_srgt']
                tbl.auto_generate_key = True
                tbl.natural_key = ['text_col']
            else:
                tbl.primary_key = ['text_col']

            if use_type1:
                tbl.type_1_surrogate = 'type_1_srgt'

            with CSVReader(
                    self.task,
                    os.path.join(self.get_package_path(), self.TEST_DATA_PATH, 'test1_insert.csv'),
            ) as insert_file:
                for source_row in insert_file:
                    self._transform_csv_row(source_row)
                    tbl.insert_row(source_row)
            tbl.commit()

            # Insert new data to a temp table
            # Get the column names
            source_columns_set = None
            for source_row in self._gen_rows_from_csv('test1_upsert.csv', transform=False):
                source_columns_set = source_row.column_set
                break
            src_table_name = f"src_{tbl_name}"
            self.mock_database.drop_table_if_exists(src_table_name)
            src_columns = [col for col in
                           self._get_column_list_table_2(
                                use_type1=False,
                                use_type2=False,
                            )
                           if col.name in source_columns_set
                           ]
            src_columns.append(Column('begin_date', DateTime))
            sa_table = sqlalchemy.schema.Table(
                src_table_name,
                self.mock_database,
                *src_columns
            )
            sa_table.create()

            with Table(
                self.task,
                self.mock_database,
                table_name=src_table_name,
            ) as src_tbl:
                src_excludes = None

                update_time = datetime(2001, 5, 23, 7, 59, 21)

                for source_row in self._gen_rows_from_csv('test1_upsert.csv', transform=False):
                    self._transform_csv_row(source_row)
                    source_row['begin_date'] = update_time
                    if src_excludes is None:
                        src_excludes = set(src_tbl.columns) - source_row.column_set
                    src_tbl.insert_row(source_row)
                src_tbl.commit()

                # Mock get_current_time so that it returns a time we can predict
                tbl.get_current_time = lambda: update_time

                tbl.sql_upsert(
                    source_table=src_tbl,
                    source_effective_date_column='begin_date',
                    source_excludes=src_excludes,
                    check_for_deletes=check_for_deletes,
                    commit_each_table=True,
                )

                tbl.commit()

            # Validate data
            if check_for_deletes:
                upsert_expected_file = 'test1_upsert_expected_with_deletes.csv'
            else:
                upsert_expected_file = 'test1_upsert_expected_no_deletes.csv'
            self._check_table_rows(
                expected_row_generator=self._gen_rows_from_csv(upsert_expected_file),
                target_table=tbl,
                special_check_values=dict(
                    begin_date={
                        'default_begin_dt': tbl.default_begin_date,
                        'upsert_dt': update_time,
                    },
                    end_date={

                        'upsert_dt-1sec': update_time - timedelta(seconds=1),
                        'default_end_dt': tbl.default_end_date,
                    },
                ),
                msg=f"{tbl_name} upsert_expected_rows check",
            )
        self.mock_database.drop_table_if_exists(tbl_name)

    ###############################################################
    # SQL Upsert Test block
    #
    # Note: We could loop over all these test parameters.
    # However, using methods for each allows for parallel testing.

    def test_sql_upsert_t2_t1_del(self):
        self._testInsertAndSQLUpsert(
            use_type2=True,
            use_type1=True,
            check_for_deletes=True,
            tbl_name=self._get_table_name("test_sql_upsert_t2_t1_del"),
        )

    def test_sql_upsert_t2_not1_del(self):
        self._testInsertAndSQLUpsert(
            use_type2=True,
            use_type1=False,
            check_for_deletes=True,
            tbl_name=self._get_table_name("test_sql_upsert_t2_not1_del"),
        )

    def test_sql_upsert_nosrgt_del(self):
        self._testInsertAndSQLUpsert(
            use_type2=False,
            use_type1=False,
            check_for_deletes=True,
            tbl_name=self._get_table_name("test_sql_upsert_nosrgt_del"),
        )

    def test_sql_upsert_t2_t1_nodel(self):
        self._testInsertAndSQLUpsert(
            use_type2=True,
            use_type1=True,
            check_for_deletes=False,
            tbl_name=self._get_table_name("test_sql_upsert_t2_t1_nodel"),
        )

    def test_sql_upsert_t2_not1_nodel(self):
        self._testInsertAndSQLUpsert(
            use_type2=True,
            use_type1=False,
            check_for_deletes=False,
            tbl_name=self._get_table_name("test_sql_upsert_t2_not1_nodel"),
        )

    def test_sql_upsert_nosrgt_nodel(self):
        self._testInsertAndSQLUpsert(
            use_type2=False,
            use_type1=False,
            check_for_deletes=False,
            tbl_name=self._get_table_name("test_sql_upsert_nosrgt_nodel"),
        )

    # End SQL Upsert Test block
    ###############################################################


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
