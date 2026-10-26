import logging
from datetime import datetime, date
from types import SimpleNamespace

import pytest
import sqlalchemy

from bi_etl.statement_queue import StatementQueue


class DatabricksStatementCompiler:
    """Stand in for the Databricks dialect compiler class (matched by type name)."""

    def __str__(self):
        return "SELECT 1"


@pytest.fixture(autouse=True)
def reset_warning_state():
    StatementQueue._compiled_warning_logged.clear()
    yield
    StatementQueue._compiled_warning_logged.clear()


def test_add_statement_restores_compiled_statement():
    queue = StatementQueue()
    queue.add_statement('k', DatabricksStatementCompiler())
    stmt = queue.get_statement_by_key('k')
    assert isinstance(stmt, sqlalchemy.sql.elements.TextClause)
    assert str(stmt) == "SELECT 1"


def test_add_statement_leaves_regular_statement():
    queue = StatementQueue()
    original = sqlalchemy.text("SELECT 2")
    queue.add_statement('k', original)
    assert queue.get_statement_by_key('k') is original


def test_warning_logged_once_with_call_stack(caplog):
    queue = StatementQueue()
    with caplog.at_level(logging.WARNING):
        queue.add_statement('a', DatabricksStatementCompiler())
        queue.add_statement('b', DatabricksStatementCompiler())
    warnings = [r for r in caplog.records if 'DatabricksStatementCompiler' in r.getMessage()]
    assert len(warnings) == 1
    assert 'test_warning_logged_once_with_call_stack' in warnings[0].getMessage()


def test_execute_check_restores_and_warns_once(caplog):
    queue = StatementQueue()
    # Bypass add_statement to simulate a statement that reached the queue directly
    queue.statements['k'] = DatabricksStatementCompiler()
    queue.append_values_by_key('k', {'x': 1})

    class FakeResult:
        rowcount = 1

    class FakeConnection:
        executed = []

        def execute(self, stmt, values):
            self.executed.append(stmt)
            return FakeResult()

    connection = FakeConnection()
    with caplog.at_level(logging.WARNING):
        queue.execute(connection)
    assert isinstance(connection.executed[0], sqlalchemy.sql.elements.TextClause)
    assert isinstance(queue.statements['k'], sqlalchemy.sql.elements.TextClause)
    warnings = [r for r in caplog.records if 'in execute' in r.getMessage()]
    assert len(warnings) == 1
 

class RecordingConnection:
    """Fake connection that records executed calls and returns a fixed rowcount."""

    def __init__(self, rowcount=1, fail_on_call=None):
        self.rowcount = rowcount
        self.fail_on_call = fail_on_call
        self.calls = []

    def execute(self, stmt, *args):
        # Copy lists because the queue clears its values lists after executing
        self.calls.append((stmt, *[list(a) if isinstance(a, list) else a for a in args]))
        if self.fail_on_call is not None and len(self.calls) == self.fail_on_call:
            raise RuntimeError("boom")
        return SimpleNamespace(rowcount=self.rowcount)


def test_len_and_append_values_by_key():
    queue = StatementQueue()
    assert len(queue) == 0
    queue.append_values_by_key('k', {'x': 1})
    queue.append_values_by_key('k', {'x': 2})
    queue.append_values_by_key('other', {'x': 3})
    assert len(queue) == 3
    assert queue.statement_values['k'] == [{'x': 1}, {'x': 2}]
    assert queue.statement_values['other'] == [{'x': 3}]


def test_get_statement_by_key_missing_returns_none():
    assert StatementQueue().get_statement_by_key('missing') is None


@pytest.mark.parametrize(
    'value, expected',
    [
        ('abc', "'abc'"),
        ("O'Brien", "'O''Brien'"),
        (datetime(2020, 1, 2, 3, 4, 5), "'2020-01-02T03:04:05'"),
        (datetime(2020, 1, 2, 3, 4, 5, 123000), "'2020-01-02 03:04:05.123'"),
        (datetime(2020, 1, 2, 3, 4, 5, 5000), "'2020-01-02 03:04:05.005'"),
        (datetime(2020, 1, 2, 3, 4, 5, 50000), "'2020-01-02 03:04:05.050'"),
        (datetime(2020, 1, 2, 3, 4, 5, 999), "'2020-01-02 03:04:05.000'"),
        (date(2020, 1, 2), "'2020-01-02'"),
        (None, 'Null'),
        (5, '5'),
        (1.5, '1.5'),
    ]
)
def test_encapsulate_value(value, expected):
    assert StatementQueue.encapsulate_value(value) == expected


def test_encapsulate_row_value_list():
    row = ['a', None, 3, date(2020, 1, 2)]
    assert StatementQueue.encapsulate_row_value_list(row) == "'a',Null,3,'2020-01-02'"


def test_values_str_list_single_group():
    queue = StatementQueue()
    assert queue.values_str_list([(1, 'a'), (2, 'b')]) == ["(1,'a'),(2,'b')"]


def test_values_str_list_empty_rows():
    assert StatementQueue().values_str_list([]) == [""]


def test_values_str_list_row_limit():
    queue = StatementQueue()
    result = queue.values_str_list([(1,), (2,), (3,)], row_limit=2)
    assert result == ["(1),(2)", "(3)"]


def test_values_str_list_uses_default_row_limit():
    queue = StatementQueue()
    queue.row_limit = 1
    assert queue.values_str_list([(1,), (2,)]) == ["(1)", "(2)"]


def test_values_str_list_size_soft_limit():
    queue = StatementQueue()
    result = queue.values_str_list([(1,), (2,), (3,)], size_soft_limit=3)
    assert result == ["(1)", "(2)", "(3)"]


def test_print_details(capsys):
    queue = StatementQueue()
    queue.add_statement('k', sqlalchemy.text("SELECT 1"))
    queue.append_values_by_key('k', {'x': 1})
    queue.print_details()
    out = capsys.readouterr().out
    assert "Statement Queue:" in out
    assert "values count = 1" in out
    assert "{'x': 1}" in out


def test_execute_empty_queue_does_nothing():
    queue = StatementQueue()
    queue.add_statement('k', sqlalchemy.text("SELECT 1"))
    connection = RecordingConnection()
    assert queue.execute(connection) == 0
    assert connection.calls == []


def test_execute_with_binds_sums_rowcount_and_clears_queue():
    queue = StatementQueue()
    stmt = sqlalchemy.text("INSERT INTO t VALUES (:x)")
    queue.add_statement('k', stmt)
    queue.append_values_by_key('k', {'x': 1})
    queue.append_values_by_key('k', {'x': 2})
    connection = RecordingConnection(rowcount=2)
    assert queue.execute(connection) == 2
    assert connection.calls == [(stmt, [{'x': 1}, {'x': 2}])]
    assert len(queue) == 0
    assert queue.statement_values['k'] == []
    # Second execute has nothing to do
    assert queue.execute(connection) == 0
    assert len(connection.calls) == 1


def test_execute_unknown_rowcount_uses_value_count():
    queue = StatementQueue()
    queue.add_statement('k', sqlalchemy.text("INSERT INTO t VALUES (:x)"))
    for i in range(3):
        queue.append_values_by_key('k', {'x': i})
    assert queue.execute(RecordingConnection(rowcount=-1)) == 3


def test_execute_multiple_statements():
    queue = StatementQueue()
    stmt_a = sqlalchemy.text("INSERT INTO a VALUES (:x)")
    stmt_b = sqlalchemy.text("INSERT INTO b VALUES (:x)")
    queue.add_statement('a', stmt_a)
    queue.add_statement('b', stmt_b)
    queue.append_values_by_key('a', {'x': 1})
    queue.append_values_by_key('b', {'x': 2})
    connection = RecordingConnection(rowcount=1)
    assert queue.execute(connection) == 2
    assert {call[0] for call in connection.calls} == {stmt_a, stmt_b}


def test_execute_without_binds_formats_values_into_statement():
    queue = StatementQueue(execute_with_binds=False)
    queue.row_limit = 2
    queue.add_statement('k', "INSERT INTO t VALUES {values}")
    for i in range(3):
        queue.append_values_by_key('k', (i, 'v'))
    connection = RecordingConnection(rowcount=-1)
    assert queue.execute(connection) == 6
    assert connection.calls == [
        ("INSERT INTO t VALUES (0,'v'),(1,'v')",),
        ("INSERT INTO t VALUES (2,'v')",),
    ]
    assert len(queue) == 0


def test_iter_single_statements():
    queue = StatementQueue()
    stmt_a = sqlalchemy.text("a")
    stmt_b = sqlalchemy.text("b")
    queue.add_statement('a', stmt_a)
    queue.add_statement('b', stmt_b)
    queue.append_values_by_key('a', {'x': 1})
    queue.append_values_by_key('a', {'x': 2})
    queue.append_values_by_key('b', {'x': 3})
    assert list(queue.iter_single_statements()) == [
        (stmt_a, {'x': 1}),
        (stmt_a, {'x': 2}),
        (stmt_b, {'x': 3}),
    ]


def test_iter_single_statements_empty():
    queue = StatementQueue()
    queue.add_statement('a', sqlalchemy.text("a"))
    assert list(queue.iter_single_statements()) == []


def test_execute_singly_with_binds():
    queue = StatementQueue()
    stmt = sqlalchemy.text("INSERT INTO t VALUES (:x)")
    queue.add_statement('k', stmt)
    queue.append_values_by_key('k', {'x': 1})
    queue.append_values_by_key('k', {'x': 2})
    connection = RecordingConnection(rowcount=1)
    assert queue.execute_singly(connection) == 2
    assert connection.calls == [(stmt, {'x': 1}), (stmt, {'x': 2})]


def test_execute_singly_without_binds():
    queue = StatementQueue(execute_with_binds=False)
    queue.add_statement('k', "INSERT INTO t VALUES {values}")
    queue.append_values_by_key('k', (1, 'a'))
    queue.append_values_by_key('k', (2, 'b'))
    connection = RecordingConnection(rowcount=1)
    assert queue.execute_singly(connection) == 2
    assert connection.calls == [
        ("INSERT INTO t VALUES (1,'a')",),
        ("INSERT INTO t VALUES (2,'b')",),
    ]


def test_execute_singly_error_raises_statement_error_and_logs(caplog):
    queue = StatementQueue()
    queue.add_statement('k', sqlalchemy.text("INSERT INTO t VALUES (:x)"))
    queue.append_values_by_key('k', {'x': 1})
    queue.append_values_by_key('k', {'x': 2})
    connection = RecordingConnection(fail_on_call=2)
    with caplog.at_level(logging.ERROR):
        with pytest.raises(sqlalchemy.exc.StatementError):
            queue.execute_singly(connection)
    assert any('row 1' in r.getMessage() and 'boom' in r.getMessage() for r in caplog.records)