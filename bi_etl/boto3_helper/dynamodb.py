"""
Created on March 28, 2022

@author: 
"""
from typing import *

from bi_etl.boto3_helper.session import Boto3_Base


class DynamoDB(Boto3_Base):
    SERVICE = 'dynamodb'

    def get_dynamo_table(
            self,
            dynamo_table_name,
            region_name: str = None
    ):
        if region_name is not None:
            self.region_name = region_name
        dynamodb = self.resource

        return dynamodb.Table(dynamo_table_name)

    @staticmethod
    def query_dynamo_table(dynamo_table, scan_args_list: Iterable[dict]) -> Iterable[dict]:
        data = []
        for scan_args in scan_args_list:
            tbl_data = dynamo_table.query(**scan_args)
            data.extend(tbl_data['Items'])

            while 'LastEvaluatedKey' in tbl_data:
                tbl_data = dynamo_table.query(ExclusiveStartKey=tbl_data['LastEvaluatedKey'], **scan_args)
                data.extend(tbl_data['Items'])

        return data

    def query_dynamo_table_by_name(
            self,
            dynamo_table_name,
            region_name,
            scan_args_list: Iterable[dict]
    ) -> Iterable[dict]:
        dynamo_table = self.get_dynamo_table(dynamo_table_name, region_name=region_name)
        return self.query_dynamo_table(dynamo_table, scan_args_list)

    def scan_dynamo_table_by_name(self, dynamo_table_name, region_name):
        dynamo_table = self.get_dynamo_table(dynamo_table_name, region_name=region_name)
        return self.scan_dynamo_table(dynamo_table)

    def scan_dynamo_table(self, dynamo_table):
        data = []
        tbl_data = dynamo_table.scan()
        data.extend(tbl_data['Items'])

        return data
