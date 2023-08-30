import logging
import os
import subprocess
import tempfile
import textwrap
from datetime import date, datetime
from pprint import pformat

from config_wrangler.config_templates.config_hierarchy import ConfigHierarchy
from config_wrangler.config_types.path_types import ExecutablePath
from sqlalchemy.dialects.mssql import BIT

from bi_etl.components.table import Table

log = logging.getLogger('etl.utils.bcp_helpers')


class BCPError(Exception):
    pass


class BCP_Config(ConfigHierarchy):
    path_to_bcp_exectable: ExecutablePath = 'bcp'
    batch_size: int = 10000


def create_bcp_format_file(table: Table, bcp_format_path, encoding=None, delimiter=None, row_terminator=None):
    with open(bcp_format_path, "w", encoding="utf-8") as bcp_fmt:
        field_list = list()
        column_list = list()
        max_col = len(table.columns)
        if delimiter is None:
            if encoding == 'utf_16_le':
                delimiter = '|\\0'
            else:
                delimiter = '|'
        for col_num, column in enumerate(table.columns):
            size = None
            scale = None

            c_type = column.type
            try:
                p_type = c_type.python_type
            except NotImplementedError:
                if isinstance(c_type, BIT):
                    p_type = bool
                else:
                    raise ValueError(f"Unexpected data type {c_type} for column")

            # Types
            # https://docs.microsoft.com/en-us/sql/relational-databases/import-export/xml-format-files-sql-server?view=sql-server-2017
            # https://msdn.microsoft.com/en-us/library/ff718877(v=sql.105).aspx

            if p_type == int:
                size = 24
            elif p_type == bool:
                size = 1
            elif p_type == datetime:
                size = 48
            elif p_type == date:
                size = 22
            elif p_type == str:
                if c_type.length is not None:
                    if encoding == 'utf_16_le':
                        size = c_type.length * 2
                    else:
                        size = c_type.length
                    if size > 2 ** 15:
                        size = None

            if col_num + 1 == max_col:
                if row_terminator is None:
                    if encoding == 'utf_16_le':
                        delimiter = "\\r\\0\\n\\0"
                    else:
                        delimiter = "\\r\\n"
                else:
                    delimiter = row_terminator
            if encoding == 'utf_16_le':
                field_type = 'NCharTerm'
            else:
                field_type = 'CharTerm'
            field_spec = f'<FIELD ID="{col_num + 1}" xsi:type="{field_type}" COLLATION="" TERMINATOR="{delimiter}"'
            if size is not None:
                field_spec += f' MAX_LENGTH="{size}"'
            if scale is not None:
                field_spec += f' SCALE="{scale}"'
            field_spec += "/>"
            field_list.append(field_spec)
            column_list.append(
                f'<COLUMN SOURCE="{col_num + 1}" NAME="{column.name}" />'
            )
        bcp_fmt.write(textwrap.dedent("""\
                        <?xml version="1.0"?>
                        <BCPFORMAT xmlns="http://schemas.microsoft.com/sqlserver/2004/bulkload/format" 
                                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                        <RECORD>
                        """))
        bcp_fmt.write('\n'.join(field_list))
        bcp_fmt.write(textwrap.dedent("""\n</RECORD>\n<ROW>"""))
        bcp_fmt.write('\n'.join(column_list))
        bcp_fmt.write(textwrap.dedent("""\n</ROW>\n</BCPFORMAT>"""))


def run_bcp(
        config: BCP_Config,
        table_name: str,
        file_path: str,
        database_bind,
        format_file_path=None,
        direction='in',
        delimiter='^K',
        temp_dir=None,
        start_line=1,
        encoding=None,
        ):
    if temp_dir is None:
        cleanup_temp = True
        temp_dir_obj = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        temp_dir = temp_dir_obj.name
    else:
        temp_dir_obj = None
        cleanup_temp = False

    bcp_errors = os.path.join(temp_dir, "bcp.errors")

    if encoding == 'utf_16_le':
        char_encoding = 'UTF-16'
    else:
        # char_encoding = 'UTF-8'
        char_encoding = '65001'

    cmd = [config.path_to_bcp_exectable,
           table_name,
           # in / out
           direction,
           file_path,
           '-S', database_bind.url.host,
           '-d', database_bind.url.database,
           '-U', database_bind.url.username,
           '-P', database_bind.url.password,
           # Max errors
           # '-m', '1000',
           # '-o', bcp_output,
           '-e', bcp_errors,
           # Batch size
           '-b', str(config.batch_size),
           # encoding eg UTF-8
           '-C', char_encoding,
           # hints
           # '-h', 'CHECK_CONSTRAINTS,TABLOCK',
           # '-h', 'CHECK_CONSTRAINTS',
           # packet size = Max
           # '-a', '65535'
           ]

    # Specify start line defaults to 1 in params
    if start_line > 1:
        cmd.extend(['-F', str(start_line)])

    if format_file_path:
        cmd.extend(['-f', format_file_path])
    else:
        # UTF Mode
        if encoding == 'utf_16_le':
            cmd.extend(['-w'])
        else:
            cmd.extend(['-c'])
        cmd.extend(['-t', delimiter])

    log.debug(" ".join(cmd).replace(database_bind.url.password, '****'))
    messages = list()

    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1, stderr=subprocess.STDOUT)
        # this did not work
        # try:
        #     outs, _ = p.communicate(input=database_bind.url.password, timeout=1)
        #     for line in outs.spltlines:
        #         if line != b'':
        #             line = line.strip()
        #             messages.append(line)
        #             log.info(line)
        # except subprocess.TimeoutExpired:
        #     pass
        while p.poll() is None:

            line = p.stdout.readline()
            if line != b'':
                line = line.strip()
                messages.append(line)
                log.info(line)
        for line in p.stdout.readlines():
            if line != b'':
                line = line.strip()
                messages.append(line)
                log.info(line)
        p.stdout.close()
        rc = p.returncode
        if rc != 0:
            log.error(f'bcp returned code {rc}')
        with open(bcp_errors, 'r', encoding='utf-8', errors='skip') as bcp_error_file:
            error_messages = bcp_error_file.read()
        if len(error_messages) > 0:
            if rc == 0:
                rc = 1
                log.error("Errors with rc = 0. Setting rc = 1")
            log.error('-' * 80)
            log.error('BCP error detail:')
            log.error(error_messages)
            log.error('-' * 80)

        if rc == 0:
            log.debug('BCP output parsing:')
            rows = 0
            for line in messages:
                line = line.strip()
                if line.endswith(b' rows copied.'):
                    rows = int(line[:-13])
                    log.debug(f"Rows message found rows = {rows}")
                    break
            return rows
        else:
            raise BCPError('bcp error')

    except IOError as e:
        raise e
    except subprocess.CalledProcessError as e:
        log.error("Error code " + str(e.returncode))
        log.error('BCP messages:')
        log.error(pformat(messages))
        log.error('BCP output:')
        log.error(e.output)
        log.error('-' * 80)
        with open(bcp_errors, 'r') as bcp_error_file:
            error_messages = bcp_error_file.read()
        log.error('BCP raw errors:')
        log.error(error_messages)
        log.error('-' * 80)
        raise BCPError("BCP Error code " + str(e.returncode))
    finally:
        if cleanup_temp:
            temp_dir_obj.cleanup()


def format_value_for_bcp(value):
    if isinstance(value, datetime):
        # noinspection PyTypeChecker,PyTypeChecker
        return (
            f'{value.year:4d}-{value.month:02d}-{value.day:02d} '
            f'{value.hour:02d}:{value.minute:02d}:{value.second + value.microsecond / 1000000:06.3f}'
            )
    elif value is None:
        return ''
    else:
        return str(value).replace('|', '/')
