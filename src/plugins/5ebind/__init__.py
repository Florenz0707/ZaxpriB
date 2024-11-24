from nonebot import on_command, require
from nonebot.adapters import Message, Event
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot_plugin_alconna import UniMessage
from nonebot.log import logger


from .database import init_db, bind_steam_id, get_steam_id
from .api_requests import search_user, info_5e, get_uuid
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import re
from nonebot.plugin import PluginMetadata
__plugin_meta__ = PluginMetadata(
    name="5e绑定",
    description="用于绑定5e对战平台账号,指令后加上自己的用户名或是5eID进行绑定",
    usage="示例: 5e绑定 Zaxpris 或 5e绑定 0129ellmdwg4",
    type="application",
    extra={},
)

# Levenshtein 距离计算函数
def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1, 1):
        current_row = [i]
        for j, c2 in enumerate(s2, 1):
            insertions = previous_row[j] + 1
            deletions = current_row[j - 1] + 1
            substitutions = previous_row[j - 1] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

init_db()

def process_string(input_str):
    # 去除首尾和中间多余空格
    input_str = re.sub(r'\s+', ' ', input_str.strip())

    # 检查是否含有非法字符，允许的字符为字母、数字、空格、连字符和下划线
    if not re.match(r'^[a-zA-Z0-9_\- ]*$', input_str):
        return {"error": "\n您输入的5E ID含有非法字符，请确认您输入的不是用户名！\n\n或使用指令 帮助 来获取更多信息"}
    return {}

fiveebind = on_command("5e绑定", aliases={"5ebind","5ebd"}, block=True, priority=1)

@fiveebind.handle()
async def bind_handler(event: Event, arg: Message = CommandArg()):
    steamid = arg.extract_plain_text().strip()
    if not steamid:
        await UniMessage.at(event.get_user_id()).text("\n请在指令后面加上你的5EID或用户名！\n\n或使用指令 帮助 来获取更多信息").finish(reply_to=True)

    get_user = await info_5e(steamid)

    if "error" in get_user:

        user_info = await search_user(steamid)
        if "error" in user_info:
            await UniMessage.at(event.get_user_id()).text(user_info['error']).finish(reply_to=True)
        users = user_info['data']['list']
        best_match = None
        min_distance = float('inf')

        for user in users:
            name = user['username']
            domain = user['domain']
            
            # 计算 domain 和 steamid 之间的相似度
            distance = levenshtein_distance(domain, steamid)
            
            # 如果当前距离更小，则更新最佳匹配
            if distance < min_distance:
                min_distance = distance
                best_match = user
        if best_match:
            matched_domain = best_match['domain']
            steamid = matched_domain
        else:
            await UniMessage.at(event.get_user_id()).text("\n绑定失败！\n未找到该用户！").finish(reply_to=True)
        
        get_user = await info_5e(steamid)

        if "error" in get_user:
            await UniMessage.at(event.get_user_id()).text("\n绑定失败！\n未找到该用户！").finish(reply_to=True)

    user_id = str(event.get_user_id())
    bind_steam_id(user_id, steamid)
    await UniMessage.at(event.get_user_id()).text(f"\n绑定成功！\n\n已绑定5e用户:{get_user['data']['user']['username']}\n如绑定用户有误请使用指令 帮助 获取更多信息").finish(reply_to=True)


fiveesearch = on_command("搜索5e用户", aliases={"ss5eyh"}, block=True, priority=2)

@fiveesearch.handle()
async def search_handler(event: Event, arg: Message = CommandArg()):
    name = arg.extract_plain_text().strip()
    if not name:
        await UniMessage.text("请输入要查找的用户名！\n\n或使用指令 帮助 来获取更多信息").finish(reply_to=True)
    user_info = await search_user(name)
    if "error" in user_info:
        await UniMessage.text(user_info['error']).finish(reply_to=True)
    else:
        msg = "\n"
        for user in user_info['data']['list']:
            avatar_url = user['avatar_url']
            username = user['username']
            domain = user['domain']
            msg += f"\n用户名: {username}\n5E ID: {domain}\n---------------"
        await UniMessage.at(event.get_user_id()).text(msg).finish(reply_to=True)