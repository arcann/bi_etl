from pathlib import Path
from typing import Optional

from config_wrangler.config_templates.aws.s3_bucket import S3_Bucket_Folder


# noinspection PyPep8Naming
class S3_Bulk_Loader_Config(S3_Bucket_Folder):
    temp_file_path: Optional[Path] = None
    s3_files_to_generate: Optional[int] = None
    s3_file_max_rows: Optional[int] = None
    s3_clear_before: Optional[bool] = True
    s3_clear_when_done: Optional[bool] = True
    analyze_compression: Optional[str] = None  # Current Redshift options PRESET, ON, OFF (or TRUE, FALSE for the latter options)

    def validate_files(self):
        if self.s3_file_max_rows is not None and self.s3_files_to_generate is not None:
            raise ValueError(f"S3_Bulk_Loader_Config can not have both s3_file_max_rows and s3_files_to_generate")

        elif self.s3_file_max_rows is None and self.s3_files_to_generate is None:
            raise ValueError(
                f"S3_Bulk_Loader_Config needs either s3_file_max_rows or s3_files_to_generate set (not both)"
            )
