from config_wrangler.config_templates.config_hierarchy import ConfigHierarchy
from config_wrangler.config_templates.sqlalchemy_database import SQLAlchemyDatabase
from config_wrangler.config_wrangler_config import ConfigWranglerConfig


class SchedulerConfig(ConfigHierarchy):
    model_config = ConfigWranglerConfig(
        validate_credentials=True,
        validate_default=False,  # All defaults are None
    )
    db: SQLAlchemyDatabase = None
    host_name: str = None
    qualified_host_name: str = None
    base_ui_url: str = None
