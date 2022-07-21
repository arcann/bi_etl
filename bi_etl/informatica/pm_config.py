"""
Created on May 5, 2015

@author: Derek Wood
"""

from config_wrangler.config_templates.credentials import Credentials
from pydantic import FilePath


class PMCMDConfig(Credentials):
    INFA_HOME: str = None
    INFA_DOMAINS_FILE: FilePath = None
    USER_SECURITY_DOMAIN: str = None
    REPOSITORY: str
    SERVICE: str
    DOMAIN: str
    DEFAULT_FOLDER: str
    DEFAULT_PARMFILE: str = None
    DEFAULT_LOCALPARAMFILE: str = None
    OSPROFILE: str = None
    RUN_VIA_CMD: bool = False
