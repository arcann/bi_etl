import gzip
import io
import shutil
import time
from datetime import datetime, date

import boto3
import botocore
import keyring
# MSQL functions Version 0.5
import sqlalchemy

from bi_etl.bi_config_parser import BIConfigParser
from bi_etl.components.csv_writer import CSVWriter, QUOTE_NONE, QUOTE_MINIMAL
from bi_etl.database.connect import Connect


def encapsulate_value(value) -> str:
    # Encapsulate the input for SQL use (add ' etc)
    if isinstance(value, str):
        value = value.replace("'", "''")
        # Percent replace is required for pyformat processed SQLs
        value = value.replace("%", "%%")
        return "'" + value + "'"
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


def timepassed(time_started, message, rows):
    print('*' * 80)
    print(f"{message} took {now() - time_started:3.4f} which is {rows / (now() - time_started):.1f} rows per second")


def print_rows(cursor):
    result = cursor.execute("SELECT count(*) as cnt from perf_test")
    if result is not None:
        for row in result:
            print(f"Rows in table = {row[0]}")
    else:
        for row in cursor:
            print(f"Rows in table = {row[0]}")
    print()


def get_cursor(con, fast_executemany=True):
    if hasattr(con, 'cursor'):
        cursor = con.cursor()
        try:
            cursor.fast_executemany = fast_executemany
            # print(f"fast_executemany on raw = {fast_executemany}")
        except AttributeError:
            pass
    else:
        cursor = con
    return cursor


def test_connection(test, con, row_list,
                    do_execute_many=True,
                    do_enlist=False,
                    enlist_sizes: list = [1, 10, 20, 50, 100, 250, 500, 1000, 2000],
                    do_singly=False,
                    do_copy=True,
                    do_copy_manifest=True,
                    do_copy_folder=True,
                    folder_partitions: int  = 3,
                    fast_executemany=True,
                    paramstyle='qmark'):
    cursor = get_cursor(con, fast_executemany=fast_executemany)

    rows = len(row_list)
    cols = 'i1,c1,c2,dt,dt2,f1,d1'
    cols_list = cols.split(',')
    col_cnt = len(cols_list)

    try:
        paramstyle = con.dialect.paramstyle
        # print(f"Using dialiect param style={paramstyle}")
    except AttributeError:
        # print(f"Using default paramstyle {paramstyle}")
        pass
    if paramstyle == 'qmark':
        insert_sql = f"INSERT INTO perf_test ({cols}) VALUES ({','.join(['?'] * col_cnt)})"
    elif paramstyle == 'pyformat':
        insert_sql = f"INSERT INTO perf_test ({cols}) VALUES ({','.join(['%s'] * col_cnt)})"
    else:
        insert_sql = f"INSERT INTO perf_test ({cols}) VALUES ({','.join(['%s'] * col_cnt)})"

    if do_copy:
        cursor.execute("TRUNCATE TABLE perf_test")
        cursor.execute("COMMIT; VACUUM perf_test; COMMIT;")
        started = now()

        filepath = 'data.csv'
        delimiter = '|'
        null = ''
        with CSVWriter(
                None,
                filepath,
                delimiter=delimiter,
                column_names=cols.split(','),
                include_header=False,
                encoding='utf-8',
                quoting=QUOTE_MINIMAL,
        ) as csv_file:
            for row in row_list:
                row = csv_file.Row(row, iteration_header=csv_file.FULL_ITERATION_HEADER)
                csv_file.insert(row)
        raw_con = con.engine.raw_connection()
        raw_cur = raw_con.cursor()

        user_id = 'AKIA6FL6UYCN67KO5XNY'
        bucket_name = 'pepfar-ap-rs-mstr-software'
        s3_folder_key = 'perf_test/data.csv'
        password = keyring.get_password('s3', user_id)
        assert password is not None, f'Password for s3 {user_id} not found in keyring'

        session = boto3.session.Session(
            aws_access_key_id=user_id,
            aws_secret_access_key=password
        )
        s3 = session.resource('s3')

        try:
            print(f"Uploading {bucket_name}' key '{s3_folder_key}' from '{filepath}'")
            s3.Bucket(bucket_name).upload_file(
                filepath,
                s3_folder_key,
            )

        except botocore.exceptions.ClientError as e:
            raise e

        s3_path = f's3://{bucket_name}/{s3_folder_key}'
        sql = f"""
            COPY perf_test FROM '{s3_path}'
                 CSV 
                 delimiter '{delimiter}'
                 null '{null}' 
                 credentials 'aws_access_key_id={user_id};aws_secret_access_key={password}'
            """
        print(sql)
        raw_cur.execute(sql)
        raw_cur.execute("COMMIT")
        timepassed(started, f'{test}: {rows} to DB COPY_FROM', rows)
        print_rows(cursor)

        # Test GZIPed file performance
        cursor.execute("TRUNCATE TABLE perf_test")
        cursor.execute("COMMIT; VACUUM perf_test; COMMIT;")
        started = now()
        gzip_filepath = 'data.gz'
        gzip_s3_file_key = 'perf_test/data.gz'

        with gzip.open(gzip_filepath, 'wb') as zip_file:
            with io.TextIOWrapper(zip_file, encoding='utf-8') as text_wrapper:
                with CSVWriter(
                        None,
                        text_wrapper,
                        delimiter=delimiter,
                        column_names=cols.split(','),
                        include_header=False,
                        encoding='utf-8',
                        escapechar='\\',
                        quoting=QUOTE_MINIMAL,
                ) as csv_file:
                    for row in row_list:
                        row = csv_file.Row(row, iteration_header=csv_file.FULL_ITERATION_HEADER)
                        csv_file.insert(row)
        try:
            bucket = s3.Bucket(bucket_name)
            print(f'Cleaning S3 folder {s3_folder_key}')
            for bucket_object in bucket.objects.filter(Prefix=gzip_s3_file_key):
                print(f'Removing {bucket_object}')
                bucket_object.delete()
            print(f"Uploading {bucket_name}' key '{gzip_s3_file_key}' from '{gzip_filepath}'")
            bucket.upload_file(
                gzip_filepath,
                gzip_s3_file_key,
            )
        except botocore.exceptions.ClientError as e:
            raise e

        s3_path = f's3://{bucket_name}/{gzip_s3_file_key}'
        sql = f"""
            COPY perf_test FROM '{s3_path}'
                 delimiter '{delimiter}'
                 CSV
                 null '{null}'
                 GZIP
                 credentials 'aws_access_key_id={user_id};aws_secret_access_key={password}'
            """
        print(sql)
        raw_cur.execute(sql)
        raw_cur.execute("COMMIT")
        raw_cur.execute("VACUUM perf_test; COMMIT;")
        timepassed(started, f'{test}: {rows} to DB COPY_FROM GZIP', rows)
        raw_cur.close()
        print_rows(cursor)

    if do_copy_manifest:
        cursor.execute("TRUNCATE TABLE perf_test")
        cursor.execute("COMMIT; VACUUM perf_test; COMMIT;")
        started = now()

        delimiter = '|'
        null = ''
        local_files = []
        writer_pool = []
        s3_files = []

        bucket_name = 'pepfar-ap-rs-mstr-software'
        s3_folder_key = 'perf_test'

        for file_number in range(folder_partitions):
            filepath = f'data_{file_number}.csv'
            local_files.append(filepath)
            writer = CSVWriter(
                None,
                filepath,
                delimiter=delimiter,
                column_names=cols.split(','),
                include_header=False,
                encoding='utf-8',
                escapechar='\\',
                quoting=QUOTE_MINIMAL,
            )
            writer_pool.append(writer)
            s3_path = f's3://{bucket_name}/{s3_folder_key}/data_{file_number}.csv'
            s3_files.append(s3_path)

        for row_number, row in enumerate(row_list):
            writer = writer_pool[row_number % folder_partitions]
            row = writer.Row(row, iteration_header=writer.FULL_ITERATION_HEADER)
            writer.insert(row)

        for writer in writer_pool:
            writer.close()

        manifest_path = 'data.manifest'
        folder_s3_path = f's3://{bucket_name}/{s3_folder_key}/data.manifest'
        with open(manifest_path, 'wt') as manifest_file:
            manifest_file.write('{"entries": [\n')
            line_delimiter = ''
            for s3_path in s3_files:
                manifest_file.write(line_delimiter)
                manifest_file.write(f'{{"url":"{s3_path}", "mandatory":true}}')
                line_delimiter = ',\n'
            manifest_file.write('\n]}\n')

        raw_con = con.engine.raw_connection()
        raw_cur = raw_con.cursor()
        user_id = 'AKIA6FL6UYCN67KO5XNY'
        password = keyring.get_password('s3', user_id)
        assert password is not None, f'Password for s3 {user_id} not found in keyring'

        session = boto3.session.Session(
            aws_access_key_id=user_id,
            aws_secret_access_key=password
        )
        s3 = session.resource('s3')

        try:
            # Upload the files
            print(f"Uploading {bucket_name}' key '{s3_folder_key}/{manifest_path}' from '{manifest_path}'")
            s3.Bucket(bucket_name).upload_file(
                manifest_path,
                f'{s3_folder_key}/{manifest_path}',
            )
            for local_path, s3_path in zip(local_files, s3_files):
                print(f"Uploading {bucket_name}' key '{s3_folder_key}/{local_path}' from '{local_path}'")
                s3.Bucket(bucket_name).upload_file(
                    local_path,
                    f'{s3_folder_key}/{local_path}',
                )

        except botocore.exceptions.ClientError as e:
            raise e

        raw_cur.execute(f"""
            COPY perf_test FROM '{folder_s3_path}'
                 CSV 
                 delimiter '{delimiter}'
                 null '{null}' 
                 credentials 'aws_access_key_id={user_id};aws_secret_access_key={password}'
                 manifest  
            """)
        raw_cur.execute("COMMIT")
        raw_cur.execute("VACUUM perf_test; COMMIT;")
        timepassed(started, f'{test}: {rows} to DB COPY_FROM using manifest with {folder_partitions} files', rows)
        raw_con.close()
        print_rows(cursor)

    if do_copy_folder:
        # Our connection is getting closed somewhere
        con = con.engine.connect()
        cursor = get_cursor(con, fast_executemany=fast_executemany)
        cursor.execute("TRUNCATE TABLE perf_test")
        cursor.execute("COMMIT; VACUUM perf_test; COMMIT;")
        started = now()

        delimiter = '|'
        null = ''
        local_files = []
        zip_pool = []
        text_wrapper_pool = []
        writer_pool = []
        s3_keys = []

        bucket_name = 'pepfar-ap-rs-mstr-software'
        s3_folder_key = 'perf_test/data_gzip_folder'
        folder_s3_path = f's3://{bucket_name}/{s3_folder_key}'

        for file_number in range(folder_partitions):
            filepath = f'data_{file_number}.csv.gz'
            local_files.append(filepath)
            zip_file = gzip.open(filepath, 'wb')
            text_wrapper = io.TextIOWrapper(zip_file, encoding='utf-8')
            writer = CSVWriter(
                    None,
                    text_wrapper,
                    delimiter=delimiter,
                    column_names=cols.split(','),
                    include_header=False,
                    encoding='utf-8',
                    escapechar='\\',
                    quoting=QUOTE_MINIMAL,
                    )
            text_wrapper_pool.append(text_wrapper)
            zip_pool.append(zip_file)
            writer_pool.append(writer)
            s3_key = f'{s3_folder_key}/data_{file_number}.csv.gz'
            s3_keys.append(s3_key)

        for row_number, row in enumerate(row_list):
            writer = writer_pool[row_number % folder_partitions]
            row = writer.Row(row, iteration_header=writer.FULL_ITERATION_HEADER)
            writer.insert(row)

        for writer in writer_pool:
            writer.close()

        for text_wrapper in text_wrapper_pool:
            text_wrapper.close()

        for zip_file in zip_pool:
            zip_file.close()

        raw_con = con.engine.raw_connection()
        raw_cur = raw_con.cursor()
        user_id = 'AKIA6FL6UYCN67KO5XNY'
        password = keyring.get_password('s3', user_id)
        assert password is not None, f'Password for s3 {user_id} not found in keyring'

        session = boto3.session.Session(
            aws_access_key_id=user_id,
            aws_secret_access_key=password
        )
        s3 = session.resource('s3')

        try:
            # Upload the files
            bucket = s3.Bucket(bucket_name)
            print(f'Cleaning S3 folder {s3_folder_key}')
            for bucket_object in bucket.objects.filter(Prefix=s3_folder_key):
                print(f'Removing {bucket_object}')
                bucket_object.delete()

            for local_path, s3_path in zip(local_files, s3_keys):
                print(f"Uploading {bucket_name}' key '{s3_path}' from '{local_path}'")
                bucket.upload_file(
                    local_path,
                    f'{s3_path}',
                )

        except botocore.exceptions.ClientError as e:
            raise e

        sql = f"""
            COPY perf_test FROM '{folder_s3_path}'
                 CSV 
                 delimiter '{delimiter}'
                 null '{null}' 
                 credentials 'aws_access_key_id={user_id};aws_secret_access_key={password}'
                 GZIP  
                 COMPUPDATE OFF 
            """
        print(sql)
        raw_cur.execute(sql)
        raw_cur.execute("COMMIT")
        cursor.execute("COMMIT; VACUUM perf_test; COMMIT;")
        timepassed(started, f'{test}: {rows} to DB COPY_FROM using folder of {folder_partitions} gziped files', rows)
        raw_con.close()
        print_rows(cursor)

    if do_execute_many:
        # Our connection is getting closed somewhere
        con = con.engine.connect()
        cursor = get_cursor(con, fast_executemany=fast_executemany)
        cursor.execute("TRUNCATE TABLE perf_test")
        cursor.execute("COMMIT; VACUUM perf_test; COMMIT;")
        started = now()

        try:
            cursor.executemany(insert_sql, row_list)
            con.commit()
            timepassed(started, f'{test}: {rows} to DB executemany', rows)
        except ValueError as e:
            print(e)
        except AttributeError:
            # sqlalchemy section
            # print("Using cursor.execute (sqlalchemy) instead of executemany (DBAPI)")
            cursor.execute(insert_sql, row_list)
            try:
                con.commit()
            except AttributeError:
                pass
            cursor.execute("COMMIT; VACUUM perf_test; COMMIT;")
            timepassed(started, f'{test}: {rows} to DB executemany sqlalchemy', rows)
        print_rows(cursor)

    if do_enlist:
        for enlist_max in enlist_sizes:
            try:
                cursor.execute("TRUNCATE TABLE perf_test")
                cursor.execute("COMMIT; VACUUM perf_test; COMMIT;")
                started = now()
                for data in values_list(row_list, enlist_max):
                    cursor.execute(f"INSERT INTO perf_test ({cols}) VALUES {data}")
                try:
                    con.commit()
                except AttributeError:
                    pass
                cursor.execute("COMMIT; VACUUM perf_test; COMMIT;")
                timepassed(started, f'{test}: {rows} to DB values_list {enlist_max:4d}  ', rows)
            except Exception as e:
                print(f'Error {e} on enlist with page size of {enlist_max}')
            print_rows(cursor)

    if do_singly:
        cursor.execute("TRUNCATE TABLE perf_test")
        cursor.execute("COMMIT; VACUUM perf_test; COMMIT;")
        started = now()
        try:
            for data in row_list:
                cursor.execute(insert_sql, data)
        except ValueError:
            for data in row_list:
                data_dict = dict(zip(cols_list, data))
                cursor.execute(f"Insert into perf_test ({cols}) Values (%(i1)s, %(c1)s, %(c2)s, %(dt)s, %(f1)s, %(d1)s)", data_dict)
        except sqlalchemy.exc.ProgrammingError:
            for data in row_list:
                cursor.execute(insert_sql, data)

        try:
            con.commit()
        except AttributeError:
            pass
        cursor.execute("COMMIT; VACUUM perf_test; COMMIT;")
        timepassed(started, f'{test}: {rows} to DB single execute', rows)
        print_rows(cursor)

    # TODO: print s.compile(compile_kwargs={"literal_binds": True})
    # https://stackoverflow.com/questions/5631078/sqlalchemy-print-the-actual-query

    cursor.close()


def main():
    server = 'analytics-etl.crezir2z6j4p.us-east-1.redshift.amazonaws.com'
    user = 'analyticsetl'
    password = keyring.get_password('BI_Cache', user)
    database_name = 'analyticsetldb'
    # charset=utf8
    # {SQL Server} - released with SQL Server 2000

    names = [
        'Derek',
        'Bob',
        'Ravi',
        'Juhi',
        'Wallace',
        'Elvis',
        'Stephanie',
        'Spanish Inquisition',
    ]

    row_list = []
    rows = 1000000
    for i in range(rows):
        dt = date(
            2017,
            (12 - i) % 12 + 1,
            i % 28 + 1,
            )
        dt2 = datetime.now()
        name = f'Hello {names[i % len(names)]}'
        if i % 25 == 0:
            name = None
        row_list.append([
            i,
            name,
            f'This is a test of chr #{i +1}: ' + chr(1 + i % 799) + ' tested',  # .encode('utf-8', errors='surrogatepass')
            dt,
            dt2,
            i/10,
            i/100,
            ]
        )

    config = BIConfigParser()
    config.read_config_ini(file_name='perf_config.ini')
    config.setup_logging()

    print("Starting test")

    # connection_str = f"DRIVER={{Amazon Redshift (x64)}};SERVER={server};UID={user};Database={database_name};PWD={password}"
    # con = pyodbc.connect(connection_str)
    # test_connection('base odbc', con, row_list,
    #                 do_enlist=True,
    #                 do_execute_many=True,
    #                 do_singly=True,
    #                 paramstyle='qmark',
    #                 )
    # con.close()
    #
    # engine = sqlalchemy.create_engine(f"redshift+psycopg2://{user}:{password}@{server}:5439/{database_name}")
    # con = engine.connect()
    # con = con.engine.raw_connection()
    # test_connection('redshift+psycopg2 do_execute_many', con, row_list,
    #                 do_enlist=False,
    #                 do_execute_many=True)
    # con.close()
    #
    # engine = sqlalchemy.create_engine(f"redshift+psycopg2://{user}:{password}@{server}:5439/{database_name}", use_batch_mode=True)
    # con = engine.connect()
    # test_connection('redshift+psycopg2 raw_connection with use_batch_mode', con, row_list,
    #                 do_enlist=True,
    #                 do_execute_many=True,
    #                 do_singly=False,
    #                 paramstyle='pyformat',
    #                 )
    # con.close()
    #
    # engine = sqlalchemy.create_engine(f"redshift+psycopg2://{user}:{password}@{server}:5439/{database_name}",
    #                                   use_batch_mode=True)
    # con = engine.connect()
    # test_connection('redshift+psycopg2 with use_batch_mode', con, row_list,
    #                 do_enlist=False,
    #                 do_execute_many=True,
    #                 do_singly=False,
    #                 paramstyle='pyformat',
    #                 )
    # con.close()
    #
    # engine = sqlalchemy.create_engine(f"redshift+psycopg2://{user}:{password}@{server}:5439/{database_name}",
    #                                   use_batch_mode=False)
    # con = engine.connect()
    # test_connection('redshift+psycopg2 with OUT use_batch_mode', con, row_list,
    #                 do_enlist=True,
    #                 do_execute_many=False,
    #                 do_singly=False,
    #                 paramstyle='pyformat',
    #                 )
    # con.close()

    # engine = Connect.get_sqlachemy_engine(config, 'perf_test')
    # con = engine.connect()
    # test_connection(f'sqlalchemy perf_test config', con, row_list,
    #                 do_enlist=True,
    #                 do_execute_many=True,
    #                 do_singly=False,
    #                 paramstyle='pyformat',
    #                 )
    # con.close()

    engine = Connect.get_sqlachemy_engine(config, 'perf_test2')
    con = engine.connect()
    test_connection(f'sqlalchemy perf_test2 config', con, row_list,
                    do_copy=True,
                    do_copy_manifest=False,
                    do_copy_folder=True,
                    folder_partitions=1,
                    do_enlist=False,
                    do_execute_many=False,
                    do_singly=False,
                    )
    # test_connection(f'sqlalchemy perf_test2 config', con, row_list,
    #                 do_copy=False,
    #                 do_copy_manifest=False,
    #                 do_copy_folder=True,
    #                 folder_partitions=3,
    #                 do_enlist=False,
    #                 do_execute_many=False,
    #                 do_singly=False,
    #                 )
    test_connection(f'sqlalchemy perf_test2 config', con, row_list,
                    do_copy=False,
                    do_copy_manifest=False,
                    do_copy_folder=True,
                    folder_partitions=6,
                    do_enlist=False,
                    do_execute_many=False,
                    do_singly=False,
                    )
    # Test INSERT methods
    # test_connection(f'sqlalchemy perf_test2 config', con, row_list[:1000],
    #                 do_copy=False,
    #                 do_copy_manifest=False,
    #                 do_copy_folder=False,
    #                 do_enlist=True,
    #                 enlist_sizes=[100, 500, 1000],
    #                 do_execute_many=True,
    #                 do_singly=False,
    #                 paramstyle='pyformat',
    #                 )
    con.close()


if __name__ == '__main__':
    main()
