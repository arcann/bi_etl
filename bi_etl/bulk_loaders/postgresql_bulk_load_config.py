from pathlib import Path
from typing import Optional

from config_wrangler.config_templates.config_hierarchy import ConfigHierarchy


class PostgreSQLBulkLoaderConfig(ConfigHierarchy):
    """
    Configuration for :class:`~bi_etl.bulk_loaders.postgresql_copy.PostgreSQLCopy`.

    Attributes
    ----------
    temp_file_path:
        Directory for the local files written before the load. The system default is used if None.
    delimiter:
        Column delimiter in the files.
    header:
        True if the files start with a header row.
    null:
        Text that represents a NULL value in the files.
    encoding:
        Character encoding of the files.
    """
    temp_file_path: Optional[Path] = None
    delimiter: str = '|'
    header: bool = True
    null: str = ''
    encoding: str = 'utf-8'
