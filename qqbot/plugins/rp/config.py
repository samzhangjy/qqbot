from typing import Dict

from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    rp: Dict[str, Dict[int, Dict[str, int]]] = {}
