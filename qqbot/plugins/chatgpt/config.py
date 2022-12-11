from typing import Dict, Tuple

from pydantic import BaseModel, Extra
import os


class Config(BaseModel, extra=Extra.ignore):
    enabled_groups: Dict[int, bool] = {}
    group_conversation_ids: Dict[int, Tuple[str, str]] = {}
    chatgpt_url: str = "https://gpt.chatapi.art"
