from typing import Dict

from EdgeGPT import Chatbot
from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    enabled_groups: Dict[int, bool] = {}
    chatbots = {}
    chatgpt_url: str = "https://gpt.chatapi.art"
