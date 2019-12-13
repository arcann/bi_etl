import psycopg2


def get_conn(
        dbname,
        username,
        password,
        encoding='UTF-8',
        ):
    conn = psycopg2.connect(database=dbname, user=username, password=password)
    conn.set_client_encoding(encoding)
    return conn


def get_cursor(
        dbname,
        username,
        password,
        encoding='UTF-8',
        ):
    conn = get_conn(
        dbname=dbname,
        username=username,
        password=password,
        encoding=encoding
        )
    cur = conn.cursor()
    return cur


def psycopg2_extract_using_bind(
        bind,
        table_name: str,
        output_file_path: str,
        delimiter: str = '|',
        csv_mode: bool = True,
        header: bool = True,
        null: str = '',
        encoding='UTF-8',
    ):
    conn = bind.engine.raw_connection()
    conn.set_client_encoding(encoding)
    cur = conn.cursor()
    if csv_mode:
        if header:
            header_cmd = 'HEADER'
        else:
            header_cmd = ''
        copy_stmt = f"COPY {table_name} TO STDOUT WITH CSV {header_cmd} DELIMITER '{delimiter}' NULL '{null}'"
    else:
        copy_stmt = f"COPY {table_name} TO STDOUT WITH DELIMITER '{delimiter}' NULL '{null}'"
    with open(output_file_path, 'wt', encoding=encoding, newline='\n') as output_file:
        cur.copy_expert(copy_stmt, output_file)
        # cur.copy_to(output_file, table_name, sep=delimiter, null=null)
    conn.close()


def psycopg2_sql_extract(
        bind,
        sql: str,
        output_file_path: str,
        delimiter: str = '|',
        csv_mode: bool = True,
        header: bool = True,
        null: str = '',
        encoding='UTF-8'):
    conn = bind.engine.raw_connection()
    conn.set_client_encoding(encoding)
    cur = conn.cursor()

    if csv_mode:
        if header:
            header_cmd = 'HEADER'
        else:
            header_cmd = ''
        copy_stmt = f"COPY ({sql}) TO STDOUT WITH CSV {header_cmd} DELIMITER '{delimiter}' NULL '{null}'"
    else:
        copy_stmt = f"COPY ({sql}) TO STDOUT WITH DELIMITER '{delimiter}' NULL '{null}'"

    with open(output_file_path, 'wt', encoding=encoding, newline='\n') as output_file:
        cur.copy_expert(copy_stmt, output_file)
