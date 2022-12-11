import json
import re
import uuid
from typing import Tuple

import aiohttp
from fake_useragent import UserAgent
from nonebot import get_driver, on_command, on_message
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, EventToMe

from .config import Config

config = Config.parse_obj(get_driver().config)

chatgpt = on_command("chatgpt", priority=1)
chatgpt_message = on_message(priority=100)


async def chat(
    message: str, parent_message_id: str = None, conversation_id: str = None
) -> Tuple[str, str, str]:
    if parent_message_id is None:
        parent_message_id = str(uuid.uuid4())
    payload = {
        "action": "next",
        "messages": [
            {
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": {"content_type": "text", "parts": [message]},
            }
        ],
        "conversation_id": conversation_id,
        "parent_message_id": parent_message_id,
        "model": "text-davinci-002-render",
    }
    if conversation_id is None:
        del payload["conversation_id"]
    ua = UserAgent()
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{config.chatgpt_url}/backend-api/conversation",
            json=payload,
            headers={"User-Agent": ua.random},
        ) as response:
            content: str = (await response.text(encoding="utf-8")).replace(
                "data: [DONE]", ""
            )
    data = json.loads(re.findall(r"data: (.*)", content)[-1])
    return (
        data["message"]["content"]["parts"][0],
        data["message"]["id"],
        data["conversation_id"],
    )


@chatgpt.handle()
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
        await bot.send_group_msg(group_id=event.group_id, message="Disabled ChatGPT.")
    elif plain_text == "status":
        status = config.enabled_groups.get(event.group_id, None)
        status_text = (
            "unset" if status is None else ("enabled" if status else "disabled")
        )
        await bot.send_group_msg(
            group_id=event.group_id,
            message=f"ChatGPT is {status_text} for group {event.group_id}.",
        )
    else:
        config.enabled_groups[event.group_id] = True
        await bot.send_group_msg(group_id=event.group_id, message="Enabling ChatGPT...")
        if config.group_conversation_ids.get(event.group_id, None) is None:
            config.group_conversation_ids[event.group_id] = (None, None)
        await bot.send_group_msg(group_id=event.group_id, message="Enabled ChatGPT!")


@chatgpt_message.handle()
async def handle_message(bot: Bot, event: GroupMessageEvent):
    if not config.enabled_groups.get(event.group_id) or not event.to_me:
        return
    answer, parent_message_id, conversation_id = await chat(
        event.raw_message,
        config.group_conversation_ids[event.group_id][0],
        config.group_conversation_ids[event.group_id][1],
    )
    config.group_conversation_ids[event.group_id] = (parent_message_id, conversation_id)
    await bot.send_group_msg(
        group_id=event.group_id,
        message=f"[CQ:reply,id={event.message_id}][CQ:at,qq={event.sender.user_id}]{answer}",
    )
