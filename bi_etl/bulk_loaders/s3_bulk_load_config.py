from pathlib import Path
from typing import Optional

from config_wrangler.config_templates.aws.s3_bucket import S3_Bucket_Folder
from pydantic import field_validator


# noinspection PyPep8Naming
class S3_Bulk_Loader_Config(S3_Bucket_Folder):
    """
    Configuration for bulk loaders that stage their files in an S3 bucket folder.

    Attributes
    ----------
    temp_file_path:
        Directory for the local files written before upload. The system default is used if None.
    s3_file_max_rows:
        Maximum rows per file. Each loader uses its own default if None.
    s3_clear_before:
        If True, empty the S3 folder before uploading. If False, a non-empty folder is an error.
    s3_clear_when_done:
        If True, empty the S3 folder after the load.
    s3_clear_on_failure:
        If True, empty the S3 folder when the load fails. If False (the default) the files are left in S3
        so that they can be used to debug the failure.
    redshift_copy_iam_role:
        IAM role used by the Redshift ``COPY`` command.
    analyze_compression:
        Redshift analyze compression option: PRESET, ON, OFF (or TRUE, FALSE for the latter options).
    """
    temp_file_path: Optional[Path] = None
    s3_file_max_rows: Optional[int] = None
    s3_clear_before: Optional[bool] = True
    s3_clear_when_done: Optional[bool] = True
    s3_clear_on_failure: Optional[bool] = False
    redshift_copy_iam_role: Optional[str] = None
    # Current Redshift analyze_compression options:
    # PRESET, ON, OFF (or TRUE, FALSE for the latter options)
    analyze_compression: Optional[str] = None

    # noinspection PyNestedDecorators
    @field_validator('s3_file_max_rows')
    @classmethod
    def _val_none_or_gt_zero(cls, v):
        if v is not None and v <= 0:
            raise ValueError(f"s3_file_max_rows must be greater than zero. Got {v}")
        return v