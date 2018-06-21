import subprocess
import time
from configparser import ConfigParser

from bi_etl.bi_config_parser import BIConfigParser

import logging

log = logging.getLogger('etl.utils.ssh_forward')


def ssh_forward(host: str, user: str, server_port: int, local_port: int=None, wait: bool=False, ssh_path=None):
    # Command line options documentation
    # https://man.openbsd.org/ssh
    if ssh_path is None:
        ssh_path = 'ssh'
    if local_port is None:
        local_port = server_port
    cmd = [
        ssh_path,
        '{user}@{host}'.format(user=user, host=host),
        '-L', '127.0.0.1:{local_port}:localhost:{server_port}'.format(
            local_port=local_port,
            server_port=server_port,
        ),
        '-o', 'ExitOnForwardFailure=yes',
        '-o', 'StrictHostKeyChecking=no',
        # Sleep 10 will give 10 seconds to connect before it shuts down.
        # It will not exit while the forward port is in use.
        # If this is the second forward to run it will exit after 10 seconds since it won't have
        # an active forward.
        'sleep 10',
    ]
    log.debug("Starting ssh")
    log.debug(cmd)
    try:
        if wait:
            stdout = subprocess.PIPE
            stderr = subprocess.PIPE
        else:
            stdout = subprocess.DEVNULL
            stderr = subprocess.DEVNULL
        p = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, universal_newlines=True)
        log.info("Started ssh as ppid {}".format(p.pid))
        if wait:
            outs, errs = p.communicate()
        else:
            time.sleep(0.25)
            outs = None
            errs = None
        rc = p.poll()
        if rc is not None:
            if rc != 0:
                if outs:
                    log.info(outs)
                if errs:
                    log.error(errs)
                log.error("ssh return code = {}".format(rc))
        else:
            log.info("ssh tunnel running OK")

    except subprocess.CalledProcessError as e:
        log.error(e.stdout)
        log.error(e.stderr)
        raise e


def ssh_forward_using_config(config: ConfigParser, section='ssh', wait=False):
    host = config[section]['host']
    user = config[section]['user']
    server_port = config[section]['server_port']
    local_port = config[section].get('local_port', fallback=None)
    ssh_path = config[section].get('ssh_path', fallback=None)
    ssh_forward(
        host=host,
        user=user,
        local_port=local_port,
        server_port=server_port,
        wait=wait,
        ssh_path=ssh_path,
    )


if __name__ == '__main__':
    config = BIConfigParser()
    config.read_config_ini()
    ssh_forward_using_config(config, wait=True)
