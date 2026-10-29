import json
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pathlib import Path, PurePath
from typing import Any

from pydantic import BaseModel


def json_default(obj: Any) -> str | int:
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, type):
        return str(obj)
    if isinstance(obj, BaseModel):
        return obj.model_dump_json()
    if isinstance(obj, PurePath):
        return str(obj)
    if isinstance(obj, Enum):
        # noinspection PyTypeChecker
        return obj.value
    print(f"No handling for {type(obj)} = {obj}")
    raise TypeError(f"No handling for {type(obj)} = {obj}")


# json class library way
class OurJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        return json_default(obj)


def json_dumps(obj: Any, **kwargs) -> str | None:
    if obj is None:
        return None
    else:
        return json.dumps(obj, cls=OurJSONEncoder, **kwargs)
