from nonebot import on_command, get_driver
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.params import EventToMe
import datetime
from .config import Config

config = Config.parse_obj(get_driver().config)

ping = on_command("ping", block=True)
time_command = on_command("time", block=True)
whoami = on_command("whoami", block=True)
help_command = on_command("help", block=True)


@ping.handle()
async def handle_ping(bot: Bot, event: GroupMessageEvent, to_me: bool = EventToMe()):
    if not to_me:
        return
    await bot.send_group_msg(
        group_id=event.group_id,
        message=f"Received ping from [CQ:at,qq={event.sender.user_id}].",
    )


@time_command.handle()
async def handle_time(bot: Bot, event: GroupMessageEvent, to_me: bool = EventToMe()):
    if not to_me:
        return
    await bot.send_group_msg(
        group_id=event.group_id, message=f"It is now {datetime.datetime.now()}."
    )


@whoami.handle()
async def handle_whoami(bot: Bot, event: GroupMessageEvent, to_me: bool = EventToMe()):
    if not to_me:
        return
    sender = await bot.get_group_member_info(
        group_id=event.group_id, user_id=event.sender.user_id
    )
    username = sender["nickname"]
    role = sender["role"]
    qid = sender["user_id"]
    join_time = sender["join_time"]
    gender = sender["sex"]
    description = f"You are group {role} {username}, ID {qid}"
    if gender is not None:
        description += ", gender " + gender
    if join_time is not None:
        description += (
            ". You joined this group at "
            + datetime.datetime.utcfromtimestamp(join_time).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
    description += "."
    await bot.send_group_msg(group_id=event.group_id, message=description)


@help_command.handle()
async def handle_help(bot: Bot, event: GroupMessageEvent, to_me: bool = EventToMe()):
    if not to_me:
        return
    help_message = "Welcome to use `wild@programmer` bot!\n\nCommands:\n"
    for command, desc in config.commands.items():
        help_message += f"  - {command}: {desc}\n"
    help_message += "\nUsage:\nUse @ to mention the bot and type `/<command-name>`."
    await bot.send_group_msg(group_id=event.group_id, message=help_message)
