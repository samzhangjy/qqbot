import json
import os
from typing import Tuple

from EdgeGPT import Chatbot
from nonebot import get_driver, on_command, on_message
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, EventToMe

from .config import Config

config = Config.parse_obj(get_driver().config)

edgegpt = on_command("edgegpt", priority=1)
edgegpt_message = on_message(priority=100)
with open("./config.json", "r", encoding="utf-8") as f:
    cookie = json.loads(f.read())["token"]
    os.environ["BING_U"] = cookie


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
            return f"Remote error: {res['item']['result']['message']}"
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
    else:
        config.enabled_groups[event.group_id] = True
        if config.chatbots.get(event.group_id, None) is None:
            config.chatbots[event.group_id] = Chatbot()
        else:
            config.chatbots[event.group_id].reset()
        await bot.send_group_msg(group_id=event.group_id, message="Enabled EdgeGPT!")


@edgegpt_message.handle()
async def handle_message(bot: Bot, event: GroupMessageEvent):
    if not config.enabled_groups.get(event.group_id) or not event.to_me:
        return
    answer = await chat(
        config.chatbots[event.group_id],
        event.group_id,
        event.message.extract_plain_text(),
    )
    max_len = 400
    chunks = [answer[i : i + max_len] for i in range(0, len(answer), max_len)]
    for chunk in chunks:
        retries_remain = 3
        while retries_remain > 0:
            try:
                await bot.send_group_msg(
                    group_id=event.group_id,
                    message=f"[CQ:reply,id={event.message_id}][CQ:at,qq={event.sender.user_id}]{chunk}",
                )
                break
            except:
                retries_remain -= 1
