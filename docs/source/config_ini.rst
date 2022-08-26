config.ini
=============

This is the main configuration file for the bi_etl module.

It relies on `config_wrangler <https://bietl.dev/config_wrangler/>`_
for finding and parsing the config files.

You should build a config class that inherits from
:py:class:`bi_etl.config.bi_etl_config_base.BI_ETL_Config_Base`
or optionally :py:class:`bi_etl.config.bi_etl_config_base.BI_ETL_Config_Base_From_Ini_Env`
(which adds code to automatically read the config data from
an INI file (default is config.ini) and also to load config items from environment variables.
See :py:class:`config_wrangler.config_from_ini_env.ConfigFromIniEnv` and in turn
:py:class:`config_wrangler.config_data_loaders.env_config_data_loader.EnvConfigDataLoader`
and :py:class:`config_wrangler.config_data_loaders.ini_config_data_loader.IniConfigDataLoader`.

**************************************
Building Configuration Classes & Files
**************************************

In most environments you'll have two types of settings:

1. Those that are common across all environments (dev, test, prod)
2. Those that are specific to one environment.

With the config_wrangler cross file references, and setting inheritance we can split those
settings into different files.  The settings that are common across all environments are
checked into the version control repository.  The environment specifc settings are usually
not checked in -- although we have found it useful to checkin an example file like
"config (example).ini"

In this example we ignore the division and put all the settings together.

.. code-block:: ini

    [bi_etl]
    ; See definition in bi_etl.config.bi_etl_config_base.BI_ETL_Config_Section
    environment_name=my_personal_dev
    disk_swap_at_percent_ram_used=90
    disk_swap_at_process_ram_usage_mb=10000
    parallel_processes=1
    partitions_per_thread=2

    [passwords]
    ; config_wrangler will read this to find the default way to get passwords
    password_source=KEEPASS

    [keepass]
    ; config_wrangler will use this section for settings on how to read
    ; passwords from keepass for any config sections that inherit from
    ; config_wrangler.config_templates.credentials.Credentials
    ; and have password_source = KEYPASS
    ; or where password_source = None (the default)
    ;    and [passwords].password_source=KEEPASS
    ;
    database_path=./data/etl_code.kdbx
    default_group=AWS
    password_source=KEYRING
    keyring_section=keepass
    keyring_user_id=keepass

    [logging]
    ; See bi_etl.config.bi_etl_config_base.BI_ETL_Config_Base
    ; which declares this section as an instance of
    ; config_wrangler.config_templates.logging_config.LoggingConfig
    log_folder=C:\python_logs\${bi_etl.environment_name}
    console_log_level=DEBUG
    file_log_level=DEBUG
    console_entry_format=%(levelname)-8s %(name)s: %(message)s
    ## root_level sets the logging level for any class not explicltly set in the [loggers] section
    root_level=INFO
    ## console_log_level can be used to filter ALL messages on the console
    console_log_level=DEBUG
    ## file_log_level can be used to filter ALL messages in the file
    file_log_level=DEBUG
    log_file_max_size=10MB
    log_files_to_keep=9
    log_file_entry_format=%(asctime)s - %(levelname)-8s - %(name)s: %(message)s
    logging_date_format=%Y-%m-%d %H:%M:%S%z
    #######  LOGGING FORMAT PLACEHOLDERS
    #   %(name)s            Name of the logger (logging channel)
    #   %(levelno)s         Numeric logging level for the message (DEBUG, INFO,
    #                       WARNING, ERROR, CRITICAL)
    #   %(levelname)s       Text logging level for the message ("DEBUG", "INFO",
    #                       "WARNING", "ERROR", "CRITICAL")
    #   %(pathname)s        Full pathname of the source file where the logging
    #                       call was issued (if available)
    #   %(filename)s        Filename portion of pathname
    #   %(module)s          Module (name portion of filename)
    #   %(lineno)d          Source line number where the logging call was issued
    #                       (if available)
    #   %(funcName)s        Function name
    #   %(created)f         Time when the LogRecord was created (time.time()
    #                       return value)
    #   %(asctime)s         Textual time when the LogRecord was created
    #   %(msecs)d           Millisecond portion of the creation time
    #   %(relativeCreated)d Time in milliseconds when the LogRecord was created,
    #                       relative to the time the logging module was loaded
    #                       (typically at application startup time)
    #   %(thread)d          Thread ID (if available)
    #   %(threadName)s      Thread name (if available)
    #   %(process)d         Process ID (if available)
    #   %(message)s         The result of record.getMessage(), computed just as
    #                       the record is emitted


    [logging.log_levels]
    ; See config_wrangler.config_templates.logging_config.LoggingConfig
    ; This section is a dynamic mapping of package/class names to the
    ; names of config_wrangler.config_templates.logging_config.LogLevel
    ; Dict[str, LogLevel]
    ; New lines can be added as needed as long as they map to a valid
    ; log level.
    root=INFO
    ## __main__ will be used for ETL jobs or other files when run directly
    __main__=DEBUG
    etl=DEBUG
    bi_etl=INFO
    bi_etl.notifiers.slack=DEBUG
    urllib3.connectionpool=INFO
    slack=INFO
    boto3=INFO
    botocore=INFO
    botocore.hooks=INFO
    s3transfer=INFO
    urllib3=INFO

    [Notifiers]
    ; See bi_etl.config.bi_etl_config_base.BI_ETL_Config_Base
    ; This is a the config class bi_etl.config.bi_etl_config_base.Notifiers
    ; specifies that there should be one or two settings here.  However,
    ; the "setting" values are in turn lists of dynamic references to other
    ; sections of the config.

    failures=Slack_ETL_failure, Jira_Bug
    ; The setting above says that failures should be sent to Slack and Jira
    ; notifiers as defined in the sections below with the names
    ; - Slack_ETL_failure
    ; - Jira_Bug

    ;--NOTE: Empty channels to skip sending notifications
    ;failures=

    [Jira_Bug]
    # Inherits
    # Set comment_on_each_instance to false so we don't get nightly comments and attachments
    comment_on_each_instance=False

    [Slack_ETL]
    notifier_class=Slack
    token=xxxxxxxxxxxxxxxxxxxxx
    channel=#etl_${bi_etl.environment_name}

    [Slack_ETL_failure]
    notifier_class=Slack
    token=${Slack_ETL:token}
    channel=${Slack_ETL:channel}
    mention=@channel

    [target_database]
    ; This section is actually not part of the standard bi_etl config
    ; it is instead an example of what could be defined in your custom config clas
    ;
    ; from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base
    ; from config_wrangler.config_templates.sqlalchemy_database import SQLAlchemyDatabase
    ; class MyCustomConfig(BI_ETL_Config_Base):
    ;    target_database: SQLAlchemyDatabase
    ;
    dialect=redshift+psycopg2
    port=5439
    dsn=warehouse.us-east-1.redshift.amazonaws.com
    dbname=data_warehouse_dev1
    user_id=etl_user
    use_get_cluster_credentials=True
    rs_db_user_id=db.user
    rs_cluster_id=warehouse
    rs_region_name=us-east-1
    duration_seconds=900

