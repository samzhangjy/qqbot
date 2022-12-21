import random
import string

import nonebot
from nonebot import on_message, require
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent

from qqbot.plugins.moderator.checker import Checker

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import (  # pylint: disable=wrong-import-order,wrong-import-position
    scheduler,
)

moderate_message = on_message(priority=100)
checker = Checker()
violated_count = {}
sent_count = {}


@moderate_message.handle()
async def handle_message(bot: Bot, event: GroupMessageEvent):
    if sent_count.get(event.group_id, None) is None:
        sent_count[event.group_id] = {}
    sender = event.sender.user_id
    if sent_count[event.group_id].get(sender, None) is None:
        sent_count[event.group_id][sender] = 0
    sent_count[event.group_id][sender] += 1
    plain_text = event.get_plaintext()
    offensed_topics = checker.check(plain_text)
    if len(offensed_topics) == 0:
        return
    try:
        await bot.delete_msg(message_id=event.message_id)
    except:  # pylint: disable=bare-except
        pass
    if violated_count.get(event.group_id, None) is None:
        violated_count[event.group_id] = {}
    if violated_count[event.group_id].get(sender, None) is None:
        violated_count[event.group_id][sender] = 0
    violated_count[event.group_id][sender] += 1
    await bot.send_group_msg(
        group_id=event.group_id,
        message=f"[CQ:at,qq={sender}] Violated {', '.join(offensed_topics)}.",
    )


@scheduler.scheduled_job("cron", second="*/30", timezone="Asia/Shanghai")
async def ban_users():
    global violated_count  # pylint: disable=global-statement,invalid-name
    bot = nonebot.get_bot()
    for group, counts in violated_count.items():
        for user, count in counts.items():
            if count > 3:
                await bot.set_group_ban(
                    group_id=group,
                    user_id=user,
                    duration=60 * 5,
                )
                await bot.send_group_msg(
                    group_id=group,
                    message=f"[CQ:at,qq={user}]Banned due to repeatedly violating group rules.",
                )
    violated_count = {}


def random_str(num: int = 5):
    return "".join(random.sample(string.ascii_letters + string.digits, num))


@scheduler.scheduled_job("cron", minute="*/2", timezone="Asia/Shanghai")
async def check_nickname():
    bot = nonebot.get_bot()
    groups = await bot.get_group_list()
    for group in groups:
        users = await bot.get_group_member_list(group_id=group["group_id"], no_cache=True)
        for user in users:
            if not user["card"]:
                continue
            violated = checker.check(user["card"])
            if len(violated) == 0:
                continue
            await bot.set_group_card(
                group_id=group["group_id"],
                user_id=user["user_id"],
                card=f"违规用户名{random_str()}",
            )
            await bot.send_group_msg(
                group_id=group["group_id"],
                message=f"[CQ:at,qq={user['user_id']}]"
                f"Your nickname violated the following rules: {', '.join(violated)}.",
            )

@scheduler.scheduled_job("cron", second="*/5", timezone="Asia/Shanghai")
async def check_spamming():
    global sent_count  # pylint: disable=global-statement,invalid-name
    bot = nonebot.get_bot()
    for group, counts in sent_count.items():
        for user, count in counts.items():
            if count > 6:
                await bot.set_group_ban(
                    group_id=group,
                    user_id=user,
                    duration=60 * 3,
                )
                await bot.send_group_msg(
                    group_id=group,
                    message=f"[CQ:at,qq={user}]Banned due to spamming.",
                )
    sent_count = {}
