import datetime
import re

from nonebot import on_command
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, Bot, GroupMessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, EventToMe

ban = on_command("ban")
unban = on_command("unban")


async def convert_to_seconds(time_str: str) -> int:
    units = {
        "s": "seconds",
        "m": "minutes",
        "h": "hours",
        "d": "days",
        "w": "weeks",
    }
    return int(
        datetime.timedelta(
            **{
                units.get(m.group("unit").lower(), "seconds"): float(m.group("val"))
                for m in re.finditer(
                    r"(?P<val>\d+(\.\d+)?)(?P<unit>[smhdw]?)", time_str, flags=re.I
                )
            }
        ).total_seconds()
    )


async def cq_at_parser(cq_at: str) -> int:
    pattern = r"\[CQ\:at,qq=(\d+)\]"
    uid = int(re.match(pattern, str(cq_at)).group(1))
    return uid


@ban.handle()
async def handle_ban(
    bot: Bot,
    matcher: Matcher,
    event: GroupMessageEvent,
    args: Message = CommandArg(),
    to_me: bool = EventToMe(),
):
    if not to_me:
        return
    matcher.stop_propagation()
    if not await GROUP_ADMIN(bot, event):
        await bot.send_group_msg(
            group_id=event.group_id, message="Sorry, only group admins can ban members."
        )
        return
    if args.extract_plain_text() == "all":
        await bot.set_group_whole_ban(group_id=event.group_id, enable=True)
        await bot.send_group_msg(
            group_id=event.group_id,
            message=f"Successfully banned group {event.group_id}.",
        )
        return
    cq_at = args[0]
    duration_str = args.extract_plain_text()
    if not duration_str.strip():
        duration_str = "30m"
    await bot.set_group_ban(
        group_id=event.group_id,
        user_id=(await cq_at_parser(cq_at)),
        duration=(await convert_to_seconds(duration_str)),
    )
    await bot.send_group_msg(
        group_id=event.group_id,
        message=f"Successfully banned {cq_at} for {duration_str}.",
    )


@unban.handle()
async def handle_unban(
    bot: Bot,
    matcher: Matcher,
    event: GroupMessageEvent,
    to_me: bool = EventToMe(),
    args: Message = CommandArg(),
):
    if not to_me:
        return
    matcher.stop_propagation()
    if not await GROUP_ADMIN(bot, event):
        await bot.send_group_msg(
            group_id=event.group_id, message="Sorry, only group admins can unban members."
        )
        return
    if args.extract_plain_text() == "all":
        await bot.set_group_whole_ban(group_id=event.group_id, enable=False)
        await bot.send_group_msg(
            group_id=event.group_id,
            message=f"Successfully unbanned group {event.group_id}.",
        )
        return
    cq_at = args[0]
    await bot.set_group_ban(
        group_id=event.group_id, user_id=await cq_at_parser(cq_at), duration=0
    )
    await bot.send_group_msg(
        group_id=event.group_id, message=f"Successfully unbanned {cq_at}."
    )
