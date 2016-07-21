'''
Created on Sep 17, 2014

@author: woodd
'''
from bi_etl.components.etlcomponent import ETLComponent

class SQLQuery(ETLComponent):
    """
    A class for reading an arbitrary SQL statement.
    Consider using sqlalchemy.sql.text to wrap the SQL.
    http://docs.sqlalchemy.org/en/latest/core/tutorial.html#using-text
    
    
    """
    def __init__(self,
                 task,
                 database,
                 sql,
                 logical_name = None,
                 **kwargs
                 ):
        ## Don't pass kwargs up. They should be set here at the end
        super(SQLQuery, self).__init__(task=task,
                                       logical_name= logical_name
                                       )
        
        self.engine = database.bind
        self.sql = sql
        
        ## Should be the last call of every init            
        self.set_kwattrs(**kwargs) 

    def __repr__(self):
        return "SQLQuery({})".format( self.logical_name or id(self))
    
    def __str__(self):
        return repr(self)

    def __iter__(self):
        """
        Run the SQL as is with no parameters or substitutions.
        """
        return self.run_parameters()
    
    def _obtain_column_names(self):
        ##warnings.warn("{self}.column_names can be slow to obtain".format(self=repr(self)))
        ## We might even error out if the query requires parameters
        raise NotImplementedError()
        

    def run_parameters(self, **parameters):
        """
        Run the SQL providing optional bind parameters. (:param in the SQL)
        """
        stats = self.get_stats_entry(stats_id=self.default_stats_id)
        stats.timer.start()
        selectResult = self.engine.execute(self.sql, **parameters)
        return self.iter_result(selectResult, parent_stats= stats)

    def run_substitute(self, *args, **kwargs):
        """
        Uses Python string formatting like {} or {name} to build a SQL string.
        Can be used to dynamically change the structure of the SQL, compared to bind variables which are more limited but faster.
        """
        stats = self.get_stats_entry(stats_id=self.default_stats_id)
        stats.timer.start()
        select = self.sql.format(*args, **kwargs)
        selectResult = self.engine.execute(select)
        return self.iter_result(selectResult, parent_stats= stats)

    