from config_wrangler.config_templates.config_hierarchy import ConfigHierarchy
from config_wrangler.config_templates.sqlalchemy_database import SQLAlchemyMetadata


class SchedulerConfig(ConfigHierarchy):
    db: SQLAlchemyMetadata = None
    host_name: str = None
    qualified_host_name: str = None
    base_ui_url: str = None
