"""
Created on May 5, 2015

@author: woodd
"""
from bi_etl.scheduler.task import ETLTask
from bi_etl.informatica.pmcmd import PMCMD
from bi_etl.scheduler.exceptions import ParameterError

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
            self.add_parameter('folder', folder)            
            self.add_parameter('workflow', 'wf_TEST_Derek')
        
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
    task.add_parameter('folder', 'MASTER')
    task.add_parameter('workflow', 'wf_TEST_Derek')
    task.run(no_mail = True)                