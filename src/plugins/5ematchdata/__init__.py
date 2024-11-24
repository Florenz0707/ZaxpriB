from nonebot import on_command, require
from nonebot.adapters import Message, Event
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot_plugin_alconna import UniMessage
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
require("nonebot_plugin_htmlrender")
from nonebot_plugin_htmlrender import get_new_page
from nonebot.plugin import PluginMetadata
__plugin_meta__ = PluginMetadata(
    name="5e比赛查询",
    description="用于查询某场比赛的详细信息，使用 5e比赛查询 [比赛id] 查询",
    usage="示例: 5e比赛查询 114514",
    type="application",
    extra={},
)

from .database import bind_match, get_match_by_id
async def take_screenshot(page, file_path):
    await page.goto(f"{file_path}", wait_until="domcontentloaded")
    await page.wait_for_timeout(2500)
    pic = await page.screenshot(full_page=True)
    return pic

match_query = on_command("5e比赛查询", aliases={}, block=True, priority=17)

@match_query.handle()
async def _(event: Event, matcher: Matcher, arg: Message = CommandArg()):
    # 获取服务器地址和端口
    id = arg.extract_plain_text().strip()
    if id.isdigit():
        match_id = get_match_by_id(int(id))
        if "error" in match_id:
            await UniMessage.at(event.get_user_id()).text("\n没找到这场比赛哦...").finish(reply_to=True)
        async with get_new_page(viewport={"width": 1300, "height": 650}) as page:
            picture = await take_screenshot(page, f"https://arena-next.5eplaycdn.com/home/MatchResult/{match_id}")
        await UniMessage.at(event.get_user_id()).image(raw=picture).finish(reply_to=True)
    
    else:
        await UniMessage.at(event.get_user_id()).text("\n你输入的比赛ID好像有问题...").finish(reply_to=True)
