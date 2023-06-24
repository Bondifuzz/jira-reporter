import functools

from .settings import load_app_settings
from pydantic import BaseModel, root_validator, ValidationError
from typing import Dict, Any, Optional
from datetime import datetime

def find_end(text: str, sub: str, start: Optional[int] = None) -> int:
    pos = text.find(sub, start)
    if pos != -1:
        pos += len(sub)
    return pos


def rfc3339_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def check_empty_strings(data: Dict[str, Any]):

    names = []
    for name, value in data.items():
        if isinstance(value, str):
            if len(value) == 0:
                names.append(name)

    return names


def check_at_least_one_field_set(data: Dict[str, Any]):
    return len(list(filter(lambda x: x is not None, data.values()))) > 0


class PydanticBaseModel(BaseModel):
    @root_validator
    def check_empty_strings(cls, data: Dict[str, Any]):

        names = check_empty_strings(data)
        if not names:
            return data

        raise ValueError(f"Empty strings not allowed in '{names}'")


class PydanticPartialBaseModel(PydanticBaseModel):
    @root_validator
    def check_at_least_one_field_set(cls, data: Dict[str, Any]):

        if check_at_least_one_field_set(data):
            return data

        raise ValueError("At least one field must be set")


def testing_only(func):

    """Provides decorator, which forbids
    calling dangerous functions in production"""

    settings = load_app_settings()
    is_danger = settings.environment.name == "prod"

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):

        if is_danger:
            err = f"Function '{func.__name__}' is allowed to call only in testing mode"
            help = "Please, check 'ENVIRONMENT' variable is not set to 'prod'"
            raise RuntimeError(f"{err}. {help}")

        return await func(*args, **kwargs)

    return wrapper
