import psycopg2


def psycopg2_extract(dbname, username, password, table_name, output_file_path, delimiter='\013', null='',
                     encoding='UTF-8'):
    conn = psycopg2.connect(database=dbname, user=username, password=password)
    conn.set_client_encoding(encoding)
    cur = conn.cursor()
    with open(output_file_path, 'wt', encoding=encoding, newline='\n') as output_file:
        cur.copy_to(output_file, table_name, sep=delimiter, null=null)


def psycopg2_extract_using_bind(
        bind,
        table_name,
        output_file_path, delimiter='\013',
        null='',
        encoding='UTF-8'
    ):
    conn = bind.engine.raw_connection()
    conn.set_client_encoding(encoding)
    cur = conn.cursor()
    with open(output_file_path, 'wt', encoding=encoding, newline='\n') as output_file:
        cur.copy_to(output_file, table_name, sep=delimiter, null=null)
    conn.close()
