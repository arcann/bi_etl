"""
Created on March 28, 2022

@author: 
"""

from bi_etl.boto3_helper.session import Boto3_Base


class SSM(Boto3_Base):
    SERVICE = 'ssm'
