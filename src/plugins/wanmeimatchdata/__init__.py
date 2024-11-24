from nonebot import require
require("nonebot_plugin_htmlrender")
from nonebot_plugin_htmlrender import (
    template_to_pic,
    get_new_page,
    html_to_pic
)
from nonebot import on_command, require
from nonebot.adapters import Message, Event
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot_plugin_alconna import UniMessage
from nonebot.log import logger

import re
import uuid
import os
from .get_match import get_match_info_data
from .database import get_match_by_id, get_steam_id, init_db

init_db()

async def take_screenshot(page, file_path):
    await page.goto(f"file://{file_path}", wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    pic = await page.screenshot(full_page=True)
    await UniMessage.image(raw=pic).send()
    os.remove(file_path)


wanmeimatchdata = on_command("完美比赛查询", aliases={}, block=True, priority=18)
@wanmeimatchdata.handle()
async def _(event: Event, args: Message = CommandArg()):
    match_id = args.extract_plain_text()
    match_new_id = re.search(r'\d+', get_match_by_id(match_id)).group()
    my_steam_id = get_steam_id(event.get_user_id())
    if my_steam_id == None:
        my_steam_id = ""
    if match_id == "":
        await UniMessage.at(event.get_user_id()).text("\n比赛ID呢...").finish(reply_to=True)
    if "error" in match_new_id:
        await UniMessage.at(event.get_user_id()).text("\n您的比赛ID有问题哦...").finish(reply_to=True)
    logger.info(match_new_id)
    match_info = await get_match_info_data(match_new_id,my_steam_id)
    async with get_new_page(viewport={"width": 1332, "height": 798}) as page:
        await take_screenshot(page, match_info)