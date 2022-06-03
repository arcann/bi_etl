"""
Created on May 5, 2015

@author: Derek Wood
"""

import errno
import logging
import os
import subprocess
import sys

from bi_etl.informatica.pm_config import PMCMDConfig


class PMCMD(object):
    """
    classdocs
    """
    CONFIG_INFORMATICA_COMMANDS = 'INFORMATICA_COMMANDS'

    def __init__(self,
                 config: PMCMDConfig,
                 folder=None,
                 parmfile=None,
                 localparamfile=None,
                 osprofile=None,
                 ):
        self.config = config
        self.log = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.f_dev_null = open(os.devnull, 'w')
        self.control_file_name = "Control_import_No_folder_rep_change.xml"
        self.setup_inf_path()
        self._folder = folder
        self._parmfile = parmfile
        self._localparamfile = localparamfile
        self._osprofile = osprofile

    def infa_home(self):
        if 'INFA_HOME' in os.environ:
            return os.environ['INFA_HOME']
        else:
            return self.config.INFA_HOME

    def setup_inf_path(self):
        userDir = os.path.expanduser('~')
        if sys.platform == 'posix':
            os.environ['PATH'] = os.path.join(userDir, 'bin') + ':' + os.path.join(self.infa_home(), 'server',
                                                                                   'bin') + ':/usr/bin'
            os.environ['LD_LIBRARY_PATH'] = os.path.join(self.infa_home(), 'server', 'bin')
        if 'INFA_DOMAINS_FILE' not in os.environ or os.environ['INFA_DOMAINS_FILE'] is None:
            if self.config.INFA_DOMAINS_FILE is None:
                raise ValueError(f"INFA_DOMAINS_FILE required in environemnt varialble or config file.")
            else:
                # noinspection PyTypeChecker
                os.environ['INFA_DOMAINS_FILE'] = self.config.INFA_DOMAINS_FILE

    def informatica_bin_dir(self):
        return os.path.join(self.infa_home(), 'server', 'bin')

    def informatica_pmcmd(self):
        return os.path.join(self.informatica_bin_dir(), 'pmcmd')

    def usersecuritydomain(self):
        return self.config.USER_SECURITY_DOMAIN

    def user_id(self):
        return self.config.user_id

    def password(self):
        return self.config.get_password()

    def set_password_in_env(self):
        os.environ['INFA_PM_PASSWORD'] = self.password()

    def repository(self):
        return self.config.REPOSITORY

    def service(self):
        return self.config.SERVICE

    def domain(self):
        return self.config.DOMAIN

    def folder(self):
        if self._folder is None:
            self._folder = self.config.DEFAULT_FOLDER
        return self._folder

    def parmfile(self):
        if self._parmfile is None:
            self._parmfile = self.config.DEFAULT_PARMFILE
        return self._parmfile

    def localparamfile(self):
        if self._localparamfile is None:
            self._localparamfile = self.config.DEFAULT_LOCALPARAMFILE
        return self._localparamfile

    def osprofile(self):
        if self._osprofile is None:
            self._osprofile = self.config.OSPROFILE
        return self._osprofile

    def run_via_cmd(self):
        return self.config.RUN_VIA_CMD

    def startworkflow(self, workflow, runinsname=None, ):
        """
        runinsname is an optional instance name for this run
        """
        cmd = []
        if sys.platform == 'win32' and self.run_via_cmd():
            cmd.append('cmd')
            cmd.append('/C')
        cmd.append(self.informatica_pmcmd())
        cmd.append('startworkflow')
        cmd.append('-service')
        cmd.append(self.service())
        cmd.append('-d')
        cmd.append(self.domain())
        usersecuritydomain = self.usersecuritydomain()
        if usersecuritydomain:
            cmd.append('-usersecuritydomain')
            cmd.append(usersecuritydomain)
        cmd.append('-u')
        cmd.append(self.user_id())
        cmd.append('-passwordvar')
        self.set_password_in_env()
        cmd.append('INFA_PM_PASSWORD')  # Informatica will read environment variable
        cmd.append('-f')
        cmd.append(self.folder())
        parmfile = self.parmfile()
        if parmfile:
            cmd.append('-paramfile')
            cmd.append(parmfile)
        localparamfile = self.localparamfile()
        if localparamfile:
            cmd.append('-localparamfile')
            cmd.append(localparamfile)
        osprofile = self.osprofile()
        if osprofile:
            cmd.append('-osprofile')
            cmd.append(osprofile)
        if runinsname:
            cmd.append('-runinsname')
            cmd.append(runinsname)
        cmd.append('-wait')
        cmd.append(workflow)

        self.log.debug(" ".join(cmd))

        self.log.info("Executing pmcmd startworkflow")
        while True:
            try:
                messages = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
                self.log.info(messages)
                break  # exit while True loop

                # TODO: Parse the run id from the line below that comes in stdout and return it.
                # Workflow wf_TEST_Derek with run instance name [] and run id [113759] started successfully.

            # TODO: python 3.3+ catch InterruptedError
            # See https://www.python.org/dev/peps/pep-0475/
            except IOError as e:
                if e.errno != errno.EINTR:
                    raise e
                # Else loop
            except subprocess.CalledProcessError as e:
                self.log.error("Error code " + str(e.returncode))
                self.log.error("From " + ' '.join(e.cmd))
                self.log.error(e.output)
                raise e

    def getworkflowdetails(self, workflow, workflow_run_id=None, runinsname=None, ):
        cmd = []
        if sys.platform == 'win32' and self.run_via_cmd():
            cmd.append('cmd')
            cmd.append('/C')
        cmd.append(self.informatica_pmcmd())
        cmd.append('getworkflowdetails')
        cmd.append('-service')
        cmd.append(self.service())
        cmd.append('-d')
        cmd.append(self.domain())
        usersecuritydomain = self.usersecuritydomain()
        if usersecuritydomain:
            cmd.append('-usersecuritydomain')
            cmd.append(usersecuritydomain)
        cmd.append('-u')
        cmd.append(self.user_id())
        cmd.append('-passwordvar')
        self.set_password_in_env()
        cmd.append('INFA_PM_PASSWORD')  # Informatica will read environment variable
        cmd.append('-f')
        cmd.append(self.folder())
        if runinsname:
            cmd.append('-runinsname')
            cmd.append(runinsname)
        if workflow_run_id:
            cmd.append('-wfrunid')
            cmd.append(workflow_run_id)
        cmd.append(workflow)

        self.log.debug(" ".join(cmd))

        self.log.info("Executing pmcmd getworkflowdetails")
        try:
            messages = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            self.log.info(messages)
        except subprocess.CalledProcessError as e:
            self.log.error("Error code " + str(e.returncode))
            self.log.error("From " + ' '.join(e.cmd))
            self.log.error(e.output)
            raise e


if __name__ == '__main__':
    test_config = PMCMDConfig()
    pcmd = PMCMD(folder='MASTER', config=test_config)
    test_workflow = 'Invalid_Name'
    pcmd.startworkflow(test_workflow)
    pcmd.getworkflowdetails(test_workflow)
