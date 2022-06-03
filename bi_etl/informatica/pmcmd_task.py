"""
Created on May 5, 2015

@author: Derek Wood
"""
from bi_etl.informatica.pmcmd import PMCMD
from bi_etl.scheduler.exceptions import ParameterError
from bi_etl.scheduler.task import ETLTask


class PMCMD_Task(ETLTask):
    """
    Runs Informatica Workflows
    """
    def init(self):
        """
        pre-load initialization.        
        """
        try:
            folder = self.get_parameter('folder')
        except ParameterError:
            ##  For testing purposes - Shouldn't get here
            self.log.error("PMCMD_Task didn't get folder parameter. Assuming test run")
            folder = 'MASTER'
            self.set_parameter('folder', folder)
            self.set_parameter('workflow', 'wf_TEST_Derek')
        
        self.cmd = PMCMD(config=self.config, folder= folder)

    def load(self):
        
        workflow = self.get_parameter('workflow')
        self.cmd.startworkflow(workflow)
        try:
            self.cmd.getworkflowdetails(workflow)
        except Exception:
            pass


if __name__ == '__main__':
    task = PMCMD_Task()
    task.set_parameter('folder', 'MASTER')
    task.set_parameter('workflow', 'wf_TEST_Derek')
    task.run(suppress_notifications= True)