from pathlib import Path
from typing import Union

import psycopg2
from psycopg2 import extensions
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError


def get_conn(
        dbname,
        username,
        password,
        encoding='UTF-8',
):
    conn: extensions.connection = psycopg2.connect(database=dbname, user=username, password=password)
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


def psycopg2_extract_using_engine(
        engine: Engine,
        table_or_query: str,
        output_file_path: Union[str, Path],
        delimiter: str = '|',
        csv_mode: bool = True,
        header: bool = True,
        null: str = '',
        encoding='UTF-8',
):
    """

    Parameters
    ----------
    engine
    table_or_query:
        table_name [ ( column_name [, ...] )
        or (SQL Query)
        For table based, column names are optional.
        For SQL query based, note that parentheses and quotes are required around the query.
    output_file_path
    delimiter
    csv_mode
    header
    null
    encoding

    Returns
    -------

    """
    # noinspection PyTypeChecker
    conn: extensions.connection = engine.raw_connection()
    conn.set_client_encoding(encoding)
    cur = conn.cursor()
    if csv_mode:
        if header:
            header_cmd = 'HEADER'
        else:
            header_cmd = ''
        copy_stmt = f"COPY {table_or_query} TO STDOUT WITH CSV {header_cmd} DELIMITER '{delimiter}' NULL '{null}'"
    else:
        copy_stmt = f"COPY {table_or_query} TO STDOUT WITH DELIMITER '{delimiter}' NULL '{null}'"
    with open(output_file_path, 'wt', encoding=encoding, newline='\n') as output_file:
        cur.copy_expert(copy_stmt, output_file)
        # cur.copy_to(output_file, table_or_query, sep=delimiter, null=null)
    conn.close()


def psycopg2_import_using_cursor(
        cursor,
        table_spec: str,
        input_file_path: Union[str, Path],
        block_size: int = 4096,
        delimiter: str = '|',
        csv_mode: bool = True,
        header: bool = True,
        null: str = '',
        encoding='UTF-8',
):
    """

    Parameters
    ----------
    cursor
    table_spec:
        table_name [ ( column_name [, ...] )
        Column names are optional unless the columns in the file do not match the order or set of columns
        in the table.
    input_file_path
    block_size
    delimiter
    csv_mode
    header
    null
    encoding
    """
    if csv_mode:
        format_str = 'csv'
    else:
        format_str = 'text'

    if header:
        if csv_mode:
            header_str = 'HEADER'
        else:
            raise ValueError("Header option is allowed only when using CSV format.")
    else:
        header_str = ''

    copy_stmt = f"""
        COPY "{table_spec}" FROM STDIN
        WITH  {format_str}
        DELIMITER '{delimiter}'
        NULL '{null}'
        {header_str}  
        """
    try:
        with open(input_file_path, 'rt', encoding=encoding, newline='\n') as input_file:
            results = cursor.copy_expert(copy_stmt, input_file, size=block_size)
            # if header:
            #     input_file.readline()
            # results = cursor.copy_from(
            #     file=input_file,
            #     table=table_spec,
            #     sep=delimiter,
            #     null=null,
            # )
        return results
    except Exception as e:
        raise DBAPIError(
            statement=copy_stmt,
            params=None,
            orig=e,
        )


def psycopg2_import_using_engine(
        engine: Engine,
        table_spec: str,
        input_file_path: Union[str, Path],
        block_size: int = 4096,
        delimiter: str = '|',
        csv_mode: bool = True,
        header: bool = True,
        null: str = '',
        encoding='UTF-8',
):
    """

    Parameters
    ----------
    engine
    table_spec:
        table_name [ ( column_name [, ...] )
        Column names are optional unless the columns in the file do not match the order or set of columns
        in the table.
    input_file_path
    block_size
    delimiter
    csv_mode
    header
    null
    encoding
    """
    # noinspection PyTypeChecker
    conn: extensions.connection = engine.raw_connection()
    conn.set_client_encoding(encoding)
    cursor = conn.cursor()
    results = psycopg2_import_using_cursor(
        cursor=cursor,
        table_spec=table_spec,
        input_file_path=input_file_path,
        block_size=block_size,
        delimiter=delimiter,
        csv_mode=csv_mode,
        header=header,
        null=null,
        encoding=encoding,
    )
    conn.close()
    return results
