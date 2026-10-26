import unittest
from datetime import datetime, date, timedelta
from types import SimpleNamespace
from unittest import mock

import sqlalchemy
from sqlalchemy import Column, Integer, DateTime

from bi_etl.components.hst_table import HistoryTable
from bi_etl.components.row.column_difference import ColumnDifference
from bi_etl.components.row.row_status import RowStatus
from bi_etl.components.table import Table
from bi_etl.exceptions import BeforeAllExisting, NoResultFound
from tests.db_base_tests.base_test_hst_table import BaseTestHstTable
from tests.db_sqlite.sqlite_db import SqliteDB

T1 = datetime(2020, 1, 1)
T2 = datetime(2021, 1, 1)
T3 = datetime(2022, 1, 1)
D1900 = datetime(1900, 1, 1)
D9999 = datetime(9999, 1, 1)
ONE_SECOND = timedelta(seconds=1)


class TestHstTableSqlite(BaseTestHstTable):
    SUPPORTS_DECIMAL = False

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.db_container = SqliteDB()

    def test_sql_upsert_nosrgt_del(self):
        super().test_sql_upsert_nosrgt_del()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _create_sa_table(self, name: str, kind: str = 'srgt') -> sqlalchemy.schema.Table:
        """
        Create a history table with the columns used by the tests below.

        Parameters
        ----------
        name:
            Table name.
        kind:
            ``'srgt'`` for a surrogate key primary key, ``'composite'`` for a (nk, begin_date)
            primary key or ``'none'`` for a table without a primary key.
        """
        self.mock_database.drop_table_if_exists(name)
        sa_table = sqlalchemy.schema.Table(
            name,
            self.mock_database,
            Column('srgt', Integer, primary_key=(kind == 'srgt')),
            Column('nk', Integer, primary_key=(kind == 'composite')),
            Column('col1', self._TEXT()),
            Column('col2', self._TEXT()),
            Column('col3', self._TEXT()),
            Column('begin_date', DateTime, primary_key=(kind == 'composite')),
            Column('end_date', DateTime),
            Column('delete_flag', self._TEXT()),
            Column('last_upd', DateTime),
            Column('t1_srgt', Integer),
        )
        sa_table.create(bind=self.mock_database.bind)
        self.print_ddl(sa_table)
        return sa_table

    def _hst(self, name: str, kind: str = 'srgt', **kwargs) -> HistoryTable:
        """
        Create the database table and a :class:`HistoryTable` on it.

        Parameters
        ----------
        name:
            Base table name.
        kind:
            See :meth:`_create_sa_table`.
        kwargs:
            Overrides of the default :class:`HistoryTable` arguments.
        """
        table_name = self._get_table_name(name)
        self._create_sa_table(table_name, kind)
        options = dict(
            primary_key=['nk', 'begin_date'] if kind == 'composite' else ['srgt'],
            natural_key=['nk'],
            auto_generate_key=(kind == 'srgt'),
            begin_date_column='begin_date',
            end_date_column='end_date',
            delete_flag='delete_flag',
        )
        options.update(kwargs)
        # The key setters cannot take None, so None means "do not pass the option"
        for key_option in ('primary_key', 'natural_key'):
            if options[key_option] is None:
                del options[key_option]
        tbl = HistoryTable(self.task, self.mock_database, table_name=table_name, **options)
        self.addCleanup(self.mock_database.drop_table_if_exists, table_name)
        self.addCleanup(tbl.close)
        return tbl

    @staticmethod
    def _row(tbl: HistoryTable, **values):
        return tbl.Row(data=values)

    def _raw_insert(self, tbl: HistoryTable, srgt, nk, begin, end, col1='a', flag='N'):
        """Insert a version without any of the history table checks."""
        row = self._row(
            tbl,
            srgt=srgt, nk=nk, col1=col1, begin_date=begin, end_date=end, delete_flag=flag,
        )
        Table.insert_row(tbl, row)

    def _rows(self, tbl: HistoryTable):
        tbl.commit()
        return list(tbl.order_by(['nk', 'begin_date']))

    def _versions(self, tbl: HistoryTable, nk=None):
        """List of (begin, end, col1, delete_flag) tuples for the key, or all rows if ``nk`` is None."""
        return [
            (r['begin_date'], r['end_date'], r['col1'], r['delete_flag'])
            for r in self._rows(tbl)
            if nk is None or r['nk'] == nk
        ]

    # ------------------------------------------------------------------
    # Properties and simple configuration
    # ------------------------------------------------------------------

    def test_time_precision_sets_end_date_timedelta(self):
        tbl = self._hst('prec')
        expected = {
            HistoryTable.TimePrecision.microsecond: timedelta(microseconds=-1),
            HistoryTable.TimePrecision.millisecond: timedelta(milliseconds=-1),
            HistoryTable.TimePrecision.second: timedelta(seconds=-1),
            HistoryTable.TimePrecision.minute: timedelta(minutes=-1),
            HistoryTable.TimePrecision.hour: timedelta(hours=-1),
            HistoryTable.TimePrecision.day: timedelta(days=-1),
        }
        for precision, delta in expected.items():
            tbl.begin_end_precision = precision
            self.assertEqual(precision, tbl.begin_end_precision)
            self.assertEqual(delta, tbl._end_date_timedelta)

    def test_time_precision_default_is_second(self):
        tbl = self._hst('prec_default')
        self.assertEqual(HistoryTable.TimePrecision.second, tbl.begin_end_precision)

    def test_time_precision_rejects_non_enum(self):
        tbl = self._hst('prec_bad')
        with self.assertRaises(ValueError):
            tbl.begin_end_precision = 's'

    def test_default_dates(self):
        tbl = self._hst('defaults')
        self.assertEqual(D1900, tbl.default_begin_date)
        self.assertEqual(D9999, tbl.default_end_date)
        self.assertTrue(tbl.inserts_use_default_begin_date)
        self.assertIsNone(tbl.type_1_surrogate)

    def test_default_dates_are_coerced_to_datetime(self):
        tbl = self._hst('defaults_coerce')
        tbl.default_begin_date = date(2000, 1, 1)
        tbl.default_end_date = date(2999, 12, 31)
        tbl.default_effective_date = date(2010, 6, 1)
        self.assertEqual(datetime(2000, 1, 1), tbl.default_begin_date)
        self.assertEqual(datetime(2999, 12, 31), tbl.default_end_date)
        self.assertEqual(datetime(2010, 6, 1), tbl.default_effective_date)

    def test_default_effective_date_constructor_argument(self):
        tbl = self._hst('eff_arg', default_effective_date=date(2015, 3, 4))
        self.assertEqual(datetime(2015, 3, 4), tbl.default_effective_date)

    def test_default_effective_date_falls_back_to_current_time_once(self):
        tbl = self._hst('eff_fallback')
        tbl.get_current_time = lambda: T1
        self.assertEqual(T1, tbl.default_effective_date)
        tbl.get_current_time = lambda: T2
        self.assertEqual(T1, tbl.default_effective_date)

    def test_repr(self):
        tbl = self._hst('repr_test')
        self.assertEqual(f"HistoryTable({tbl.table_name})", repr(tbl))

    def test_kwattrs_order_puts_date_columns_first(self):
        order = HistoryTable.kwattrs_order()
        self.assertEqual({'begin_date_column': 1, 'end_date_column': 1}, order)

    def test_is_date_key_column(self):
        tbl = self._hst('is_date')
        self.assertTrue(tbl.is_date_key_column('begin_date'))
        self.assertTrue(tbl.is_date_key_column('end_date'))
        self.assertFalse(tbl.is_date_key_column('nk'))

    def test_is_date_key_column_requires_date_columns(self):
        table_name = self._get_table_name('is_date_missing')
        self._create_sa_table(table_name)
        self.addCleanup(self.mock_database.drop_table_if_exists, table_name)
        tbl = HistoryTable(self.task, self.mock_database, table_name=table_name)
        self.addCleanup(tbl.close)
        with self.assertRaises(AssertionError):
            tbl.is_date_key_column('nk')
        tbl.begin_date_column = 'begin_date'
        with self.assertRaises(AssertionError):
            tbl.is_date_key_column('nk')

    def test_natural_key_setter_stores_column_names(self):
        tbl = self._hst('nk_setter', natural_key=None)
        tbl.natural_key = ['nk']
        self.assertEqual(['nk'], tbl.natural_key)

    def test_natural_key_setter_replaces_constructor_value(self):
        tbl = self._hst('nk_setter_replace', natural_key=['nk'])
        tbl.natural_key = ['col1', 'col2']
        self.assertEqual(['col1', 'col2'], tbl.natural_key)

    def test_natural_key_setter_defines_nk_lookup(self):
        tbl = self._hst('nk_setter_lookup', natural_key=None)
        tbl.natural_key = ['nk']
        self.assertEqual(['nk'], list(tbl.get_lookup(tbl.get_nk_lookup_name()).lookup_keys))

    def test_natural_key_setter_rejects_unknown_column(self):
        tbl = self._hst('nk_setter_unknown', natural_key=None)
        with self.assertRaises(KeyError):
            tbl.natural_key = ['not_a_column']

    def test_natural_key_not_set_falls_back_to_primary_key(self):
        tbl = self._hst('nk_fallback', kind='composite', natural_key=None)
        self.assertEqual(['nk', 'begin_date'], list(tbl.natural_key))

    def test_natural_key_not_set_with_auto_generate_key_raises(self):
        tbl = self._hst('nk_not_set', natural_key=None)
        with self.assertRaisesRegex(ValueError, 'natural key not set'):
            _ = tbl.natural_key

    def test_build_nk_with_single_primary_key_logs_error_and_returns_none(self):
        tbl = self._hst('nk_single')
        with self.assertLogs(tbl.log, level='ERROR') as logs:
            self.assertIsNone(tbl.infer_natural_key())
        self.assertIn('Cannot determine natural key', '\n'.join(logs.output))

    def test_build_nk_excludes_date_columns_of_composite_key(self):
        tbl = self._hst('nk_composite', kind='composite')
        self.assertEqual(['nk'], tbl.infer_natural_key())

    def test_date_column_setters_maintain_custom_special_values(self):
        tbl = self._hst('special_values_setters')
        self.assertEqual(D1900, tbl.custom_special_values['begin_date'])
        self.assertEqual(D9999, tbl.custom_special_values['end_date'])

        tbl.begin_date_column = 'col1'
        tbl.end_date_column = 'col2'
        self.assertNotIn('begin_date', tbl.custom_special_values)
        self.assertNotIn('end_date', tbl.custom_special_values)
        self.assertEqual(D1900, tbl.custom_special_values['col1'])
        self.assertEqual(D9999, tbl.custom_special_values['col2'])

        tbl.begin_date_column = None
        tbl.end_date_column = None
        self.assertNotIn('col1', tbl.custom_special_values)
        self.assertNotIn('col2', tbl.custom_special_values)

    def test_define_lookup_requires_a_non_date_column(self):
        tbl = self._hst('lookup_dates_only')
        with self.assertRaises(AssertionError):
            tbl.define_lookup('only_dates', ['begin_date', 'end_date'])

    def test_define_lookup_removes_date_columns_from_keys(self):
        tbl = self._hst('lookup_strip_dates')
        tbl.define_lookup('col_lookup', ['col1', 'begin_date', 'end_date'])
        self.assertEqual(['col1'], list(tbl.get_lookup('col_lookup').lookup_keys))

    # ------------------------------------------------------------------
    # insert_row / build_row
    # ------------------------------------------------------------------

    def test_insert_row_requires_begin_date_column(self):
        table_name = self._get_table_name('insert_no_begin')
        self._create_sa_table(table_name)
        self.addCleanup(self.mock_database.drop_table_if_exists, table_name)
        tbl = HistoryTable(self.task, self.mock_database, table_name=table_name, end_date_column='end_date')
        self.addCleanup(tbl.close)
        with self.assertRaisesRegex(ValueError, 'begin_date column name not set'):
            tbl.insert_row(self._row(tbl, srgt=1, nk=1))

    def test_insert_row_requires_end_date_column(self):
        table_name = self._get_table_name('insert_no_end')
        self._create_sa_table(table_name)
        self.addCleanup(self.mock_database.drop_table_if_exists, table_name)
        tbl = HistoryTable(self.task, self.mock_database, table_name=table_name, begin_date_column='begin_date')
        self.addCleanup(tbl.close)
        with self.assertRaisesRegex(ValueError, 'end_date column name not set'):
            tbl.insert_row(self._row(tbl, srgt=1, nk=1))

    def test_insert_row_rejects_begin_after_end(self):
        tbl = self._hst('insert_bad_dates')
        with self.assertRaisesRegex(ValueError, 'greater than end date'):
            tbl.insert_row(self._row(tbl, nk=1, begin_date=T2, end_date=T1))

    def test_insert_row_defaults_dates_and_delete_flag(self):
        tbl = self._hst('insert_defaults')
        tbl.insert_row(self._row(tbl, nk=1, col1='a'))
        self.assertEqual([(D1900, D9999, 'a', 'N')], self._versions(tbl))

    def test_insert_row_keeps_supplied_dates(self):
        tbl = self._hst('insert_dates')
        tbl.insert_row(self._row(tbl, nk=1, col1='a', begin_date=T1, end_date=T2, delete_flag='Y'))
        self.assertEqual([(T1, T2, 'a', 'Y')], self._versions(tbl))

    def test_insert_row_generates_type_1_surrogate_at_default_begin_date(self):
        tbl = self._hst('insert_type1', type_1_surrogate='t1_srgt')
        tbl.insert_row(self._row(tbl, nk=1, col1='a'))
        rows = self._rows(tbl)
        self.assertEqual(1, len(rows))
        self.assertIsNotNone(rows[0]['t1_srgt'])

    def test_insert_row_warns_instead_of_generating_type_1_surrogate_for_later_begin_date(self):
        tbl = self._hst('insert_type1_warn', type_1_surrogate='t1_srgt')
        with self.assertWarnsRegex(UserWarning, 'type1 surrogate'):
            tbl.insert_row(self._row(tbl, nk=1, col1='a', begin_date=T1))
        rows = self._rows(tbl)
        self.assertEqual(1, len(rows))
        self.assertIsNone(rows[0]['t1_srgt'])

    def test_build_row_defaults_delete_flag(self):
        tbl = self._hst('build_row')
        built = tbl.build_row(self._row(tbl, nk=1, col1='a'))
        self.assertEqual('N', built['delete_flag'])
        built = tbl.build_row(self._row(tbl, nk=1, col1='a', delete_flag='Y'))
        self.assertEqual('Y', built['delete_flag'])

    def test_delete_is_not_implemented(self):
        tbl = self._hst('delete_ni')
        with self.assertRaises(NotImplementedError):
            tbl.delete(key_values=[1])

    # ------------------------------------------------------------------
    # upsert / apply_updates
    # ------------------------------------------------------------------

    def test_upsert_new_key_uses_default_dates(self):
        tbl = self._hst('upsert_new')
        inserted = []
        result = tbl.upsert(
            self._row(tbl, nk=1, col1='a'),
            effective_date=T1,
            insert_callback=inserted.append,
        )
        self.assertEqual([(D1900, D9999, 'a', 'N')], self._versions(tbl))
        self.assertEqual(1, len(inserted))
        self.assertEqual(1, result['nk'])

    def test_upsert_new_key_without_default_begin_date_uses_effective_date(self):
        tbl = self._hst('upsert_new_eff', inserts_use_default_begin_date=False)
        tbl.upsert(self._row(tbl, nk=1, col1='a'), effective_date=T1)
        self.assertEqual([(T1, D9999, 'a', 'N')], self._versions(tbl))

    def test_upsert_effective_date_from_begin_date_in_source_row(self):
        tbl = self._hst('upsert_row_eff', inserts_use_default_begin_date=False)
        tbl.upsert(self._row(tbl, nk=1, col1='a', begin_date=T1))
        tbl.upsert(self._row(tbl, nk=1, col1='b', begin_date=T2))
        self.assertEqual(
            [(T1, T2 - ONE_SECOND, 'a', 'N'), (T2, D9999, 'b', 'N')],
            self._versions(tbl),
        )

    def test_upsert_effective_date_defaults_to_default_effective_date(self):
        tbl = self._hst('upsert_default_eff', inserts_use_default_begin_date=False)
        tbl.default_effective_date = T1
        tbl.upsert(self._row(tbl, nk=1, col1='a'))
        tbl.default_effective_date = T2
        tbl.upsert(self._row(tbl, nk=1, col1='b'))
        self.assertEqual(
            [(T1, T2 - ONE_SECOND, 'a', 'N'), (T2, D9999, 'b', 'N')],
            self._versions(tbl),
        )

    def test_upsert_change_creates_new_version_and_calls_update_callback(self):
        tbl = self._hst('upsert_change')
        tbl.upsert(self._row(tbl, nk=1, col1='a', col2='x'), effective_date=T1)
        calls = []
        tbl.upsert(
            self._row(tbl, nk=1, col1='b', col2='x'),
            effective_date=T2,
            update_callback=lambda changes, row: calls.append([c.column_name for c in changes]),
        )
        self.assertEqual(
            [(D1900, T2 - ONE_SECOND, 'a', 'N'), (T2, D9999, 'b', 'N')],
            self._versions(tbl),
        )
        self.assertEqual([['col1']], calls)
        # Each version gets its own surrogate key
        self.assertEqual(2, len({r['srgt'] for r in self._rows(tbl)}))

    def test_upsert_without_change_does_not_create_version(self):
        tbl = self._hst('upsert_nochange')
        tbl.upsert(self._row(tbl, nk=1, col1='a'), effective_date=T1)
        calls = []
        tbl.upsert(
            self._row(tbl, nk=1, col1='a'),
            effective_date=T2,
            update_callback=lambda changes, row: calls.append(changes),
        )
        self.assertEqual([(D1900, D9999, 'a', 'N')], self._versions(tbl))
        self.assertEqual([], calls)

    def test_upsert_do_not_update_column_is_ignored(self):
        tbl = self._hst('upsert_do_not_update')
        tbl.upsert(self._row(tbl, nk=1, col1='a', col2='x'), effective_date=T1)
        tbl.upsert(self._row(tbl, nk=1, col1='a', col2='y'), effective_date=T2, do_not_update=['col2'])
        self.assertEqual(1, len(self._rows(tbl)))

    def test_upsert_skip_update_check_on_accepts_list(self):
        tbl = self._hst('upsert_skip_list')
        tbl.upsert(self._row(tbl, nk=1, col1='a', col2='x'), effective_date=T1)
        tbl.upsert(
            self._row(tbl, nk=1, col1='a', col2='y'),
            effective_date=T2,
            skip_update_check_on=['col2', 'end_date'],
        )
        self.assertEqual(1, len(self._rows(tbl)))

    def test_upsert_same_effective_date_as_begin_date_updates_in_place(self):
        tbl = self._hst('upsert_in_place', inserts_use_default_begin_date=False)
        tbl.upsert(self._row(tbl, nk=1, col1='a'), effective_date=T1)
        tbl.upsert(self._row(tbl, nk=1, col1='b'), effective_date=T1)
        self.assertEqual([(T1, D9999, 'b', 'N')], self._versions(tbl))

    def test_upsert_before_all_existing_inserts_earlier_version(self):
        tbl = self._hst(
            'upsert_before_all',
            inserts_use_default_begin_date=False,
            type_1_surrogate='t1_srgt',
            last_update_date='last_upd',
        )
        tbl.upsert(self._row(tbl, nk=1, col1='b'), effective_date=T2)
        tbl.commit()
        inserted = []
        tbl.upsert(
            self._row(tbl, nk=1, col1='a'),
            effective_date=T1,
            insert_callback=inserted.append,
            additional_insert_values={'col2': 'extra'},
        )
        rows = self._rows(tbl)
        self.assertEqual(
            [(T1, T2 - ONE_SECOND, 'a', 'N'), (T2, D9999, 'b', 'N')],
            self._versions(tbl),
        )
        self.assertEqual(1, len(inserted))
        self.assertEqual('extra', rows[0]['col2'])
        self.assertIsNone(rows[1]['col2'])
        # Type 1 surrogate is shared by all versions, type 2 surrogates are not
        self.assertIsNotNone(rows[0]['t1_srgt'])
        self.assertEqual(rows[1]['t1_srgt'], rows[0]['t1_srgt'])
        self.assertNotEqual(rows[1]['srgt'], rows[0]['srgt'])
        self.assertIsNotNone(rows[0]['last_upd'])

    def test_upsert_before_all_existing_with_default_begin_date(self):
        tbl = self._hst('upsert_before_all_default')
        tbl.upsert(self._row(tbl, nk=1, col1='b'), effective_date=T2)
        # Version that starts after the default begin date, e.g. from a load that used inserts_use_default_begin_date
        tbl.commit()
        tbl.default_begin_date = datetime(1800, 1, 1)
        tbl.upsert(self._row(tbl, nk=1, col1='a'), effective_date=datetime(1850, 1, 1))
        versions = self._versions(tbl)
        self.assertEqual((datetime(1800, 1, 1), D1900 - ONE_SECOND, 'a', 'N'), versions[0])
        self.assertEqual((D1900, D9999, 'b', 'N'), versions[1])

    def test_upsert_new_key_sets_type_1_surrogate_and_last_update_date(self):
        tbl = self._hst('upsert_new_t1', type_1_surrogate='t1_srgt', last_update_date='last_upd')
        tbl.upsert(self._row(tbl, nk=1, col1='a'), effective_date=T1)
        tbl.upsert(self._row(tbl, nk=2, col1='b'), effective_date=T1)
        tbl.upsert(self._row(tbl, nk=1, col1='c'), effective_date=T2)
        rows = self._rows(tbl)
        self.assertEqual(3, len(rows))
        for row in rows:
            self.assertIsNotNone(row['t1_srgt'])
            self.assertIsNotNone(row['last_upd'])
        nk1_rows = [r for r in rows if r['nk'] == 1]
        nk2_rows = [r for r in rows if r['nk'] == 2]
        self.assertEqual(nk1_rows[0]['t1_srgt'], nk1_rows[1]['t1_srgt'])
        self.assertNotEqual(nk1_rows[0]['t1_srgt'], nk2_rows[0]['t1_srgt'])

    def test_upsert_with_filled_cache(self):
        tbl = self._hst('upsert_cache')
        tbl.upsert(self._row(tbl, nk=1, col1='a'), effective_date=T1)
        tbl.commit()
        tbl.fill_cache()
        tbl.upsert(self._row(tbl, nk=1, col1='b'), effective_date=T2)
        tbl.upsert(self._row(tbl, nk=2, col1='c'), effective_date=T2)
        self.assertEqual(
            [
                (D1900, T2 - ONE_SECOND, 'a', 'N'),
                (T2, D9999, 'b', 'N'),
                (D1900, D9999, 'c', 'N'),
            ],
            self._versions(tbl),
        )

    def test_upsert_trace_data_logs_actions(self):
        tbl = self._hst('upsert_trace')
        tbl.trace_data = True
        with self.assertLogs(tbl.log, level='DEBUG') as logs:
            tbl.upsert(self._row(tbl, nk=1, col1='a', col2='x'), effective_date=T1)
            tbl.upsert(
                self._row(tbl, nk=1, col1='b', col2='y'),
                effective_date=T2,
                skip_update_check_on=frozenset({'col2'}),
            )
        output = '\n'.join(logs.output)
        self.assertIn('not found, inserting as new', output)
        self.assertIn('col1 changed from a to b', output)
        self.assertIn('NO UPDATE TRIGGERED BY col2 changed from x to y', output)
        self.assertIn('retiring row with begin effective', output)

    def test_upsert_trace_data_logs_in_place_update(self):
        tbl = self._hst('upsert_trace_in_place', inserts_use_default_begin_date=False)
        tbl.trace_data = True
        with self.assertLogs(tbl.log, level='DEBUG') as logs:
            tbl.upsert(self._row(tbl, nk=1, col1='a'), effective_date=T1)
            tbl.upsert(self._row(tbl, nk=1, col1='b'), effective_date=T1)
        self.assertIn('Begin date exact match', '\n'.join(logs.output))

    def test_upsert_trace_data_logs_insert_before_existing(self):
        tbl = self._hst('upsert_trace_before', inserts_use_default_begin_date=False)
        tbl.trace_data = True
        tbl.upsert(self._row(tbl, nk=1, col1='b'), effective_date=T2)
        tbl.commit()
        with self.assertLogs(tbl.log, level='DEBUG') as logs:
            tbl.upsert(self._row(tbl, nk=1, col1='a'), effective_date=T1)
        self.assertIn('before existing history', '\n'.join(logs.output))

    def test_upsert_without_track_update_columns(self):
        tbl = self._hst('upsert_no_track')
        tbl.track_update_columns = False
        tbl.upsert(self._row(tbl, nk=1, col1='a'), effective_date=T1)
        tbl.upsert(self._row(tbl, nk=1, col1='b'), effective_date=T2)
        self.assertEqual(2, len(self._rows(tbl)))

    def test_upsert_tracks_source_rows(self):
        tbl = self._hst('upsert_track_source')
        tbl.track_source_rows = True
        tbl.upsert(self._row(tbl, nk=1, col1='a'), effective_date=T1)
        tbl.upsert(self._row(tbl, nk=2, col1='a'), effective_date=T1)
        self.assertEqual({(1,), (2,)}, set(tbl.source_keys_processed))

    def test_apply_updates_rejects_begin_after_end(self):
        tbl = self._hst('apply_bad_dates')
        row = self._row(tbl, srgt=1, nk=1, col1='a', begin_date=T2, end_date=T1)
        with self.assertRaisesRegex(ValueError, 'greater than end date'):
            tbl.apply_updates(row, changes_list=[ColumnDifference('col1', 'a', 'b')], effective_date=T3)

    def test_apply_updates_warns_when_existing_versions_do_not_reach_effective_date(self):
        tbl = self._hst('apply_gap', auto_generate_key=False)
        self._raw_insert(tbl, srgt=1, nk=1, begin=T1, end=T2)
        tbl.commit()
        tbl.fill_cache()
        existing = tbl.get_by_lookup_and_effective_date(
            tbl.get_nk_lookup_name(),
            self._row(tbl, nk=1),
            T1,
        )
        self.assertEqual(T2, existing['end_date'])
        with self.assertLogs(tbl.log, level='WARNING') as logs:
            tbl.apply_updates(
                existing,
                changes_list=[ColumnDifference('col1', 'a', 'b')],
                additional_update_values={'srgt': 2},
                effective_date=T3,
            )
        self.assertIn('did not cover all dates', '\n'.join(logs.output))
        self.assertEqual(
            [(T1, T3 - ONE_SECOND, 'a', 'N'), (T3, D9999, 'b', 'N')],
            self._versions(tbl),
        )

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    def test_fill_cache_ordered_by_primary_key_and_begin_date(self):
        tbl = self._hst('fill_cache_pk')
        tbl.upsert(self._row(tbl, nk=1, col1='a'), effective_date=T1)
        tbl.upsert(self._row(tbl, nk=1, col1='b'), effective_date=T2)
        tbl.commit()
        tbl.fill_cache(order_by='-PK-')
        self.assertTrue(tbl.cache_filled)
        found = tbl.get_by_lookup_and_effective_date(
            tbl.get_nk_lookup_name(),
            self._row(tbl, nk=1),
            T3,
        )
        self.assertEqual('b', found['col1'])
        found = tbl.get_by_lookup_and_effective_date(
            tbl.get_nk_lookup_name(),
            self._row(tbl, nk=1),
            T1,
        )
        self.assertEqual('a', found['col1'])

    def test_fill_cache_with_composite_key_order_by_primary_key(self):
        tbl = self._hst('fill_cache_composite', kind='composite')
        self._raw_insert(tbl, srgt=None, nk=1, begin=D1900, end=T2 - ONE_SECOND, col1='a')
        self._raw_insert(tbl, srgt=None, nk=1, begin=T2, end=D9999, col1='b')
        tbl.commit()
        tbl.fill_cache(order_by='-PK-')
        self.assertTrue(tbl.cache_filled)

    def test_get_by_lookup_uses_begin_date_from_row(self):
        tbl = self._hst('get_by_lookup_row')
        tbl.upsert(self._row(tbl, nk=1, col1='a'), effective_date=T1)
        tbl.upsert(self._row(tbl, nk=1, col1='b'), effective_date=T2)
        tbl.commit()
        tbl.default_effective_date = T3
        lookup_name = tbl.get_nk_lookup_name()
        found = tbl.get_by_lookup(lookup_name, self._row(tbl, nk=1, begin_date=T1))
        self.assertEqual('a', found['col1'])

    def test_get_by_lookup_defaults_to_default_effective_date(self):
        tbl = self._hst('get_by_lookup_default')
        tbl.upsert(self._row(tbl, nk=1, col1='a'), effective_date=T1)
        tbl.upsert(self._row(tbl, nk=1, col1='b'), effective_date=T2)
        tbl.commit()
        tbl.default_effective_date = T3
        found = tbl.get_by_lookup(tbl.get_nk_lookup_name(), self._row(tbl, nk=1))
        self.assertEqual('b', found['col1'])

    def test_get_by_lookup_and_effective_date_without_lookup_name_uses_default_lookup(self):
        tbl = self._hst('get_by_lookup_none')
        tbl.upsert(self._row(tbl, nk=1, col1='a'), effective_date=T1)
        tbl.commit()
        source_row = self._row(tbl, nk=1)
        found = tbl.get_by_lookup_and_effective_date(None, source_row, T2)
        self.assertEqual('a', found['col1'])

    def test_get_by_lookup_raises_for_unknown_key(self):
        tbl = self._hst('get_by_lookup_unknown')
        tbl.upsert(self._row(tbl, nk=1, col1='a'), effective_date=T1)
        tbl.commit()
        with self.assertRaises(NoResultFound):
            tbl.get_by_lookup(tbl.get_nk_lookup_name(), self._row(tbl, nk=2))

    def test_get_by_lookup_raises_before_all_existing(self):
        tbl = self._hst('get_by_lookup_before', inserts_use_default_begin_date=False)
        tbl.upsert(self._row(tbl, nk=1, col1='a'), effective_date=T2)
        tbl.commit()
        with self.assertRaises(BeforeAllExisting) as ctx:
            tbl.get_by_lookup(tbl.get_nk_lookup_name(), self._row(tbl, nk=1, begin_date=T1))
        self.assertEqual(T2, ctx.exception.first_existing_row['begin_date'])

    # ------------------------------------------------------------------
    # physically_delete_version
    # ------------------------------------------------------------------

    def _three_versions(self, tbl: HistoryTable):
        self._raw_insert(tbl, srgt=1, nk=1, begin=D1900, end=T2 - ONE_SECOND, col1='a')
        self._raw_insert(tbl, srgt=2, nk=1, begin=T2, end=T3 - ONE_SECOND, col1='b')
        self._raw_insert(tbl, srgt=3, nk=1, begin=T3, end=D9999, col1='c')
        tbl.commit()

    def _version_row(self, tbl: HistoryTable, col1: str):
        return [r for r in self._rows(tbl) if r['col1'] == col1][0]

    def test_physically_delete_middle_version_extends_prior_version(self):
        tbl = self._hst('phys_del_middle', kind='composite')
        self._three_versions(tbl)
        tbl.physically_delete_version(self._version_row(tbl, 'b'))
        self.assertEqual(
            [(D1900, T3 - ONE_SECOND, 'a', 'N'), (T3, D9999, 'c', 'N')],
            self._versions(tbl),
        )

    def test_physically_delete_last_version_extends_prior_to_end_of_time(self):
        tbl = self._hst('phys_del_last', kind='composite')
        self._three_versions(tbl)
        tbl.physically_delete_version(self._version_row(tbl, 'c'))
        self.assertEqual(
            [(D1900, T2 - ONE_SECOND, 'a', 'N'), (T2, D9999, 'b', 'N')],
            self._versions(tbl),
        )

    def test_physically_delete_first_version_moves_begin_date_of_following_version(self):
        tbl = self._hst('phys_del_first', auto_generate_key=False)
        self._three_versions(tbl)
        tbl.physically_delete_version(self._version_row(tbl, 'a'))
        self.assertEqual(
            [(D1900, T3 - ONE_SECOND, 'b', 'N'), (T3, D9999, 'c', 'N')],
            self._versions(tbl),
        )

    def test_physically_delete_first_version_keeps_begin_date_when_not_using_default(self):
        tbl = self._hst('phys_del_first_nodef', kind='composite', inserts_use_default_begin_date=False)
        self._three_versions(tbl)
        tbl.physically_delete_version(self._version_row(tbl, 'a'))
        self.assertEqual(
            [(T2, T3 - ONE_SECOND, 'b', 'N'), (T3, D9999, 'c', 'N')],
            self._versions(tbl),
        )

    def test_physically_delete_only_version(self):
        tbl = self._hst('phys_del_only', kind='composite')
        self._raw_insert(tbl, srgt=None, nk=1, begin=D1900, end=D9999, col1='a')
        tbl.commit()
        tbl.physically_delete_version(self._version_row(tbl, 'a'))
        self.assertEqual([], self._versions(tbl))

    def test_physically_delete_version_with_explicit_prior_row(self):
        tbl = self._hst('phys_del_prior', kind='composite')
        self._three_versions(tbl)
        prior = self._version_row(tbl, 'a')
        tbl.physically_delete_version(self._version_row(tbl, 'b'), prior_row=prior)
        self.assertEqual(
            [(D1900, T3 - ONE_SECOND, 'a', 'N'), (T3, D9999, 'c', 'N')],
            self._versions(tbl),
        )

    def test_physically_delete_version_with_prior_row_none_does_not_touch_other_rows(self):
        tbl = self._hst('phys_del_prior_none', kind='composite', inserts_use_default_begin_date=False)
        self._three_versions(tbl)
        tbl.physically_delete_version(self._version_row(tbl, 'b'), prior_row=None)
        self.assertEqual(
            [(D1900, T2 - ONE_SECOND, 'a', 'N'), (T3, D9999, 'c', 'N')],
            self._versions(tbl),
        )

    def test_physically_delete_version_with_unknown_status_row_reads_it(self):
        tbl = self._hst('phys_del_unknown', kind='composite')
        self._three_versions(tbl)
        key_only = tbl.Row(data={'nk': 1, 'begin_date': T2})
        key_only.status = RowStatus.unknown
        tbl.physically_delete_version(key_only)
        self.assertEqual(
            [(D1900, T3 - ONE_SECOND, 'a', 'N'), (T3, D9999, 'c', 'N')],
            self._versions(tbl),
        )

    def test_physically_delete_version_with_filled_cache(self):
        tbl = self._hst('phys_del_cache', kind='composite')
        self._three_versions(tbl)
        tbl.fill_cache()
        tbl.physically_delete_version(self._version_row(tbl, 'b'))
        self.assertEqual(
            [(D1900, T3 - ONE_SECOND, 'a', 'N'), (T3, D9999, 'c', 'N')],
            self._versions(tbl),
        )

    # ------------------------------------------------------------------
    # Logical deletes and update_not_in_set
    # ------------------------------------------------------------------

    def _two_keys(self, name: str, **kwargs) -> HistoryTable:
        tbl = self._hst(name, **kwargs)
        tbl.upsert(self._row(tbl, nk=1, col1='a'), effective_date=T1)
        tbl.upsert(self._row(tbl, nk=2, col1='b'), effective_date=T1)
        tbl.commit()
        return tbl

    def test_delete_not_processed_logically_deletes_missing_keys(self):
        tbl = self._hst('del_not_processed')
        tbl.track_source_rows = True
        tbl.upsert(self._row(tbl, nk=1, col1='a'), effective_date=T1)
        tbl.upsert(self._row(tbl, nk=2, col1='b'), effective_date=T1)
        tbl.commit()
        tbl.source_keys_processed = set()
        tbl.upsert(self._row(tbl, nk=1, col1='a'), effective_date=T2)
        tbl.commit()
        tbl.delete_not_processed(effective_date=T2)
        tbl.commit()
        self.assertEqual([(D1900, D9999, 'a', 'N')], self._versions(tbl, 1))
        self.assertEqual(
            [(D1900, T2 - ONE_SECOND, 'b', 'N'), (T2, D9999, 'b', 'Y')],
            self._versions(tbl, 2),
        )

    def test_delete_not_in_set_logically_deletes_keys_not_in_set(self):
        tbl = self._two_keys('del_not_in_set')
        keep = {tbl.get_natural_key_tuple(self._row(tbl, nk=1))}
        tbl.delete_not_in_set(keep, effective_date=T2)
        tbl.commit()
        self.assertEqual([(D1900, D9999, 'a', 'N')], self._versions(tbl, 1))
        self.assertEqual(
            [(D1900, T2 - ONE_SECOND, 'b', 'N'), (T2, D9999, 'b', 'Y')],
            self._versions(tbl, 2),
        )

    def test_update_not_in_set_updates_keys_not_in_set(self):
        tbl = self._two_keys('upd_not_in_set')
        keep = {tbl.get_natural_key_tuple(self._row(tbl, nk=1))}
        tbl.update_not_in_set({'col2': 'stale'}, keep, effective_date=T2)
        tbl.commit()
        rows = self._rows(tbl)
        self.assertEqual(3, len(rows))
        self.assertEqual([None], [r['col2'] for r in rows if r['nk'] == 1])
        self.assertEqual([None, 'stale'], [r['col2'] for r in rows if r['nk'] == 2])

    def test_update_not_in_set_with_criteria_list_and_dict(self):
        tbl = self._two_keys('upd_not_in_set_criteria')
        tbl.update_not_in_set(
            {'col2': 'stale'},
            set(),
            criteria_list=[tbl.get_column('col1') == 'b'],
            effective_date=T2,
        )
        tbl.update_not_in_set(
            {'col2': 'stale2'},
            set(),
            criteria_dict={'col1': 'a'},
            effective_date=T2,
        )
        tbl.commit()
        rows = self._rows(tbl)
        self.assertEqual(4, len(rows))
        self.assertEqual([None, 'stale2'], [r['col2'] for r in rows if r['nk'] == 1])
        self.assertEqual([None, 'stale'], [r['col2'] for r in rows if r['nk'] == 2])

    def test_update_not_in_set_with_explicit_lookup_name(self):
        tbl = self._two_keys('upd_not_in_set_lookup')
        lookup_name = tbl.get_nk_lookup_name()
        keep = {tbl.get_natural_key_tuple(self._row(tbl, nk=2))}
        tbl.update_not_in_set({'col2': 'stale'}, keep, lookup_name=lookup_name, effective_date=T2)
        tbl.commit()
        self.assertEqual([None, 'stale'], [r['col2'] for r in self._rows(tbl) if r['nk'] == 1])

    def test_update_not_in_set_logs_progress(self):
        tbl = self._two_keys('upd_not_in_set_progress')
        with self.assertLogs(tbl.log, level='INFO') as logs:
            tbl.update_not_in_set({'col2': 'stale'}, set(), effective_date=T2, progress_frequency=0.0000001)
        self.assertIn('update_not_in_set current', '\n'.join(logs.output))

    # ------------------------------------------------------------------
    # cleanup_versions
    # ------------------------------------------------------------------

    def _cleanup_table(self, name: str, **kwargs) -> HistoryTable:
        """
        Table with explicit surrogate keys and clean sentinel keys (0 and 99) around the data under test.

        The first row of the first key and the final end date of the last key are not checked by
        :meth:`HistoryTable.cleanup_versions`, so the sentinels keep the keys under test out of those positions.
        """
        kwargs.setdefault('auto_generate_key', False)
        tbl = self._hst(name, **kwargs)
        self._raw_insert(tbl, srgt=1000, nk=0, begin=D1900, end=D9999, col1='first')
        self._raw_insert(tbl, srgt=1099, nk=99, begin=D1900, end=D9999, col1='last')
        return tbl

    def _data_versions(self, tbl: HistoryTable, nk: int = 1):
        return self._versions(tbl, nk)

    def test_cleanup_versions_corrects_first_begin_date(self):
        tbl = self._cleanup_table('clean_begin')
        self._raw_insert(tbl, srgt=1, nk=1, begin=T1, end=D9999, col1='a')
        tbl.commit()
        with self.assertLogs(tbl.log, level='WARNING') as logs:
            tbl.cleanup_versions()
        self.assertIn('Correcting first version begin date', '\n'.join(logs.output))
        self.assertEqual([(D1900, D9999, 'a', 'N')], self._data_versions(tbl))

    def test_cleanup_versions_corrects_inter_version_end_date(self):
        tbl = self._cleanup_table('clean_end')
        self._raw_insert(tbl, srgt=1, nk=1, begin=D1900, end=T3, col1='a')
        self._raw_insert(tbl, srgt=2, nk=1, begin=T2, end=D9999, col1='b')
        tbl.commit()
        with self.assertLogs(tbl.log, level='WARNING') as logs:
            tbl.cleanup_versions()
        self.assertIn('Correcting end date', '\n'.join(logs.output))
        self.assertEqual(
            [(D1900, T2 - ONE_SECOND, 'a', 'N'), (T2, D9999, 'b', 'N')],
            self._data_versions(tbl),
        )

    def test_cleanup_versions_corrects_final_end_date(self):
        tbl = self._cleanup_table('clean_final_end')
        self._raw_insert(tbl, srgt=1, nk=1, begin=D1900, end=T2, col1='a')
        tbl.commit()
        with self.assertLogs(tbl.log, level='WARNING') as logs:
            tbl.cleanup_versions()
        self.assertIn('Correcting final version end date', '\n'.join(logs.output))
        self.assertEqual([(D1900, D9999, 'a', 'N')], self._data_versions(tbl))

    def test_cleanup_versions_clean_table_is_unchanged(self):
        tbl = self._cleanup_table('clean_noop')
        self._raw_insert(tbl, srgt=1, nk=1, begin=D1900, end=T2 - ONE_SECOND, col1='a')
        self._raw_insert(tbl, srgt=2, nk=1, begin=T2, end=D9999, col1='b')
        tbl.commit()
        before = self._versions(tbl)
        tbl.cleanup_versions()
        self.assertEqual(before, self._versions(tbl))

    def test_cleanup_versions_removes_redundant_versions(self):
        tbl = self._cleanup_table('clean_redundant')
        self._raw_insert(tbl, srgt=1, nk=1, begin=D1900, end=T2 - ONE_SECOND, col1='a')
        self._raw_insert(tbl, srgt=2, nk=1, begin=T2, end=D9999, col1='a')
        tbl.commit()
        tbl.cleanup_versions()
        self.assertEqual([(D1900, D9999, 'a', 'N')], self._data_versions(tbl))

    def test_cleanup_versions_keeps_redundant_versions_when_disabled(self):
        tbl = self._cleanup_table('clean_redundant_off')
        self._raw_insert(tbl, srgt=1, nk=1, begin=D1900, end=T2 - ONE_SECOND, col1='a')
        self._raw_insert(tbl, srgt=2, nk=1, begin=T2, end=D9999, col1='a')
        tbl.commit()
        tbl.cleanup_versions(remove_redundant_versions=False)
        self.assertEqual(2, len(self._data_versions(tbl)))

    def test_cleanup_versions_keeps_redundant_versions_by_default_with_generated_keys(self):
        tbl = self._cleanup_table('clean_redundant_autogen', auto_generate_key=True)
        self._raw_insert(tbl, srgt=1, nk=1, begin=D1900, end=T2 - ONE_SECOND, col1='a')
        self._raw_insert(tbl, srgt=2, nk=1, begin=T2, end=D9999, col1='a')
        tbl.commit()
        tbl.cleanup_versions()
        self.assertEqual(2, len(self._data_versions(tbl)))

    def test_cleanup_versions_exclude_from_compare(self):
        tbl = self._cleanup_table('clean_exclude')
        self._raw_insert(tbl, srgt=1, nk=1, begin=D1900, end=T2 - ONE_SECOND, col1='a')
        self._raw_insert(tbl, srgt=2, nk=1, begin=T2, end=D9999, col1='b')
        tbl.commit()
        tbl.cleanup_versions(exclude_from_compare=frozenset({'col1'}))
        self.assertEqual([(D1900, D9999, 'a', 'N')], self._data_versions(tbl))

    def test_cleanup_versions_removes_spurious_deletes(self):
        tbl = self._cleanup_table('clean_spurious')
        self._raw_insert(tbl, srgt=1, nk=1, begin=D1900, end=T2 - ONE_SECOND, col1='a', flag='N')
        self._raw_insert(tbl, srgt=2, nk=1, begin=T2, end=T3 - ONE_SECOND, col1='a', flag='Y')
        self._raw_insert(tbl, srgt=3, nk=1, begin=T3, end=D9999, col1='b', flag='N')
        tbl.commit()
        tbl.cleanup_versions(remove_spurious_deletes=True)
        self.assertEqual(
            [(D1900, T3 - ONE_SECOND, 'a', 'N'), (T3, D9999, 'b', 'N')],
            self._data_versions(tbl),
        )

    def test_cleanup_versions_keeps_spurious_deletes_by_default(self):
        tbl = self._cleanup_table('clean_spurious_off')
        self._raw_insert(tbl, srgt=1, nk=1, begin=D1900, end=T2 - ONE_SECOND, col1='a', flag='N')
        self._raw_insert(tbl, srgt=2, nk=1, begin=T2, end=T3 - ONE_SECOND, col1='a', flag='Y')
        self._raw_insert(tbl, srgt=3, nk=1, begin=T3, end=D9999, col1='b', flag='N')
        tbl.commit()
        tbl.cleanup_versions()
        self.assertEqual(3, len(self._data_versions(tbl)))

    def test_cleanup_versions_trace_data_logs_deletes(self):
        tbl = self._cleanup_table('clean_trace')
        tbl.trace_data = True
        self._raw_insert(tbl, srgt=1, nk=1, begin=D1900, end=T2 - ONE_SECOND, col1='a', flag='N')
        self._raw_insert(tbl, srgt=2, nk=1, begin=T2, end=T3 - ONE_SECOND, col1='a', flag='Y')
        self._raw_insert(tbl, srgt=3, nk=1, begin=T3, end=D9999, col1='b', flag='N')
        self._raw_insert(tbl, srgt=4, nk=2, begin=D1900, end=T2 - ONE_SECOND, col1='c')
        self._raw_insert(tbl, srgt=5, nk=2, begin=T2, end=D9999, col1='c')
        tbl.commit()
        with self.assertLogs(tbl.log, level='DEBUG') as logs:
            tbl.cleanup_versions(remove_spurious_deletes=True)
        output = '\n'.join(logs.output)
        self.assertIn('deleting spurious logical delete row', output)
        self.assertIn('deleting spurious unchanged row', output)
        self.assertTrue(tbl.trace_data)

    def test_cleanup_versions_limits_begin_date_warnings(self):
        tbl = self._cleanup_table('clean_begin_limit')
        self._raw_insert(tbl, srgt=1, nk=1, begin=T1, end=D9999, col1='a')
        self._raw_insert(tbl, srgt=2, nk=2, begin=T1, end=D9999, col1='b')
        tbl.commit()
        with self.assertLogs(tbl.log, level='WARNING') as logs:
            tbl.cleanup_versions(max_begin_date_warnings=1)
        output = '\n'.join(logs.output)
        self.assertIn("Limit reached for 'Correcting begin date' messages.", output)
        self.assertNotIn('Correcting first version begin date', output)
        self.assertEqual([(D1900, D9999, 'a', 'N')], self._data_versions(tbl, 1))
        self.assertEqual([(D1900, D9999, 'b', 'N')], self._data_versions(tbl, 2))

    def test_cleanup_versions_limits_final_end_date_warnings(self):
        tbl = self._cleanup_table('clean_final_limit')
        self._raw_insert(tbl, srgt=1, nk=1, begin=D1900, end=T2, col1='a')
        self._raw_insert(tbl, srgt=2, nk=2, begin=D1900, end=T2, col1='b')
        tbl.commit()
        with self.assertLogs(tbl.log, level='WARNING') as logs:
            tbl.cleanup_versions(max_end_date_warnings=1)
        output = '\n'.join(logs.output)
        self.assertIn("Limit reached for 'Correcting end date' messages.", output)
        self.assertNotIn('Correcting final version end date', output)

    def test_cleanup_versions_limits_inter_version_end_date_warnings(self):
        tbl = self._cleanup_table('clean_end_limit')
        self._raw_insert(tbl, srgt=1, nk=1, begin=D1900, end=T3, col1='a')
        self._raw_insert(tbl, srgt=2, nk=1, begin=T2, end=D9999, col1='b')
        tbl.commit()
        with self.assertLogs(tbl.log, level='WARNING') as logs:
            tbl.cleanup_versions(max_end_date_warnings=1)
        self.assertIn('Limit (1) reached', '\n'.join(logs.output))

    def test_cleanup_versions_max_passes_exceeded_raises(self):
        tbl = self._cleanup_table('clean_max_passes')
        with self.assertRaisesRegex(RuntimeError, 'cleanup_versions failed'):
            tbl.cleanup_versions(max_passes=0)

    def test_cleanup_versions_repeats_until_clean(self):
        tbl = self._cleanup_table('clean_repeat')
        self._raw_insert(tbl, srgt=1, nk=1, begin=T1, end=D9999, col1='a')
        tbl.commit()
        with self.assertLogs(tbl.log, level='DEBUG') as logs:
            tbl.cleanup_versions()
        self.assertIn('Repeating cleanup_versions check. Completed pass 1.', '\n'.join(logs.output))
        self.assertEqual([(D1900, D9999, 'a', 'N')], self._data_versions(tbl))

    def test_cleanup_versions_single_pass_when_repeat_disabled(self):
        tbl = self._cleanup_table('clean_no_repeat')
        self._raw_insert(tbl, srgt=1, nk=1, begin=T1, end=D9999, col1='a')
        tbl.commit()
        with self.assertLogs(tbl.log, level='DEBUG') as logs:
            tbl.cleanup_versions(repeat_until_clean=False)
        self.assertNotIn('Repeating cleanup_versions check', '\n'.join(logs.output))
        self.assertEqual([(D1900, D9999, 'a', 'N')], self._data_versions(tbl))

    def test_cleanup_versions_merges_consecutive_redundant_versions(self):
        tbl = self._cleanup_table('clean_consecutive')
        self._insert_three_redundant_versions(tbl)
        tbl.cleanup_versions()
        self.assertEqual([(D1900, D9999, 'a', 'N')], self._data_versions(tbl))

    def test_cleanup_versions_single_pass_merges_consecutive_redundant_versions(self):
        tbl = self._cleanup_table('clean_consecutive_one_pass')
        self._insert_three_redundant_versions(tbl)
        tbl.cleanup_versions(repeat_until_clean=False)
        self.assertLess(len(self._data_versions(tbl)), 3)

    def _insert_three_redundant_versions(self, tbl: HistoryTable):
        """Insert three consecutive versions of nk 1 that differ only by their dates."""
        for srgt, begin, end in [
            (1, D1900, T2 - ONE_SECOND),
            (2, T2, T3 - ONE_SECOND),
            (3, T3, D9999),
        ]:
            self._raw_insert(tbl, srgt=srgt, nk=1, begin=begin, end=end, col1='a')
        tbl.commit()

    def test_cleanup_versions_with_explicit_lookup_name(self):
        tbl = self._cleanup_table('clean_lookup')
        self._raw_insert(tbl, srgt=1, nk=1, begin=D1900, end=T3, col1='a')
        self._raw_insert(tbl, srgt=2, nk=1, begin=T2, end=D9999, col1='b')
        tbl.commit()
        tbl.cleanup_versions(lookup_name=tbl.get_nk_lookup_name())
        self.assertEqual(
            [(D1900, T2 - ONE_SECOND, 'a', 'N'), (T2, D9999, 'b', 'N')],
            self._data_versions(tbl),
        )

    def test_cleanup_versions_without_natural_key_uses_primary_key_lookup(self):
        tbl = self._cleanup_table('clean_no_nk', kind='composite', natural_key=None)
        tbl.cleanup_versions()
        self.assertEqual(2, len(self._rows(tbl)))

    def test_cleanup_versions_with_criteria_uses_database_source(self):
        tbl = self._cleanup_table('clean_criteria')
        self._raw_insert(tbl, srgt=1, nk=1, begin=D1900, end=T3, col1='a')
        self._raw_insert(tbl, srgt=2, nk=1, begin=T2, end=D9999, col1='b')
        tbl.commit()
        tbl.fill_cache()
        with self.assertLogs(tbl.log, level='WARNING') as logs:
            tbl.cleanup_versions(criteria_list=[tbl.get_column('nk') == 1])
        self.assertIn('had to use DB source to honor criteria_list', '\n'.join(logs.output))

    def test_cleanup_versions_without_filled_cache_uses_database_source(self):
        tbl = self._cleanup_table('clean_no_cache')
        with self.assertLogs(tbl.log, level='WARNING') as logs:
            tbl.cleanup_versions(use_cache_as_source=True)
        self.assertIn('had to use DB source since cache_filled', '\n'.join(logs.output))

    def test_cleanup_versions_with_filled_cache_as_source(self):
        tbl = self._cleanup_table('clean_cache')
        self._raw_insert(tbl, srgt=1, nk=1, begin=D1900, end=T3, col1='a')
        self._raw_insert(tbl, srgt=2, nk=1, begin=T2, end=D9999, col1='b')
        tbl.commit()
        tbl.fill_cache()
        tbl.cleanup_versions(use_cache_as_source=True)
        self.assertEqual(
            [(D1900, T2 - ONE_SECOND, 'a', 'N'), (T2, D9999, 'b', 'N')],
            self._data_versions(tbl),
        )

    def test_cleanup_versions_progress_message_logged(self):
        tbl = self._cleanup_table('clean_progress')
        tbl.progress_frequency = 0.0000001
        with self.assertLogs(tbl.log, level='INFO') as logs:
            tbl.cleanup_versions(progress_message='{table} pass {pass_number} row {row_number}')
        self.assertIn(' pass 1 row ', '\n'.join(logs.output))
        self.assertEqual(0.0000001, tbl.progress_frequency)

    # ------------------------------------------------------------------
    # Special values and mapping checks
    # ------------------------------------------------------------------

    def test_upsert_special_values_rows_is_idempotent(self):
        tbl = self._hst('special_rows')
        tbl.upsert_special_values_rows()
        first = self._versions(tbl)
        self.assertGreaterEqual(len(first), 4)
        for begin, end, _col1, _flag in first:
            self.assertEqual(D1900, begin)
            self.assertEqual(D9999, end)
        tbl.upsert_special_values_rows()
        self.assertEqual(first, self._versions(tbl))
        self.assertTrue(tbl.auto_generate_key)

    def test_sanity_check_source_mapping_ignores_date_columns_and_type_1_surrogate(self):
        tbl = self._hst('sanity', type_1_surrogate='t1_srgt')
        source = SimpleNamespace(column_names_set=None)
        with mock.patch.object(Table, 'sanity_check_source_mapping') as parent_check:
            tbl.sanity_check_source_mapping(source, target_excludes=frozenset({'col2'}))
        self.assertEqual(
            frozenset({'col2', 'begin_date', 'end_date', 't1_srgt'}),
            parent_check.call_args.kwargs['target_excludes'],
        )

    # ------------------------------------------------------------------
    # sql_upsert
    # ------------------------------------------------------------------

    @staticmethod
    def _fake_source():
        return SimpleNamespace(
            column_names_set={'nk', 'col1', 'col2', 'begin_date'},
            qualified_table_name='fake_source',
        )

    def _make_source(self, name: str, rows: list) -> Table:
        """Create a source table with ``rows`` of (nk, col1, col2, begin_date) and return a :class:`Table` on it."""
        table_name = self._get_table_name(name)
        self.mock_database.drop_table_if_exists(table_name)
        sa_table = sqlalchemy.schema.Table(
            table_name,
            self.mock_database,
            Column('nk', Integer),
            Column('col1', self._TEXT()),
            Column('col2', self._TEXT()),
            Column('begin_date', DateTime),
        )
        sa_table.create(bind=self.mock_database.bind)
        self.addCleanup(self.mock_database.drop_table_if_exists, table_name)
        src = Table(self.task, self.mock_database, table_name=table_name)
        self.addCleanup(src.close)
        for nk, col1, col2, begin_date in rows:
            src.insert_row(src.Row(data={'nk': nk, 'col1': col1, 'col2': col2, 'begin_date': begin_date}))
        src.commit()
        return src

    def test_sql_upsert_rejects_empty_natural_key(self):
        tbl = self._hst('sql_upsert_empty_nk', natural_key=[])
        with self.assertRaisesRegex(ValueError, 'natural key not set'):
            tbl.sql_upsert(self._fake_source(), 'begin_date')

    def test_sql_upsert_rejects_natural_key_without_auto_generate_key(self):
        tbl = self._hst('sql_upsert_nk_no_autogen', auto_generate_key=False)
        with self.assertRaisesRegex(ValueError, 'autogenerate_key = False'):
            tbl.sql_upsert(self._fake_source(), 'begin_date')

    def test_sql_upsert_rejects_table_without_keys(self):
        tbl = self._hst('sql_upsert_no_keys', kind='none', primary_key=None, natural_key=None, auto_generate_key=False)
        with self.assertRaisesRegex(ValueError, 'Empty natural key'):
            tbl.sql_upsert(self._fake_source(), 'begin_date')

    def test_sql_upsert_rejects_composite_primary_key(self):
        tbl = self._hst('sql_upsert_composite', kind='composite', auto_generate_key=True)
        with self.assertRaisesRegex(ValueError, 'requires single primary_key'):
            tbl.sql_upsert(self._fake_source(), 'begin_date')

    def _check_sql_upsert_two_loads(self, tbl: HistoryTable, **upsert_kwargs):
        src1 = self._make_source('sql_src1', [(1, 'a1', 'x', T1), (2, 'b1', 'x', T1)])
        tbl.get_current_time = lambda: T1
        tbl.begin()
        tbl.sql_upsert(src1, 'begin_date', **upsert_kwargs)
        tbl.commit()
        self.assertEqual(['a1'], [v[2] for v in self._versions(tbl, 1)])
        self.assertEqual(['b1'], [v[2] for v in self._versions(tbl, 2)])

        src2 = self._make_source('sql_src2', [(1, 'a2', 'x', T2), (3, 'c1', 'x', T2)])
        tbl.get_current_time = lambda: T2
        tbl.begin()
        tbl.sql_upsert(src2, 'begin_date', **upsert_kwargs)
        tbl.commit()

        nk1 = self._versions(tbl, 1)
        self.assertEqual(['a1', 'a2'], [v[2] for v in nk1])
        self.assertEqual(T2 - ONE_SECOND, nk1[0][1])
        self.assertEqual(D9999, nk1[1][1])
        self.assertEqual(['c1'], [v[2] for v in self._versions(tbl, 3)])
        return self._versions(tbl, 2)

    def test_sql_upsert_inserts_new_keys_and_new_versions(self):
        tbl = self._hst('sql_upsert_basic')
        nk2 = self._check_sql_upsert_two_loads(tbl, check_for_deletes=False)
        self.assertEqual([('b1', 'N')], [(v[2], v[3]) for v in nk2])

    def test_sql_upsert_adds_logical_delete_versions_for_missing_keys(self):
        tbl = self._hst('sql_upsert_deletes')
        nk2 = self._check_sql_upsert_two_loads(tbl, check_for_deletes=True)
        self.assertEqual([('b1', 'N'), ('b1', 'Y')], [(v[2], v[3]) for v in nk2])
        self.assertEqual(T2 - ONE_SECOND, nk2[0][1])
        self.assertEqual(D9999, nk2[1][1])

    def test_sql_upsert_check_for_deletes_defaults_on_with_delete_flag(self):
        tbl = self._hst('sql_upsert_deletes_default')
        nk2 = self._check_sql_upsert_two_loads(tbl)
        self.assertEqual(2, len(nk2))

    def test_sql_upsert_commit_each_table(self):
        tbl = self._hst('sql_upsert_commit_each')
        nk2 = self._check_sql_upsert_two_loads(tbl, check_for_deletes=True, commit_each_table=True)
        self.assertEqual(2, len(nk2))

    def test_sql_upsert_with_type_1_surrogate(self):
        tbl = self._hst('sql_upsert_type1', type_1_surrogate='t1_srgt')
        self._check_sql_upsert_two_loads(tbl, check_for_deletes=False)
        rows = self._rows(tbl)
        nk1 = [r for r in rows if r['nk'] == 1]
        self.assertEqual(2, len(nk1))
        self.assertIsNotNone(nk1[0]['t1_srgt'])
        self.assertEqual(nk1[0]['t1_srgt'], nk1[1]['t1_srgt'])

    def test_sql_upsert_with_last_update_date(self):
        tbl = self._hst('sql_upsert_last_upd', last_update_date='last_upd')
        self._check_sql_upsert_two_loads(tbl, check_for_deletes=True)
        for row in self._rows(tbl):
            self.assertIsNotNone(row['last_upd'])

    def test_sql_upsert_check_for_deletes_defaults_off_without_delete_flag(self):
        tbl = self._hst('sql_upsert_no_flag', delete_flag=None)
        nk2 = self._check_sql_upsert_two_loads(tbl)
        self.assertEqual(1, len(nk2))

    def _sql_upsert_second_load(self, tbl: HistoryTable, first_row: tuple, second_row: tuple, **upsert_kwargs):
        """Load ``first_row`` at T1, then ``second_row`` at T2 with ``upsert_kwargs``. Rows are (nk, col1, col2)."""
        src1 = self._make_source('sql_skip_src1', [(*first_row, T1)])
        tbl.get_current_time = lambda: T1
        tbl.begin()
        tbl.sql_upsert(src1, 'begin_date', check_for_deletes=False)
        tbl.commit()
        src2 = self._make_source('sql_skip_src2', [(*second_row, T2)])
        tbl.get_current_time = lambda: T2
        tbl.begin()
        tbl.sql_upsert(src2, 'begin_date', check_for_deletes=False, **upsert_kwargs)
        tbl.commit()

    def test_sql_upsert_skip_update_check_on_ignores_skipped_column(self):
        tbl = self._hst('sql_upsert_skip_check')
        self._sql_upsert_second_load(
            tbl, (1, 'a1', 'x1'), (1, 'a2', 'x1'), skip_update_check_on=frozenset({'col1'})
        )
        self.assertEqual(1, len(self._versions(tbl, 1)))

    def test_sql_upsert_skip_update_check_on_still_checks_other_columns(self):
        tbl = self._hst('sql_upsert_skip_other')
        self._sql_upsert_second_load(
            tbl, (1, 'a1', 'x1'), (1, 'a2', 'x2'), skip_update_check_on=frozenset({'col1'})
        )
        self.assertEqual(2, len(self._versions(tbl, 1)))

    def test_sql_upsert_leaves_target_only_column_untouched_by_compare(self):
        tbl = self._hst('sql_upsert_target_only')
        self._sql_upsert_second_load(tbl, (1, 'a1', 'x1'), (1, 'a2', 'x1'))
        self.assertEqual(2, len(self._versions(tbl, 1)))
        self.assertEqual([None, None], [r['col3'] for r in self._rows(tbl) if r['nk'] == 1])

    def test_sql_upsert_rejects_no_columns_to_compare(self):
        tbl = self._hst('sql_upsert_no_compare')
        with self.assertRaisesRegex(ValueError, 'No columns to compare'):
            tbl.sql_upsert(
                self._fake_source(),
                'begin_date',
                skip_update_check_on=frozenset({'col1', 'col2'}),
            )


del BaseTestHstTable