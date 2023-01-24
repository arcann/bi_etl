import logging
import os
import subprocess
import tempfile
from pprint import pformat

log = logging.getLogger('etl.utils.psql_command')


def generate_extract_sql(table_name, sql_file_path, output_file_path, delimiter='\\013', null='', encoding='UTF-8'):
    with open(sql_file_path, "wt") as f:
        f.write("\copy {table_name} to '{output_file_path}' with delimiter E'{delimiter}' NULL '{null}' ENCODING '{encoding}';".format(
            table_name=table_name,
            output_file_path=output_file_path,
            delimiter=delimiter,
            null=null,
            encoding=encoding,
        ))

    """  Commands to re-encode content as UTF-16
    powershell -c "Get-Content -Encoding utf8  -TotalCount 1 .\output.txt | Set-Content -Encoding Unicode output-utf16le.txt
    powershell -c "Get-Content -Encoding utf8 .\output.txt | Add-Content -Encoding Unicode output-utf16le.txt
    """


def psql(config, dbname, username, password, sql_file_path):
    cmd = [config.get('psql', 'path', fallback='psql'),
           '--dbname', dbname,
           '--username', username,
           # Password must be set in %APPDATA%\postgresql\pgpass.conf
           # For example C:\Users\__developer__\AppData\Roaming\postgresql\pgpass.conf
           '--file', sql_file_path,
           ]
    log.debug([x for x in cmd])
    messages = list()

    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # while p.poll() is None:
        #     # TODO: Use pexpect instead?  bcp output to the PIPE is buffered when using this method.
        #     line = p.stdout.readline()
        #     if line != b'':
        #         line = line.strip()
        #         messages.append(line)
        #         self.log.info(line)
        # self.log.info('--psql exit--')
        # for line in p.stdout.readlines():
        #     if line != b'':
        #         line = line.strip()
        #         messages.append(line)
        #         self.log.info(line)
        outs, errs = p.communicate(input=password + "\n")
        # outs, errs = p.communicate()
        rc = p.returncode
        if rc != 0:
            log.error('psql returned code {}'.format(rc))
            log.error('psql returned message {}'.format(outs))
            log.error('psql returned message {}'.format(errs))
            raise RuntimeError('psql execution error')
        else:
            log.debug('psql returned message {}'.format(outs))
            log.debug('psql returned error {}'.format(errs))
            if outs.startswith(b'COPY '):
                rows = int(outs[5:])
                log.debug("Rows message found rows = {}".format(rows))
                return rows
            else:
                log.error('psql returned message {}'.format(outs))
                log.error('psql returned error {}'.format(errs))
                raise ValueError("psql output did not contain COPY rows")
    except subprocess.CalledProcessError as e:
        log.error("Error code " + str(e.returncode))
        log.error('BCP messages:')
        log.error(pformat(messages))
        log.error('BCP output:')
        log.error(e.output)
        log.error('-' * 80)
        raise RuntimeError("psql error code " + str(e.returncode))


def psql_extract(self, dbname, username, password, table_name, output_file_path, delimiter='\\013', null='', encoding='UTF-8'):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        sql_file_path = os.path.join(temp_dir, 'extract.sql')
        self.generate_extract_sql(table_name, sql_file_path, output_file_path, delimiter, null, encoding)
        self.psql(dbname, username, password, sql_file_path)