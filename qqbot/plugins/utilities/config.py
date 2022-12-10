from typing import Dict

from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    commands: Dict[str, str] = {
        "repeat": "Start / stop repeating others' messages.",
        "ban": "Ban given user.",
        "unban": "Unban given user.",
        "whoami": "Show sender's information.",
        "liferestart": "Play the `Life Restart` game.",
        "time": "Get current time.",
        "ping": "Test connection with bot.",
        "help": "Show this message and exit.",
    }
