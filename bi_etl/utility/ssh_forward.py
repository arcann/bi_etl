import logging
import random
import subprocess
import time
from pathlib import Path
from typing import Optional, Union

from config_wrangler.config_templates.config_hierarchy import ConfigHierarchy
from config_wrangler.config_types.path_types import ExecutablePath

log = logging.getLogger('etl.utils.ssh_forward')


def ssh_run_command(
        host: str,
        user: str,
        command: str,
        ssh_path: Optional[Union[str, Path]] = None,
        ) -> str:
    # Command line options documentation
    # https://man.openbsd.org/ssh
    if ssh_path is None:
        ssh_path = 'ssh'
    cmd = [
        ssh_path,
        f'{user}@{host}',
        command,
    ]
    log.debug("Starting ssh")
    log.debug(' '.join(cmd))
    try:
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE
        log.debug(f"Running {' '.join(cmd)}")
        p = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, universal_newlines=True)
        log.info(f"Started ssh as ppid {p.pid}")
        outs, errs = p.communicate()
        rc = p.poll()
        if rc is not None:
            if rc != 0:
                if outs:
                    log.info(outs)
                if errs:
                    log.error(errs)
                log.error(f"ssh return code = {rc}")
        return outs

    except subprocess.CalledProcessError as e:
        log.error(e.stdout)
        log.error(e.stderr)
        raise e


class SSH_Config(ConfigHierarchy):
    host: str
    user_id: str
    ssh_path: ExecutablePath = None


def ssh_run_command_using_config(config: SSH_Config, command: str) -> str:
    return ssh_run_command(
        host=config.host,
        user=config.user_id,
        ssh_path=config.ssh_path,
        command=command,
    )


def ssh_forward(
        host: str,
        user: str,
        server: str,
        server_port: int,
        local_port: int = None,
        wait: bool = False,
        ssh_path: Optional[Union[str, Path]] = None,
        seconds_wait_for_usage: int = 60):
    # Command line options documentation
    # https://man.openbsd.org/ssh
    if ssh_path is None:
        ssh_path = 'ssh'
    if local_port is None:
        local_port = random.randrange(10000, 60000)
    cmd = [
        ssh_path,
        f'{user}@{host}',
        '-L', f'127.0.0.1:{local_port}:{server}:{server_port}',
        '-o', 'ExitOnForwardFailure=yes',
        '-o', 'StrictHostKeyChecking=no',
        # Sleep 10 will give 10 seconds to connect before it shuts down.
        # It will not exit while the forward port is in use.
        # If this is the second forward to run it will exit after 10 seconds since it won't have
        # an active forward.
        'sleep', str(seconds_wait_for_usage),
    ]
    log.info(f'Starting ssh to {host}:{server_port}')
    log.debug(' '.join(cmd))
    try:
        if wait:
            stdout = subprocess.PIPE
            stderr = subprocess.PIPE
        else:
            stdout = subprocess.DEVNULL
            stderr = subprocess.DEVNULL
        p = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, universal_newlines=True)
        log.info(f"Started ssh as ppid {p.pid}")
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
                log.error(f"ssh return code = {rc}")
        else:
            log.info(f"ssh tunnel running OK with local_port = {local_port}")

        return local_port

    except subprocess.CalledProcessError as e:
        log.error(e.stdout)
        log.error(e.stderr)
        raise e


class SSH_Forward_Config(SSH_Config):
    server: str
    server_port: int
    local_port: int
    seconds_wait_for_usage: int = 60
    seconds_wait_for_tunnel_start: int = 2


def ssh_forward_using_config(config: SSH_Forward_Config, wait=False):
    local_port = ssh_forward(
        host=config.host,
        user=config.user_id,
        local_port=config.local_port,
        server=config.server,
        server_port=config.server_port,
        ssh_path=config.ssh_path,
        seconds_wait_for_usage=config.seconds_wait_for_usage,
        wait=wait,
    )
    if config.seconds_wait_for_tunnel_start:
        time.sleep(config.seconds_wait_for_tunnel_start)

    return local_port
