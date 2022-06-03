"""
Created on March 28, 2022

@author: 
"""
import logging
import warnings

import boto3
import keyring


def get_user_id(
    **kwargs
):
    raise DeprecationWarning("Replaced with self.config.my_config_section.user_id. "
                             "Most likely not needed since the config S3_Bucket will connect seamlessly")


def get_boto3_session_from_config(
        config,
        user_id: str = None,
        password: str = None,
        keyring_system: str = 's3'
):
    warnings.warn("Replace with self.s3_helper_from_config", DeprecationWarning, stacklevel=2)

    log = logging.getLogger(__name__)

    if user_id is None:
        user_id = get_user_id(config)

    if password is None:
        password = keyring.get_password(keyring_system, user_id)
        if password is None:
            raise ValueError(f"Password not supplied in keyring for {keyring_system} {user_id}")
        # Detect short passwords from bad copy/paste
        elif len(password) < 3:
            raise ValueError(f"Password too short ({password}) in keyring for {keyring_system} {user_id}")

    log.info(f'Connecting to S3 with ID {user_id}')
    session = boto3.session.Session(
        aws_access_key_id=user_id,
        aws_secret_access_key=password
    )

    return session


class Boto3_Base(object):
    SERVICE = None

    def __init__(self, session, region_name: str = None):
        self.session = session
        self.region_name = region_name
        self._client = None
        self._resource = None

    @property
    def resource(self, ):
        if self._resource is None:
            self._resource = self.session.resource(self.SERVICE, region_name=self.region_name)

        return self._resource

    @property
    def client(self, ):
        if self._client is None:
            self._client = self.session.client(self.SERVICE, region_name=self.region_name)

        return self._client
