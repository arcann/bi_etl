from pathlib import Path
from typing import Optional

from config_wrangler.config_templates.config_hierarchy import ConfigHierarchy


class PostgreSQLBulkLoaderConfig(ConfigHierarchy):
    temp_file_path: Optional[Path] = None
    delimiter: str = '|'
    header: bool = True
    null: str = ''
    encoding: str = 'utf-8'
