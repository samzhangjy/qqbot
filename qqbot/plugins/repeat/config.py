from typing import Dict

from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    enabled_groups: Dict[int, bool] = {}
