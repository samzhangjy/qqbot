import json
import os
from typing import Tuple

from EdgeGPT import Chatbot
from nonebot import get_driver, on_command, on_message, require
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, EventToMe
import nonebot
from poe import Client as Poe

from datetime import datetime

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import (
    scheduler,
)  # pylint: disable=wrong-import-order,wrong-import-position

from .config import Config
import time

config = Config.parse_obj(get_driver().config)

edgegpt = on_command("edgegpt", priority=1)
edgegpt_message = on_message(priority=100)
with open("./config.json", "r", encoding="utf-8") as f:
    data = json.loads(f.read())
    cookie = data["token"]
    poe_token = data["poe-token"]
    proxy = data["proxy"]
    os.environ["BING_U"] = cookie
    poe_client = Poe(poe_token, proxy)
# jarvis_groups = [450854560, 132608658]
jarvis_groups = [450854560]


async def chat(chatbot: Chatbot, group_id: int, message: str) -> list:
    try:
        if config.is_responding.get(group_id, False):
            return "Error: The last user message is being processed. Please wait for a response before submitting further messages."
        config.is_responding[group_id] = True
        ag = chatbot.ask_stream(prompt=message)
        res = ""
        async for _, response in ag:
            res = response
        if res["item"].get("messages", None) is None:
            config.is_responding[group_id] = False
            err_msg = f"Remote error: {res['item']['result']['message']}"
            if res["item"]["result"].get("exception", None) is not None:
                err_msg += "\n\n" + res["item"]["result"]["exception"]
            return err_msg
        search_results = ""
        answer = ""
        for response in res["item"]["messages"]:
            if response["author"] == "bot":
                answer = response["text"]
                if (
                    len(response.get("adaptiveCards", [])) != 0
                    and len(response["adaptiveCards"][0].get("body", [])) > 1
                ):
                    search_results = response["adaptiveCards"][0]["body"][-1]["text"]
                break
        config.is_responding[group_id] = False
        if search_results:
            answer += "\n\n" + search_results
        return answer
    except Exception as e:
        config.is_responding[group_id] = False
        return f"Error: {e}"


async def chat_poe(message: str) -> None:
    try:
        for chunk in poe_client.send_message("jarvissamzhang", message):
            pass
        return str(chunk["text"]).strip("Jarvis:").strip()
    except Exception as e:
        return f"Error: {e}"


@edgegpt.handle()
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
        config.is_responding[event.group_id] = False
        if config.chatbots.get(event.group_id, None) is not None:
            config.chatbots[event.group_id].close()
        await bot.send_group_msg(group_id=event.group_id, message="Disabled EdgeGPT.")
    elif plain_text == "status":
        status = config.enabled_groups.get(event.group_id, None)
        status_text = (
            "unset" if status is None else ("enabled" if status else "disabled")
        )
        await bot.send_group_msg(
            group_id=event.group_id,
            message=f"EdgeGPT is {status_text} for group {event.group_id}.",
        )
    elif plain_text == "reset":
        config.is_responding[event.group_id] = False
        poe_client.send_chat_break("jarvissamzhang")
        config.chatbots[event.group_id] = Chatbot()
        await bot.send_group_msg(
            group_id=event.group_id, message="EdgeGPT reset successfully."
        )
    else:
        config.enabled_groups[event.group_id] = True
        if config.chatbots.get(event.group_id, None) is None:
            config.chatbots[event.group_id] = Chatbot()
        else:
            config.chatbots[event.group_id].reset()
        await bot.send_group_msg(group_id=event.group_id, message="Enabled EdgeGPT!")


@edgegpt_message.handle()
async def handle_message(bot: Bot, event: GroupMessageEvent):
    # if not config.enabled_groups.get(event.group_id) or not event.to_me:
    if not config.enabled_groups.get(event.group_id):
        return
    # answer = await chat(
    #     config.chatbots[event.group_id],
    #     event.group_id,
    #     event.message.extract_plain_text(),
    # )
    answer = await chat_poe(
        f"{event.sender.nickname}({event.sender.user_id}): {event.message.extract_plain_text()}"
    )
    max_len = 400
    chunks = [answer[i : i + max_len] for i in range(0, len(answer), max_len)]
    for chunk in chunks:
        retries_remain = 3
        while retries_remain > 0:
            try:
                await bot.send_group_msg(
                    group_id=event.group_id,
                    message=f"{chunk}",
                )
                break
            except:
                retries_remain -= 1


@scheduler.scheduled_job("date", run_date=datetime(2023, 4, 14, 20, 16))
async def handle_job():
    bot = nonebot.get_bot()
    groups = await bot.get_group_list()
    for group in groups:
        if group["group_id"] not in jarvis_groups:
            continue
        group_id = group["group_id"]
        await bot.send_group_msg(
            group_id=group_id,
            message="Error: internal server failure, please contact cloud computing provider adminstrator for details.",
        )
        time.sleep(1)
        await bot.send_group_msg(
            group_id=group_id, message="Trying to restart server..."
        )
        time.sleep(5)
        await bot.send_group_msg(group_id=group_id, message="Server restarted.")
        time.sleep(1)
        await bot.send_group_msg(group_id=group_id, message="Starting project Jarvis.")
        config.enabled_groups[group_id] = True
        await bot.send_group_msg(group_id=group_id, message="Jarvis started.")
        poe_client.send_chat_break("jarvissamzhang")
        answer = await chat_poe("系统: Jarvis 机器人成功启动。")
        await bot.send_group_msg(group_id=group_id, message=answer)
