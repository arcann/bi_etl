from config_wrangler.config_templates.s3_bucket import S3_Bucket_Folder


class S3_Bulk_Loader_Config(S3_Bucket_Folder):
    class Config:
        validate_all = True
        validate_assignment = True
        allow_mutation = True

    s3_files_to_generate: int = 10
    s3_clear_before: bool = True
    s3_clear_when_done: bool = True
    analyze_compression: str = None  # Current Redshift options PRESET, ON, OFF (or TRUE, FALSE for the latter options)
