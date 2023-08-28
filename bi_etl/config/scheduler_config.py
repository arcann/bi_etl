from config_wrangler.config_templates.config_hierarchy import ConfigHierarchy
from config_wrangler.config_templates.sqlalchemy_database import SQLAlchemyMetadata
from config_wrangler.config_wrangler_config import ConfigWranglerConfig


class SchedulerConfig(ConfigHierarchy):
    model_config = ConfigWranglerConfig(
        validate_credentials=True,
        validate_default=False,  # All defaults are None
    )

    db: SQLAlchemyMetadata = None
    host_name: str = None
    qualified_host_name: str = None
    base_ui_url: str = None
