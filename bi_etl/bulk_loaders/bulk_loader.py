# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import logging
from typing import *
from datetime import datetime

import sqlalchemy

from bi_etl.components.row.row import Row
from bi_etl.components.row.row_status import RowStatus

if TYPE_CHECKING:
    from bi_etl.components.table import Table
    from bi_etl.scheduler.task import ETLTask


class BulkLoader(object):
    def __init__(
        self,
    ):
        self.log = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    @property
    def needs_all_columns(self):
        return True

    @staticmethod
    def _get_table_specific_folder_name(
            base_folder: str,
            table_object: Table,
    ):
        table_name_for_folder = table_object.qualified_table_name.replace('.', '_')
        return f'{base_folder}/{table_name_for_folder}'

    def load_from_files(
            self,
            local_files: list,
            table_object: Table,
            table_to_load: str = None,
            perform_rename: bool = False,
            file_compression: str = '',
            options: str = '',
            analyze_compression: str = None,
    ) -> int:
        raise NotImplementedError()

    def load_from_iterator(
            self,
            iterator: Iterator,
            table_object: Table,
            table_to_load: str = None,
            perform_rename: bool = False,
            progress_frequency: int = 10,
            analyze_compression: str = None,
            parent_task: Optional[ETLTask] = None,
    ) -> int:
        raise NotImplementedError()

    def load_table_from_cache(
            self,
            table_object: Table,
            table_to_load: str = None,
            perform_rename: bool = False,
            progress_frequency: int = 10,
            analyze_compression: str = None,
    ) -> int:
        row_count = self.load_from_iterator(
            iterator=table_object.cache_iterator(),
            table_object=table_object,
            perform_rename=False,  # False since we do it here
            analyze_compression=analyze_compression,
        )
        if perform_rename:
            self.rename_table(table_to_load, table_object)
        return row_count

    def rename_table(
            self,
            temp_table_name: str,
            table_object: Table,
    ):
        if temp_table_name is not None:
            old_name = table_object.qualified_table_name + '_old'

            table_object.database.drop_table_if_exists(old_name)

            with Table(
                    table_object.task,
                    table_name=temp_table_name,
                    database=table_object.database,
            ) as table_to_load_object:
                table_object.table.rename(old_name)
                table_to_load_object.table.rename(table_object.table_name)
        else:
            self.log.warning(f'Asked to perform rename but load went directly to {table_object}')

    def apply_updates(
            self,
            table_object: Table,
            update_rows: Sequence[Row]):
        """
        NOT TESTED !
        """
        bcp_update_table_dict = dict()

        for row in update_rows:
            if row.status not in [RowStatus.deleted, RowStatus.insert]:
                update_stmt_key = row.column_set
                if update_stmt_key in bcp_update_table_dict:
                    update_table_object, pending_rows = bcp_update_table_dict[update_stmt_key]
                else:
                    created = False
                    tmp_id = 0
                    table_name = None
                    while not created:
                        # Create a new temp table
                        table_name = "tmp_" + str(datetime.now().toordinal()) + str(tmp_id)
                        try:
                            row_columns = [table_object.get_column(col_name).copy() for col_name in row.columns_in_order]
                            sa_table = sqlalchemy.schema.Table(
                                table_name,
                                table_object.database,
                                *row_columns
                            )
                            sa_table.create()
                            created = True
                        except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.InvalidRequestError):
                            tmp_id += 1
                    update_table_object = Table(
                        task=table_object.task,
                        table_name=table_name,
                        database=table_object.database,
                        )
                    update_table_object.close()
                    pending_rows = list()
                    bcp_update_table_dict[update_stmt_key] = update_table_object, pending_rows
                pending_rows.append(row)

        for update_table_object, pending_rows in bcp_update_table_dict.values():
            self.load_from_iterator(
                iterator=pending_rows,
                table_object=update_table_object,
            )

            database_type = type(table_object.connection().dialect).name
            if database_type == 'oracle':
                raise NotImplementedError("Oracle MERGE not yet implemented")
            elif database_type in ['mssql']:
                sets_list = [f"{column} = {update_table_object.table_name}.{column}"
                             for column in update_table_object.column_names
                             ]
                sets = ','.join(sets_list)

                key_join_list = [
                    f"{table_object}.{column} = {update_table_object.table_name}.{column}"
                    for column in table_object.primary_key
                ]
                key_joins = ','.join(key_join_list)

                sql = f"""\
                    UPDATE {table_object.qualified_table_name}
                    SET {sets}
                    FROM {table_object.qualified_table_name}
                         INNER JOIN
                         {update_table_object.qualified_table_name}
                           ON {key_joins}
                    """
                table_object.execute(sql)
            else:
                raise NotImplementedError("UPDATE FROM/MERGE not yet implemented for {}".format(database_type))