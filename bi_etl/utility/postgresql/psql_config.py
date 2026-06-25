from config_wrangler.config_templates.config_hierarchy import ConfigHierarchy
from config_wrangler.config_types.path_types import ExecutablePath


class PSQL_Config(ConfigHierarchy):
    psql_path: ExecutablePath = 'psql'
