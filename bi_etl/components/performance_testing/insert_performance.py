import pymssql
import pyodbc

from bi_etl.bi_config_parser import BIConfigParser

from bi_etl.database.connect import Connect

import keyring
# MSQL functions Version 0.5
import sqlalchemy
from datetime import datetime, date
import time


def encapsulate_value(value) -> str:
    # Encapsulate the input for SQL use (add ' etc)
    if isinstance(value, str):
        return "N'" + value.replace("'", "''") + "'"
    # Note we need to check datetime before date because a date passes both isinstance
    elif isinstance(value, datetime):
        if value.microsecond == 0:
            return "'" + value.isoformat() + "'"
        else:
            # For SQL Server dateime that can only hold milliseconds not microseconds
            return f"'{value:%Y-%m-%d %H:%M:%S}.{int(value.microsecond/1000)}{value:%z}'"
    elif isinstance(value, date):
        return "'" + value.isoformat() + "'"
    elif value is None:
        return 'Null'
    else:
        return str(value)


def encapsulate_list(value_list: list) -> str:
    return ','.join([encapsulate_value(v) for v in value_list])


def values_list(rows, row_limit: int = 1000, size_soft_limit: int = 60000):
    # Takes a list of items and make them in format for SQL insert
    cl_lists = []
    cl = []
    line_counter = 0
    size = 0
    for i in rows:
        if line_counter >= row_limit or size > size_soft_limit:
            cl_lists.append(",".join(cl))
            cl = []
            line_counter = 0
        row_str = "(" + encapsulate_list(i) + ")"
        cl.append(row_str)
        size += len(row_str) + 1  # One extra for comma separator
        line_counter += 1
    cl_lists.append(",".join(cl))
    return cl_lists


def now():
    return time.perf_counter()


def timepassed(time_started, message):
    print( f"{message:55s} took {now() - time_started:3.4f}")


def print_rows(cursor):
    result = cursor.execute("SELECT count(*) as cnt from perf_test")
    if result is not None:
        for row in result:
            print(f"Rows = {row[0]}")
    else:
        for row in cursor:
            print(f"Rows = {row[0]}")


def test_connection(test, con, row_list, do_execute_many=True, do_enlist=True, do_singly=False, fast_executemany=True):
    if hasattr(con, 'cursor'):
        cursor = con.cursor()
        try:
            cursor.fast_executemany = fast_executemany
            print(f"fast_executemany on raw = {fast_executemany}")
        except AttributeError:
            pass
    else:
        cursor = con

    rows = len(row_list)
    cols = 'c1,c2,dt,dt2,i1,f1,d1'
    col_cnt = len(cols.split(','))

    if do_execute_many:
        cursor.execute("TRUNCATE TABLE perf_test")
        started = now()
        try:
            cursor.executemany(f"INSERT INTO perf_test ({cols}) VALUES ({','.join(['?'] * col_cnt)})", row_list)
            con.commit()
            timepassed(started, f'{test}: {rows} to DB executemany')
        except ValueError as e:
            print(e)
        except AttributeError:
            # sqlalchemy section
            print(f"style={con.dialect.paramstyle}")
            if con.dialect.paramstyle == 'qmark':
                cursor.execute(f"INSERT INTO perf_test ({cols}) VALUES ({','.join(['?'] * col_cnt)})", row_list)
            else:
                # cursor.execute("INSERT INTO perf_test (c1,c2,dt,i1,f1,d1) VALUES (%(c1)s, %(c2)s, %(dt)s, %(i1)s, %(f1)s, %(d1)s)", row_list)
                cursor.execute(f"INSERT INTO perf_test ({cols}) VALUES ({','.join(['%s'] * col_cnt)})", row_list)
            try:
                con.commit()
            except AttributeError:
                pass
            timepassed(started, f'{test}: {rows} to DB executemany sqlalchemy')
        print_rows(cursor)

    if do_enlist:
        # for enlist_max in [1, 10, 20, 50, 100, 250, 500, 1000]:
        for enlist_max in [1000]:
            cursor.execute("TRUNCATE TABLE perf_test")
            started = now()
            for data in values_list(row_list, enlist_max):
                cursor.execute(f"INSERT INTO perf_test ({cols}) VALUES {data}")
            try:
                con.commit()
            except AttributeError:
                pass
            timepassed(started, f'{test}: {rows} to DB values_list {enlist_max:4d}  ')
        print_rows(cursor)

    if do_singly:
        cursor.execute("TRUNCATE TABLE perf_test")
        started = now()
        try:
            for data in row_list:
                cursor.execute(f"Insert into perf_test ({cols}) Values ({','.join(['?'] * col_cnt)})", data)
        except ValueError:
            cols = ['c1', 'c2', 'dt', 'i1', 'f1', 'd1']
            for data in row_list:
                data_dict = dict(zip(cols, data))
                cursor.execute(f"Insert into perf_test ({cols}) Values (%(c1)s, %(c2)s, %(dt)s, %(i1)s, %(f1)s, %(d1)s)", data_dict)
        except sqlalchemy.exc.ProgrammingError:
            if con.dialect.paramstyle == 'qmark':
                for data in row_list:
                    cursor.execute(f"Insert into perf_test ({cols}) Values ({','.join(['?'] * col_cnt)})", data)
            else:
                for data in row_list:
                    cursor.execute(f"INSERT INTO perf_test ({cols}) VALUES ({','.join(['%s'] * col_cnt)})", data)

        try:
            con.commit()
        except AttributeError:
            pass
        timepassed(started, f'{test}: {rows} to DB single execute')
        print_rows(cursor)

    # TODO: print s.compile(compile_kwargs={"literal_binds": True})
    # https://stackoverflow.com/questions/5631078/sqlalchemy-print-the-actual-query

    cursor.close()


def main():
    server = 'db-dev.pdh.datim.internal'
    user = 'systemBI'
    password = keyring.get_password('BI_Cache', user)
    database_name = 'data_warehouse_qnext'
    # charset=utf8
    # {SQL Server} - released with SQL Server 2000
    row_list = []
    rows = 1500
    for i in range(rows):
        dt = datetime(2017, (12 - i) % 12 + 1, i % 28 + 1,
                      10, i % 60, 33,
                      123000)
        dt2 = datetime.now()
        row_list.append([
            f'hello{i}',
            f'2this is a test #{i}',
            dt,
            dt2,
            i,
            i/10,
            i/100,
            ]
        )

    print("Starting test")

    # connection_str = f"DRIVER={{SQL server}};SERVER={server};UID={user};Database={database_name};PWD={password}"
    # con = pyodbc.connect(connection_str)
    # test_connection('base odbc', con, row_list)
    # con.close()

    # connection_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};UID={user};Database={database_name};PWD={password}"
    # con = pyodbc.connect(connection_str)
    # test_connection('odbc 17', con, row_list,
    #                 do_execute_many=False)
    # con.close()
    #
    # engine = sqlalchemy.create_engine(f"mssql+pymssql://{user}:{password}@{server}/{database_name}?charset=utf8")
    # con = engine.connect()
    # con = con.engine.raw_connection()
    # test_connection('sqlalchemy mssql+pymssql', con, row_list,
    #                 do_enlist=False,
    #                 do_execute_many=True)
    # con.close()
    # engine = sqlalchemy.create_engine(f"mssql+pymssql://{user}:{password}@{server}/{database_name}?charset=utf8")
    # con = engine.connect()
    # test_connection('sqlalchemy mssql+pymssql', con, row_list,
    #                 do_enlist=True,
    #                 do_execute_many=True,
    #                 fast_executemany=False,
    #                 )
    # con.close()

    config = BIConfigParser()
    config.read_config_ini()
    engine = Connect.get_sqlachemy_engine(config, 'perf_test')
    test_connection(f'sqlalchemy perf_test {engine}', con, row_list,
                    do_enlist=False,
                    do_execute_many=True,
                    fast_executemany=False,
                    )

    # con = engine.connect()
    # con = con.engine.raw_connection()
    # test_connection('sqlalchemy mssql+pymssql', con, row_list,
    #                 do_enlist=False,
    #                 do_execute_many=True)
    # con.close()

    engine = sqlalchemy.create_engine(f"mssql+pyodbc://{user}:{password}@{server}/{database_name}?driver=ODBC+Driver+17+for+SQL+Server",
                                      fast_executemany=True)  # Requires sqlalchemy 1.3+ and only works with pyodbc
    con = engine.connect()
    test_connection('sqlalchemy mssql+pyodbc with fast_executemany', con, row_list,
                    do_enlist=False,
                    do_execute_many=True,
                    fast_executemany=True
                    )
    con.close()

    # engine = sqlalchemy.create_engine(
    #     f"mssql+pyodbc://{user}:{password}@{server}:1433/{database_name}?driver=ODBC+Driver+17+for+SQL+Server")
    # con = engine.connect()
    # test_connection('sqlalchemy mssql+pyodbc without fast_executemany', con, row_list,
    #                 do_enlist=True,
    #                 do_execute_many=True,
    #                 fast_executemany=False,
    #                 )
    # con.close()
    # engine = sqlalchemy.create_engine(
    #     f"mssql+pyodbc://{user}:{password}@{server}:1433/{database_name}?driver=ODBC+Driver+17+for+SQL+Server")
    # con = engine.connect()
    # test_connection('sqlalchemy mssql+pymssql', con, row_list,
    # test_connection('sqlalchemy->RAW mssql+pyodbc fast_executemany', con, row_list,
    #                 do_enlist=False,
    #                 do_execute_many=True,
    #                 fast_executemany=True,
    #                 )
    # con.close()

    engine = sqlalchemy.create_engine(f"mssql+pyodbc://{user}:{password}@{server}:1433/{database_name}?driver=ODBC+Driver+17+for+SQL+Server")
    con = engine.connect()
    con = con.engine.raw_connection()
    test_connection('sqlalchemy mssql+pyodbc', con, row_list,
                    do_enlist=True,
                    do_execute_many=True)
    con.close()

    engine = sqlalchemy.create_engine(f"mssql+pyodbc://{user}:{password}@{server}:1433/{database_name}?driver=ODBC+Driver+17+for+SQL+Server",
                                      fast_executemany=True)  # Requires sqlalchemy 1.3+ and only works with pyodbc
    con = engine.connect()
    test_connection('sqlalchemy mssql+pyodbc with fast_executemany', con, row_list,
                    do_enlist=False,
                    do_execute_many=True,
                    )
    con.close()

    engine = sqlalchemy.create_engine(
        f"mssql+pyodbc://{user}:{password}@{server}:1433/{database_name}?driver=ODBC+Driver+17+for+SQL+Server")
    con = engine.connect()
    test_connection('sqlalchemy mssql+pyodbc without fast_executemany', con, row_list,
                    do_enlist=True,
                    do_execute_many=True,
                    )
    con.close()

    engine = sqlalchemy.create_engine(
        f"mssql+pyodbc://{user}:{password}@{server}:1433/{database_name}?driver=ODBC+Driver+17+for+SQL+Server")
    con = engine.connect()
    con = con.engine.raw_connection()
    test_connection('sqlalchemy->RAW mssql+pyodbc fast_executemany', con, row_list,
                    do_enlist=False,
                    do_execute_many=True,
                    fast_executemany=True,
                    )
    con.close()

    # Requires sqlachemy 1.3 which is in BETA
    # engine = sqlalchemy.create_engine(f"mssql+pyodbc://{user}:{password}@perf_test", fast_executemany=True)
    # con = engine.connect()
    # con = con.engine.connect()
    # test_connection('sqlalchemy mssql+pyodbc fast_executemany', con, row_list)
    # con.close()

    # con = pymssql.connect(server, user, password, database_name)
    # test_connection('pymssql', con, row_list)
    # con.close()


if __name__ == '__main__':
    main()



"""
Starting test
'params' arg (<class 'list'>) can be only a tuple or a dictionary.
pymssql: 1500 to DB values_list    1   took 19.7775
pymssql: 1500 to DB values_list   10   took 2.2929
pymssql: 1500 to DB values_list   20   took 0.9240
pymssql: 1500 to DB values_list   50   took 0.4331
pymssql: 1500 to DB values_list  100   took 0.4140
pymssql: 1500 to DB values_list  250   took 0.2779
pymssql: 1500 to DB values_list  500   took 0.2873
pymssql: 1500 to DB values_list 1000   took 0.2369
pymssql: 1500 to DB single execute took 21.5789
base odbc: 1500 to DB executemany took 45.2001
base odbc: 1500 to DB values_list    1   took 21.3615
base odbc: 1500 to DB values_list   10   took 2.1795
base odbc: 1500 to DB values_list   20   took 1.1822
base odbc: 1500 to DB values_list   50   took 0.4395
base odbc: 1500 to DB values_list  100   took 0.3588
base odbc: 1500 to DB values_list  250   took 0.2687
base odbc: 1500 to DB values_list  500   took 0.2720
base odbc: 1500 to DB values_list 1000   took 0.2170
base odbc: 1500 to DB single execute took 42.9432
odbc 17: 1500 to DB executemany took 20.7880
odbc 17: 1500 to DB values_list    1   took 19.5995
odbc 17: 1500 to DB values_list   10   took 2.0096
odbc 17: 1500 to DB values_list   20   took 1.0576
odbc 17: 1500 to DB values_list   50   took 0.4468
odbc 17: 1500 to DB values_list  100   took 0.3613
odbc 17: 1500 to DB values_list  250   took 0.2437
odbc 17: 1500 to DB values_list  500   took 0.2079 
odbc 17: 1500 to DB values_list 1000   took 0.2278
odbc 17: 1500 to DB single execute took 20.1598
pyformat
sqlalchemy mssql+pymssql: 1500 to DB executemany took 17.8610
sqlalchemy mssql+pymssql: 1500 to DB values_list    1   took 56.2522
sqlalchemy mssql+pymssql: 1500 to DB values_list   10   took 7.0875
sqlalchemy mssql+pymssql: 1500 to DB values_list   20   took 3.8077
sqlalchemy mssql+pymssql: 1500 to DB values_list   50   took 1.1056
sqlalchemy mssql+pymssql: 1500 to DB values_list  100   took 0.7566
sqlalchemy mssql+pymssql: 1500 to DB values_list  250   took 0.3795
sqlalchemy mssql+pymssql: 1500 to DB values_list  500   took 0.3263
sqlalchemy mssql+pymssql: 1500 to DB values_list 1000   took 0.3408
sqlalchemy mssql+pymssql: 1500 to DB single execute took 55.0011
qmark
sqlalchemy mssql+pyodbc: 1500 to DB executemany took 19.5923
sqlalchemy mssql+pyodbc: 1500 to DB values_list    1   took 38.8268
sqlalchemy mssql+pyodbc: 1500 to DB values_list   10   took 4.1481
sqlalchemy mssql+pyodbc: 1500 to DB values_list   20   took 1.7915
sqlalchemy mssql+pyodbc: 1500 to DB values_list   50   took 0.7470
sqlalchemy mssql+pyodbc: 1500 to DB values_list  100   took 0.5410
sqlalchemy mssql+pyodbc: 1500 to DB values_list  250   took 0.3510
sqlalchemy mssql+pyodbc: 1500 to DB values_list  500   took 0.2749
sqlalchemy mssql+pyodbc: 1500 to DB values_list 1000   took 0.1730  <-- fastest
sqlalchemy mssql+pyodbc: 1500 to DB single execute took 66.8404


----------------------------------------------------------------------------------------------------

Starting test
pymssql: 15000 to DB values_list  500   took 7.1770
pymssql: 15000 to DB values_list 1000   took 9.4099
base odbc: 15000 to DB values_list  500   took 7.0049
base odbc: 15000 to DB values_list 1000   took 9.4537
odbc 17: 15000 to DB values_list  500   took 1.7342
odbc 17: 15000 to DB values_list 1000   took 1.6154                <-- fastest
sqlalchemy mssql+pymssql: 15000 to DB values_list  500   took 3.2981
sqlalchemy mssql+pymssql: 15000 to DB values_list 1000   took 2.6317
sqlalchemy mssql+pyodbc: 15000 to DB values_list  500   took 2.7706
sqlalchemy mssql+pyodbc: 15000 to DB values_list 1000   took 2.4001

----------------------------------------------------------------------------------------------------

Starting test
pymssql: 150000 to DB values_list 1000                   took 14.1320                   <-- fastest
base odbc: 150000 to DB values_list 1000                 took 15.1948
odbc 17: 150000 to DB values_list 1000                   took 14.3572                   <-- next fastest
sqlalchemy mssql+pymssql: 150000 to DB values_list 1000  took 26.8538
sqlalchemy mssql+pyodbc: 150000 to DB values_list 1000   took 23.3228

"""