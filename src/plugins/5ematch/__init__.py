from nonebot import on_command, require
from nonebot.adapters import Message, Event
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot_plugin_alconna import UniMessage
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

from nonebot import require
require("nonebot_plugin_htmlrender")
from nonebot_plugin_htmlrender import (
    template_to_pic,
    get_new_page,
    html_to_pic
)
from .database import init_db, bind_steam_id, get_steam_id
from .api_requests import get_uuid
from .make_match_pic import make_match_pic
import os
import io
import json
__plugin_meta__ = PluginMetadata(
    name="5e比赛记录",
    description="用于查询5e对战平台账号比赛记录",
    usage="示例: 5e比赛记录 Zaxpris 或 5e比赛记录 0129ellmdwg4",
    type="application",
    extra={},
)

async def take_screenshot(page, url:str):
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_timeout(5000)
    pic = await page.screenshot(full_page=True)
    return pic

def get_message_at(data: str) -> list:
    qq_list = []
    data = json.loads(data)
    try:
        for msg in data['message']:
            if msg['type'] == 'at':
                qq_list.append(int(msg['data']['qq']))
        return qq_list
    except Exception:
        return []

init_db()

fivee_info = on_command("5e比赛记录", aliases={"5ebsjl"}, priority=5, block=True)
@fivee_info.handle()
async def _(event: Event, args: Message = CommandArg()):
    args = args.extract_plain_text().strip()
    qq = event.get_user_id()

    if args:

        uuid = await get_uuid(args)
        if "error" in uuid:
            await UniMessage.text(uuid["error"]).finish()
        if uuid == "":
            await UniMessage.at(event.get_user_id()).text("\n没找到这个用户的说...").finish(reply_to=True)
        else:
            #事件处理
            raw = await make_match_pic(uuid)
            if isinstance(raw, bytes):
                await UniMessage.at(event.get_user_id()).image(raw=raw).finish(reply_to=True)
            else:
                await UniMessage.at(event.get_user_id()).text(raw["error"]).finish(reply_to=True)
            
    else:
        at = get_message_at(event.json())
        if len(at) > 0:
            qq = at[0]
            is_use_at = True
        domain = get_steam_id(qq)

        if domain != None:
            uuid = await get_uuid(domain)
            #事件处理
            raw = await make_match_pic(uuid)
            
            if isinstance(raw, bytes):
                await UniMessage.at(event.get_user_id()).image(raw=raw).finish(reply_to=True)
            else:
                await UniMessage.at(event.get_user_id()).text(raw["error"]).finish(reply_to=True)
        else:
            if is_use_at:
                await UniMessage.at(event.get_user_id()).text("\nTA还未绑定5E账号哦...").finish(reply_to=True)
            else:
                await UniMessage.at(event.get_user_id()).text("\n未绑定5E账号，请先绑定哦...").finish(reply_to=True)
        