from pathlib import Path
from typing import Optional

from config_wrangler.config_templates.aws.s3_bucket import S3_Bucket_Folder


class S3_Bulk_Loader_Config(S3_Bucket_Folder):
    class Config:
        validate_all = True
        validate_assignment = True
        allow_mutation = True

    temp_file_path: Optional[Path] = None
    s3_files_to_generate: int = None
    s3_file_max_rows: int = None
    s3_clear_before: bool = True
    s3_clear_when_done: bool = True
    analyze_compression: str = None  # Current Redshift options PRESET, ON, OFF (or TRUE, FALSE for the latter options)

    def validate_files(self):
        if self.s3_file_max_rows is not None and self.s3_files_to_generate is not None:
            raise ValueError(f"S3_Bulk_Loader_Config can not have both s3_file_max_rows and s3_files_to_generate")

        elif self.s3_file_max_rows is None and self.s3_files_to_generate is None:
            raise ValueError(
                f"S3_Bulk_Loader_Config needs either s3_file_max_rows or s3_files_to_generate set (not both)"
            )
