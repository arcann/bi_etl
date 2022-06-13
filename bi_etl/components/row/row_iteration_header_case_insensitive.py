import functools
from typing import *

from sqlalchemy import Column

from bi_etl.components.row.row_iteration_header import RowIterationHeader


if TYPE_CHECKING:
    from bi_etl.components.row.row import Row
    from bi_etl.components.etlcomponent import ETLComponent


class RowIterationHeaderCaseInsensitive(RowIterationHeader):
    # Override since the case-sensitive versions should not share a name map
    __shared_name_map_db = dict()

    def __init__(
            self,
            logical_name: Optional[str] = None,
            primary_key: Optional[Iterable] = None,
            parent: Optional['ETLComponent'] = None,
            columns_in_order: Optional[Iterable] = None,
            owner_pid: int = None,
    ):
        if columns_in_order is not None:
            columns_in_order = [c.lower() for c in columns_in_order]
        super().__init__(
            logical_name=logical_name,            
            primary_key=primary_key,            
            parent=parent,            
            columns_in_order=columns_in_order,            
            owner_pid=owner_pid,            
        )

    @classmethod
    def from_other_header(cls, other_header: RowIterationHeader):
        columns_in_order = [c.lower() for c in other_header.columns_in_order]
        new_inst = cls(
            logical_name=other_header.logical_name,
            primary_key=other_header.primary_key,
            parent=other_header.parent,
            columns_in_order=columns_in_order,
            owner_pid=other_header.owner_pid,
        )
        return new_inst

    def get_column_name(self, input_name: Union[str, Column]) -> str:
        name_str = super().get_column_name(input_name)
        lower_name = name_str.lower()
        self._name_map_db[input_name] = lower_name
        return lower_name

    def has_column(self, column_name) -> bool:
        return self.get_column_name(column_name) in self._columns_positions

    @functools.lru_cache(maxsize=1000)
    def get_column_position(
            self,
            column_name: str,
            allow_create: bool = False,
    ) -> int:
        column_name = self.get_column_name(column_name)
        return super().get_column_position(
            column_name=column_name,
            allow_create=allow_create,
        )

    def row_set_item(
            self,
            column_name: str,
            value,
            row: 'Row',
    ) -> RowIterationHeader:
        column_name_fixed = self.get_column_name(column_name)
        return super().row_set_item(
            column_name=column_name_fixed,
            value=value,
            row=row,
        )

    def rename_column(
            self,
            old_name: str,
            new_name: str,
            ignore_missing: bool = False,
            no_new_header: bool = False,
    ) -> RowIterationHeader:
        """
        Rename a column

        Parameters:
            old_name: str
                The name of the column to find and rename.

            new_name: str
                The new name to give the column.

            ignore_missing: boolean
                Ignore (don't raise error) if we don't have a column with the name in old_name.
                Defaults to False

            no_new_header:
                Skip creating a new row header, modify in place.

                ** BE CAREFUL USING THIS! **

                All new rows created with this header will immediately get the new name,
                in which case you won't want to call this method again.
        """
        old_name = self.get_column_name(old_name)
        new_name = self.get_column_name(new_name)
        return super().rename_column(
            old_name=old_name,
            new_name=new_name,
            ignore_missing=ignore_missing,
            no_new_header=no_new_header,
        )

    def row_remove_column(
            self,
            column_name: str,
            row: 'Row',
            ignore_missing: bool = False,
    ) -> RowIterationHeader:
        column_name = self.get_column_name(column_name)
        return super().row_remove_column(
            column_name=column_name,
            row=row,
            ignore_missing=ignore_missing,
        )
