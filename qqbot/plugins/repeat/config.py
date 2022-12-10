from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    enabled_groups: dict[int, bool] = {}
