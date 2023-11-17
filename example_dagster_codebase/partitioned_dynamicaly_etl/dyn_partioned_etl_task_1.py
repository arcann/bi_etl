import random
from datetime import datetime
from functools import lru_cache
from typing import Optional, Mapping, Any, Sequence

import dagster

from bi_etl.scheduler.etl_task import DAGSTER_SENSOR_TYPE
from tests.etl_jobs.etl_test_task_base import ETL_Test_Task_Base


class PartitionedDynETLTask1(ETL_Test_Task_Base):
    # No dependencies so dagster_input_etl_tasks is not present

    @classmethod
    def dagster_group_name(cls, **kwargs) -> Optional[str]:
        return 'special_group_2'

    @classmethod
    def dagster_op_tags(
            cls,
            **kwargs
    ) -> Optional[Mapping[str, Any]]:
        return {
            'is_part': True,
            'is_sample': True,
            'is_great': False,
        }

    @classmethod
    @lru_cache(maxsize=None)
    def dagster_partitions_def(
            cls,
            *,
            debug: bool = False,
            **kwargs
    ) -> Optional[dagster.PartitionsDefinition]:
        """
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the asset.
        """
        return dagster.DynamicPartitionsDefinition(name="part_number")

    @classmethod
    def example_partition_change_sensor(
            cls,
            *,
            debug: bool = False,
            **kwargs
    ):
        this_asset_key = cls.dagster_asset_key()

        asset_job = dagster.define_asset_job(
            f"{this_asset_key.to_python_identifier()}_asset_job",
            f"{this_asset_key.to_user_string()}*"
        )

        # noinspection PyTypeChecker
        @dagster.sensor(
            minimum_interval_seconds=30,
            description="""
                This is a test sensor that adds new partitions every 30 seconds.  
                Once a limit (100) is reached it removes the oldest partitions. 
            """,
            job=asset_job,
            default_status=dagster.DefaultSensorStatus.RUNNING,
        )
        def sensor_check(
            context: dagster.SensorEvaluationContext,
        ):
            if debug:
                context.log.info(
                    f"{cls.dagster_asset_key()} "
                    f"sensor_check {context.sensor_name} "
                    f"context.last_completion_time {context.last_completion_time} "
                    f"context.cursor {context.cursor} "
                )


            dagster_partitions_def: dagster.DynamicPartitionsDefinition = cls.dagster_partitions_def()

            existing_keys = list(dagster_partitions_def.get_partition_keys(dynamic_partitions_store=context.instance))
            existing_keys.sort()
            context.log.info(f"Existing partition keys: {existing_keys}")
            existing_keys_as_int = [int(key) for key in existing_keys]

            max_key = max(existing_keys_as_int)
            partitions_to_add = [f"{max_key + 1}"]

            MAX_PARTITIONS = 100

            if len(existing_keys) > MAX_PARTITIONS:
                cnt_partitions_to_remove = MAX_PARTITIONS - len(existing_keys)
                partitions_to_remove = existing_keys[:cnt_partitions_to_remove]
            else:
                partitions_to_remove = []

            # Update some random partitions
            update_random_choices = random.choices(existing_keys, k=random.choice([0, 0, 1, 2]))

            context.log.info(f"Updating partitions {update_random_choices}")
            context.log.info(f"Adding partitions {partitions_to_add}")
            context.log.info(f"Removing partitions {partitions_to_remove}")

            # Just an example cursor value to save for the next iteration of this function
            # It doesn't really do anything in this example
            # A logical cursor in many cases would be the datetime that the source was last scanned
            # So that now we could look for modified_date >= cursor_date
            cursor = f"{max_key}"

            return dagster.SensorResult(
                # Run all updated partitions
                # run_key is provided above so that a job is only done once.
                # We don't provide it for
                # See https://docs.dagster.io/concepts/partitions-schedules-sensors/sensors#idempotence-using-run-keys
                run_requests=[dagster.RunRequest(partition_key=key, run_key="a-{key}", tags={'delete': False})
                              for key in partitions_to_add] +
                             [dagster.RunRequest(partition_key=key, run_key=None, tags={'delete': False})
                              for key in update_random_choices] +
                             [dagster.RunRequest(partition_key=key, run_key=f"d-{key}", tags={'delete': True})
                              for key in partitions_to_remove],
                cursor=cursor,
                # Add new partitions only (not existing but changed)
                dynamic_partitions_requests=[
                    dagster_partitions_def.build_add_request(list(partitions_to_add))
                ],
            )
        return sensor_check

    @classmethod
    def example_asset_sensor(
            cls,
            *,
            debug: bool = False,
            **kwargs
    ):
        """
        Sensor that runs after each asset materialization.
        Used here to delete partitions after materializing a delete request.
        """

        @dagster.asset_sensor(
            asset_key=cls.dagster_asset_key(),
            minimum_interval_seconds=30,
            description="""
                This is a test sensor that handles partition removals after the asset runs.
            """,
            default_status=dagster.DefaultSensorStatus.RUNNING,
        )
        def asset_sensor_function(
                context: dagster.SensorEvaluationContext,
                asset_event: dagster.EventLogEntry
        ):
            assert asset_event.dagster_event and asset_event.dagster_event.asset_key

            context.log.info(f"asset_sensor running {asset_event}")

            if asset_event.asset_materialization.metadata.get('deleted', False):
                context.log.info(f"Removing partition # {asset_event.asset_materialization.partition} from records after delete job")
                context.instance.delete_dynamic_partition(cls.dagster_partitions_def().name, asset_event.asset_materialization.partition)

            # We don't need to actually run anything
            # yield dagster.RunRequest(
            #     run_key=context.cursor,
            # )
        return asset_sensor_function

    @classmethod
    @lru_cache(maxsize=None)
    def dagster_sensors(
            cls,
            *,
            debug: bool = False,
            **kwargs
    ) -> Optional[Sequence[DAGSTER_SENSOR_TYPE]]:
        """
        Return a list of one more sensors for this task
        """
        return [
            cls.example_partition_change_sensor(),
            cls.example_asset_sensor(),
        ]

    @classmethod
    def dagster_code_version(
            cls,
            **kwargs
    ) -> Optional[str]:
        return '1.0'

    def load(self):
        self.log.info("PartitionedETLTask1 starting")
        context = self.dagster_context
        self.log.info(f"Partition executing = '{context.partition_key}'")
        context.log.info(context.partition_key)

        if context.run_tags.get('delete', False):
            self.log.info(f"Partition deletion run for = '{context.partition_key}'")
            self.dagster_results = dagster.Output(
                {
                    'update_dt': datetime.now()
                },
                metadata={
                    'deleted': True,
                },
                data_version=dagster.DataVersion('deleted'),
            )
        else:
            self.set_parameters(job_run_seconds=2, extra_random_seconds=0)
            # load inherited from ETL_Test_Task_Base
            super().load()
            self.dagster_results = dagster.Output({
                'update_dt': datetime.now()
                },
                data_version=dagster.DataVersion(datetime.now().isoformat()),
            )
            self.log.info(f"Partition create/update run for = '{context.partition_key}'")
