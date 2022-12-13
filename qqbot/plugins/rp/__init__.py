from datetime import datetime
from random import randint
from typing import Dict, Tuple

from tabulate import tabulate
from nonebot import get_driver, on_command, on_message
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, EventToMe

from .config import Config

config = Config.parse_obj(get_driver().config)
rp = on_command("rp")


def get_current_date():
    return datetime.now().strftime("%Y.%m.%d")


def clear_old_record():
    now = get_current_date()
    for record in config.rp:
        if record != now:
            config.rp.pop(record)


@rp.handle()
async def handle_rp(
    bot: Bot,
    event: GroupMessageEvent,
    to_me: bool = EventToMe(),
    args: Message = CommandArg(),
):
    if not to_me:
        return
    clear_old_record()
    now = get_current_date()
    plain_text = args.extract_plain_text()
    if config.rp.get(now, None) is None:
        config.rp[now] = {}
    today = config.rp[now]
    if today.get(event.group_id, None) is None:
        today[event.group_id] = {}
    group_rp = today[event.group_id]
    if plain_text == "rank":
        ranked: Dict[str, int] = dict(
            sorted(group_rp.items(), key=lambda item: item[1], reverse=True)
        )
        rank_cleaned = []
        for i, user in enumerate(ranked, 1):
            username = (await bot.get_group_member_info(
                group_id=event.group_id, user_id=user
            ))['nickname']
            rank_cleaned.append([i, username, ranked[user]])
        rank_table = tabulate(rank_cleaned, ["Rank", "Username", "Rp"])
        await bot.send_group_msg(group_id=event.group_id, message=rank_table)
        return
    sender = event.sender.user_id
    if group_rp.get(sender, None) is None:
        config.rp[now][event.group_id][sender] = group_rp[sender] = randint(0, 100)
        await bot.send_group_msg(
            group_id=event.group_id,
            message=f"[CQ:reply,id={event.message_id}]Your rp for today is {group_rp[sender]}.",
        )
    else:
        await bot.send_group_msg(
            group_id=event.group_id,
            message=f"[CQ:reply,id={event.message_id}]"
            f"You've already tested your rp today. The result is {group_rp[sender]}.",
        )
