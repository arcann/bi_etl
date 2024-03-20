import logging
from pathlib import Path
from typing import Optional, cast

from bi_etl.scheduler.task import ETLTask
from examples.example_config import ExampleETLConfig


class ExampleETLTaskBase(ETLTask):
    def __init__(
            self,
            task_id=None,
            parent_task_id=None,
            root_task_id=None,
            scheduler=None,
            task_rec=None,
            config: Optional[ExampleETLConfig] = None,
            config_load_log_level: int = logging.INFO,
            **kwargs
    ):
        if config is None:
            config = ExampleETLConfig(config_load_log_level=config_load_log_level)
        super().__init__(
            task_id=task_id,
            parent_task_id=parent_task_id,
            root_task_id=root_task_id,
            scheduler=scheduler,
            task_rec=task_rec,
            config=config,
            **kwargs
        )
        assert isinstance(self.config, ExampleETLConfig)
        self.config = cast(ExampleETLConfig, self.config)

    @property
    def package_path(self) -> Path:
        return Path(__file__).parent.parent

    def get_target_database_metadata(self):
        return self.get_database_metadata(self.config.target_database)
