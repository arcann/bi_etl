import logging

from sqlalchemy import Column
from sqlalchemy import event
from sqlalchemy import exc
from sqlalchemy.dialects.oracle.base import NCLOB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.pool import Pool
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.schema import MetaData
from sqlalchemy.sql.schema import Sequence
from sqlalchemy.sql.sqltypes import BLOB
from sqlalchemy.sql.sqltypes import Unicode
from sqlalchemy.types import DateTime
from sqlalchemy.types import INTEGER
from sqlalchemy.types import VARCHAR

from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base_From_Ini_Env
from bi_etl.scheduler.status import Status
from bi_etl.utility import dict_to_str

log = logging.getLogger(__name__)


# pylint: disable=missing-docstring, too-few-public-methods
# pylint: disable=unused-argument

@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    """
    Test connections before they are used (finds disconnected sessions)

    Parameters
    ----------
    dbapi_connection
    connection_record
    connection_proxy

    Returns
    -------

    """
    cursor = dbapi_connection.cursor()
    try:
        # Only ping connections that support it
        if hasattr(dbapi_connection, 'ping'):
            dbapi_connection.ping()
    except:
        # optional - dispose the whole pool
        # instead of invalidating one at a time
        # connection_proxy._pool.dispose()

        # raise DisconnectionError - pool will try
        # connecting again up to three times before raising.
        raise exc.DisconnectionError()
    cursor.close()


# Only use ZopeTransactionExtension on the web tier,
# on the scheduler the import will likely fail, but we don't use DBSession there
try:
    from zope.sqlalchemy import ZopeTransactionExtension  # @UnresolvedImport

    DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
except ImportError:
    ZopeTransactionExtension = None
    DBSession = None

metadata = MetaData(schema='public')
Base = declarative_base(metadata=metadata)


class ETL_Scheduler(Base):
    __tablename__ = 'etl_scheduler'
    __table_args__ = {'quote': False}
    scheduler_id = Column(INTEGER, primary_key=True)
    host_name = Column(VARCHAR(400), nullable=False)
    qualified_host_name = Column(VARCHAR(400), nullable=False)
    last_heartbeat = Column(DateTime, nullable=True)


class ETL_Tasks(Base):
    __tablename__ = 'etl_tasks'
    __table_args__ = {'quote': False}
    task_id = Column(INTEGER, Sequence('etl_task_id_seq'), primary_key=True)
    scheduler_id = Column(INTEGER, ForeignKey('etl_scheduler.scheduler_id'), nullable=False)
    scheduler = relationship('ETL_Scheduler')
    submitted_date = Column(DateTime, nullable=False, server_default=text("sysdate"))
    status_id = Column(INTEGER, ForeignKey('etl_task_status_cd.status_id'), nullable=False, )
    status_cd = relationship('ETL_Task_Status_CD', lazy="joined", )
    submit_by_user_id = Column(VARCHAR(100), nullable=True)
    pid = Column(INTEGER, nullable=True)
    modulename = Column(VARCHAR(400), nullable=False)
    classname = Column(VARCHAR(400), nullable=True)
    display_name = Column(VARCHAR(400), nullable=True)
    parent_task_id = Column(INTEGER, ForeignKey('etl_tasks.task_id'), nullable=True)
    root_task_id = Column(INTEGER, ForeignKey('etl_tasks.task_id'), nullable=True)
    children = relationship("ETL_Tasks",
                            foreign_keys=[parent_task_id],
                            backref=backref('parent_task', remote_side=[task_id])
                            )
    ancestors = relationship("ETL_Tasks",
                             foreign_keys=[root_task_id],
                             backref=backref('root_task', remote_side=[task_id])

                             )
    started_date = Column(DateTime, nullable=True)
    finished_date = Column(DateTime, nullable=True)
    summary_message = Column(Unicode(2000), nullable=True)
    parameters = relationship('ETL_Task_Params')
    log_entries = relationship('ETL_Task_Log', order_by="ETL_Task_Log.log_entry_ts")
    stats = relationship('ETL_Task_Stats',
                         collection_class=attribute_mapped_collection('stat_name'),
                         cascade="all, delete-orphan"
                         )

    def __repr__(self):
        return "ETL_Tasks({})".format(dict_to_str(self))

    def __str__(self):
        return "ETL_Tasks(task_id={})".format(self.task_id)

    @property
    def Status(self):
        if self.status_id is not None:
            return Status(self.status_id)
        else:
            return None

    @Status.setter
    def Status(self, status_object):
        try:
            self.status_id = status_object.value
        except AttributeError:
            self.status_id = int(status_object)

    @property
    def children_id_list(self):
        c_lst = [str(c.task_id) for c in self.children]
        return ','.join(c_lst)

    @staticmethod
    def get_next_task_id(session):
        # We have to query the sequence each time
        # because this code might be running on a different server or thread from others
        next_id = list(session.execute(ETL_Tasks.task_id.default))[0][0]
        return next_id

    def errors(self):
        result = list()
        for log_row in self.log_entries:
            if log_row.log_entry is not None:
                lines = str(log_row.log_entry).split('\n')
                for line in lines:
                    if line.startswith('ERROR'):
                        result.append(line)
        return result


class ETL_Task_Dependency(Base):
    __tablename__ = 'etl_task_dependency'
    __table_args__ = {'quote': False}
    task_id = Column(INTEGER, ForeignKey('etl_tasks.task_id'), primary_key=True, )
    dependent_on_task_id = Column(INTEGER, ForeignKey('etl_tasks.task_id'), primary_key=True, )
    dependent_reason = Column(VARCHAR(100), nullable=False)
    current_blocking_flag = Column(VARCHAR(1), nullable=False)

    task = relationship(ETL_Tasks,
                        foreign_keys=[task_id],
                        backref=backref("dependencies", )
                        )
    dependent_on_task = relationship(ETL_Tasks,
                                     foreign_keys=[dependent_on_task_id],
                                     backref=backref("depends_on_this", )
                                     )

    def __init__(self, task, dependent_on_task, dependent_reason):
        self.task = task
        self.dependent_on_task = dependent_on_task
        self.dependent_reason = str(dependent_reason)
        self.current_blocking_flag = 'Y'
        super().__init__()

    def __str__(self):
        return "(id={},reason={},current_blocking_flag={})".format(self.dependent_on_task, self.dependent_reason,
                                                                   self.current_blocking_flag)


class ETL_Task_Status_CD(Base):
    __tablename__ = 'etl_task_status_cd'
    __table_args__ = {'quote': False}
    status_id = Column(INTEGER, primary_key=True, )
    status_name = Column(VARCHAR(25), nullable=False)


class ETL_Task_Params(Base):
    __tablename__ = 'etl_task_params'
    __table_args__ = {'quote': False}
    task_id = Column(INTEGER, ForeignKey('etl_tasks.task_id'), primary_key=True, )
    param_name = Column(VARCHAR(400), primary_key=True)
    param_value = Column(BLOB, nullable=True)

    def __init__(self, param_name, param_value):
        self.param_name = param_name
        self.param_value = param_value
        super().__init__()


class ETL_Task_Log(Base):
    __tablename__ = 'etl_task_log'
    __table_args__ = {'quote': False}
    task_id = Column(INTEGER, ForeignKey('etl_tasks.task_id'), primary_key=True, )
    log_entry_ts = Column(DateTime, nullable=True, primary_key=True, )
    log_entry = Column(NCLOB, nullable=True, )


class ETL_Task_Stats(Base):
    __tablename__ = 'etl_task_stats'
    __table_args__ = {'quote': False}
    task_id = Column(INTEGER, ForeignKey('etl_tasks.task_id'), primary_key=True, )
    stat_name = Column(VARCHAR(400), primary_key=True)
    stat_value = Column(VARCHAR(400), nullable=True)

    def __init__(self, stat_name, stat_value):
        self.stat_name = stat_name
        self.stat_value = stat_value
        super().__init__()

    def is_row_count(self):
        return 'rows' in self.stat_name.lower()

    def is_int(self):
        try:
            int(self.stat_value)
            return True
        except ValueError:
            return False


class ETL_Class(Base):
    __tablename__ = 'etl_class'
    __table_args__ = {'quote': False}
    etl_class_id = Column(INTEGER, Sequence('etl_clas_id_seq'), primary_key=True)
    module_name = Column(VARCHAR(400), nullable=False)
    class_name = Column(VARCHAR(400), nullable=True)


class ETL_Class_Dependency(Base):
    __tablename__ = 'etl_class_dependency'
    __table_args__ = {'quote': False}
    etl_class_id = Column(INTEGER, ForeignKey('etl_class.etl_class_id'), primary_key=True, )
    dependent_on_etl_class_id = Column(INTEGER, ForeignKey('etl_class.etl_class_id'), primary_key=True, )

    etl_class = relationship(ETL_Class,
                             foreign_keys=[etl_class_id],
                             backref=backref("dependencies", )
                             )
    dependent_on_etl_task = relationship(ETL_Class,
                                         foreign_keys=[dependent_on_etl_class_id],
                                         backref=backref("depends_on_this", )
                                         )

    def __init__(self, etl_class, dependent_on_etl_task):
        self.etl_class = etl_class
        self.dependent_on_etl_task = dependent_on_etl_task
        super().__init__()


##############################################################################
if __name__ == '__main__':
    config = BI_ETL_Config_Base_From_Ini_Env()
    engine = config.bi_etl.scheduler.db.get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Model tables created")
