from typing import Dict

from nonebot import get_driver, on_command, on_message
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, EventToMe

from .config import Config

config = Config.parse_obj(get_driver().config)

repeat_command = on_command("repeat", priority=1)
repeat_message = on_message(priority=100)
last_message: Dict[int, str] = {}


@repeat_command.handle()
async def handle_command(
    matcher: Matcher,
    bot: Bot,
    event: GroupMessageEvent,
    args: Message = CommandArg(),
    to_me: bool = EventToMe(),
):
    if not to_me:
        return
    matcher.stop_propagation()
    plain_text = args.extract_plain_text()
    if plain_text == "disable":
        config.enabled_groups[event.group_id] = False
        await bot.send_group_msg(group_id=event.group_id, message="Disabled repeating.")
    elif plain_text == "status":
        status = config.enabled_groups.get(event.group_id, None)
        status_text = (
            "unset" if status is None else ("enabled" if status else "disabled")
        )
        await bot.send_group_msg(
            group_id=event.group_id,
            message=f"Repeating is {status_text} for group {event.group_id}.",
        )
    else:
        config.enabled_groups[event.group_id] = True
        await bot.send_group_msg(group_id=event.group_id, message="Enabled repeating!")


@repeat_message.handle()
async def handle_message(bot: Bot, event: GroupMessageEvent):
    if not config.enabled_groups.get(event.group_id):
        return
    await bot.send_group_msg(group_id=event.group_id, message=event.raw_message)
