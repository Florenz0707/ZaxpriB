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
from .api_requests import search_user,info_wm,get_card_info
from .grade_image_processing import create_hexagon_image
from PIL import Image, ImageDraw, ImageFont
import re
import io
import base64
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import uuid
import os


# 初始化数据库
init_db()

__plugin_meta__ = PluginMetadata(
    name="完美绑定",
    description="用于绑定完美世界对战平台账号,指令后加上自己的用户名或是Steam64位ID进行绑定",
    usage="示例: 完美绑定 Zaxpris 或 完美绑定 76561199239617537",
    type="application",
    extra={},
)

async def take_screenshot(page, file_path):
    await page.goto(f"file://{file_path}", wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    pic = await page.screenshot(full_page=True, path="./html2pic.png")
    image = Image.open(io.BytesIO(pic))
    cropped_image = image.crop((0, 0, 1509, 595))
    output_buffer = io.BytesIO()
    cropped_image.save(output_buffer, format='JPEG')  # 根据需要选择合适的格式
    cropped_image_bytes = output_buffer.getvalue()
    return cropped_image_bytes
    os.remove(file_path)
    os.remove("./html2pic.png")


def generate_hex_filename():
    return f"{uuid.uuid4().hex}.html"
def calculate_grade(score: int) -> str:
    grade_ranges = {
        range(0, 1): '?',
        range(1, 1000): 'D',
        range(1000, 1201): 'D+',
        range(1201, 1401): 'C',
        range(1401, 1601): 'C+',
        range(1601, 1801): 'B',
        range(1801, 2001): 'B+',
        range(2001, 2201): 'A',
        range(2201, 2401): 'A+'
    }
    
    for grade_range, grade in grade_ranges.items():
        if score in grade_range:
            return grade
    return 'S'  # 2401及以上均显示S

def get_upordownimg(upordown:str):
    if upordown == "down":
        return '<svg viewBox="0 0 1024 1024" data-icon="caret-down" width="1em" height="1em" fill="currentColor" aria-hidden="true" focusable="false" class=""><path d="M840.4 300H183.6c-19.7 0-30.7 20.8-18.5 35l328.4 380.8c9.4 10.9 27.5 10.9 37 0L858.9 335c12.2-14.2 1.2-35-18.5-35z"></path></svg>'
    elif upordown == "up":
        return '<svg viewBox="0 0 1024 1024" data-icon="caret-up" width="1em" height="1em" fill="currentColor" aria-hidden="true" focusable="false" class=""><path d="M858.9 689L530.5 308.2c-9.4-10.9-27.5-10.9-37 0L165.1 689c-12.2 14.2-1.2 35 18.5 35h656.8c19.7 0 30.7-20.8 18.5-35z"></path></svg>'
    else:
        return ''
def generate_progress_circle(current_value, max_value):
    # 计算进度百分比
    percentage = current_value / max_value
    # SVG路径的总周长 (调整此值以适应你的需求)
    total_length = 292.168
    # 根据百分比计算当前的进度长度
    progress_length = total_length * percentage
    
    # 创建SVG元素
    svg_template = f'''
        <path style="stroke-dasharray: {progress_length}px, 292.168px; stroke-dashoffset: 0px; transition: stroke-dashoffset 0.3s ease 0s, stroke-dasharray 0.3s ease 0s, stroke 0.3s ease 0s, stroke-width 0.06s ease 0.3s;" class="ant-progress-circle-path" fill-opacity="0" stroke-width="7" stroke-linecap="round" stroke="url(#ant-progress-gradient-60)" d="M 50,50 m 0,-46.5
     a 46.5,46.5 0 1 1 0,93
     a 46.5,46.5 0 1 1 0,-93"></path>
    '''
    return svg_template

def save_html(rendered_html: str, filename: str):
    # 将 HTML 保存至指定文件路径
    output_path = Path(__file__).parent / filename
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    print(f"HTML saved to {output_path}")

wanmei_bind = on_command("wanmeibind", aliases={"完美绑定"}, block=True, priority=3)

@wanmei_bind.handle()
async def bind_handler(matcher: Matcher, event: Event, arg: Message = CommandArg()):
    steamid = arg.extract_plain_text().strip()

    if not steamid:
        await UniMessage.at(event.get_user_id()).text("\n请在指令后面加上你的steam64位id或是用户名！\n\n或使用指令 帮助 来获取更多信息").finish()
    user_info = await info_wm(steamid)
    logger.info(user_info)
    if "error" in user_info or steamid.isdigit() == False:
        user_info = await search_user(steamid)
        if "error" in user_info:
            await UniMessage.at(event.get_user_id()).text(user_info['error']).finish()
        steamid = user_info['data']['users'][0]['steam_id']
        name = user_info['data']['users'][0]['nickname']
    else:
        name = user_info['data']['name']
    user_id = str(event.get_user_id())
    bind_steam_id(user_id, steamid)
    card_info = await get_card_info(steamid)

    def get_change_status(value, threshold=0):
        if value > threshold:
            return "up", get_upordownimg("up"), "green"
        elif value < threshold:
            return "down", get_upordownimg("down"), "red"
        return "", get_upordownimg(""), ""

    def get_color(value, thresholds, colors):
        for threshold, color in zip(thresholds, colors):
            if value >= threshold:
                return color
        return colors[-1]

    card_data = card_info.get('data', {}).get('card_info', {})
    ladder_stats = card_data.get('ladder_season_stats', {})

    user = {
        "avatarurl": card_data['avatar'],
        "frameurl": card_data.get('avatarBorder', {}).get('image', ""),
        "name": card_data['nickname'],
        "power": card_data.get('perfectPower', {}).get('perfectPower'),
        "eloimg": "",
        "elo": card_data.get('score', ""),
        "we": round(float(ladder_stats.get('pri_avg', "0")), 1),
        "rating": round(float(ladder_stats.get('pw_rating_avg', "0")), 2),
        "matchcount": ladder_stats.get('match_count', ""),
        "winrate": int(float(ladder_stats.get('win_rate', "0")) * 100),
        "headshotrate": round(float(ladder_stats.get('hs_kill_rate', "0")) * 100, 1),
        "adr": int(round(float(ladder_stats.get('adpr', "0")), 0)),
        "kills": ladder_stats.get('kill_num', "0"),
        "deaths": ladder_stats.get('death_num', "1"),  # default to 1 to avoid division by zero
        "rws": round(float(ladder_stats.get('rws_avg', "0")), 2)
    }

    logger.info(user)

    # Calculate up/down status for metrics
    user["weupordown"], user["weupordownimg"], user["wecolor"] = get_change_status(ladder_stats.get('pri_avg_change', 0))
    user["ratingupordown"], user["ratingupordownimg"], user["ratingcolor"] = get_change_status(ladder_stats.get('pw_rating_avg_change', 0))
    user["winrateupordown"], user["winrateupordownimg"], _ = get_change_status(ladder_stats.get('win_rate_change', 0))
    user["headshotrateupordown"], user["headshotrateupordownimg"], _ = get_change_status(ladder_stats.get('hs_kill_rate_change', 0))
    user["adrupordown"], user["adrupordownimg"], _ = get_change_status(ladder_stats.get('adpr_change', 0))
    user["rwsupordown"], user["rwsupordownimg"], _ = get_change_status(ladder_stats.get('rws_avg_change', 0))

    # Generate progress circles
    user["weprogress"] = generate_progress_circle(float(user["we"]), 16)
    user["ratingprogress"] = generate_progress_circle(float(user["rating"]), 2)

    # Calculate K/D ratio
    user["kd"] = round(float(user["kills"]) / int(user["deaths"]), 2)

    # Color settings based on thresholds
    user["headshotratecolor"] = get_color(
        user["headshotrate"], [50, 30, 0], ["green", "", "red"]
    )
    user["winratecolor"] = get_color(
        user["winrate"], [50, 40, 0], ["green", "", "red"]
    )
    user["adrcolor"] = get_color(
        user["adr"], [100, 70, 0], ["green", "", "red"]
    )
    user["kdcolor"] = get_color(
        user["kd"], [1, 0.8, 0], ["green", "", "red"]
    )
    user["rwscolor"] = get_color(
        user["rws"], [12, 8, 0], ["green", "", "red"]
    )


    rankimg =  io.BytesIO()
    create_hexagon_image(200, float(int(user['elo'])%200) / 200,calculate_grade(int(user['elo'])),'resources/fonts/CS.ttf').save(rankimg, format='PNG')
    rankimg = rankimg.getvalue()
    user["eloimg"] = f"data:image/png;base64,{base64.b64encode(rankimg).decode('utf-8')}"

    current_dir = Path(__file__).parent

    # 加载模板
    env = Environment(loader=FileSystemLoader(current_dir))
    html_path = current_dir / generate_hex_filename()
    template = env.get_template("temp.html")

    # 渲染模板并传入参数
    html_output = template.render(user=user)
    save_html(html_output, html_path)

    async with get_new_page(viewport={"width": 984, "height": 298}) as page:
        picture = await take_screenshot(page, html_path)
    await UniMessage.at(event.get_user_id()).image(raw=picture).text("\n绑定成功!").finish()

wanmeisearch = on_command("搜索完美用户", aliases={}, block=True, priority=4)

@wanmeisearch.handle()
async def wanmeisearch_handler(matcher: Matcher, event: Event, arg: Message = CommandArg()):
    name = arg.extract_plain_text().strip()
    if not name:
        await UniMessage.at(event.get_user_id()).text("\n请输入要查找的用户名！\n\n或使用指令 帮助 来获取更多信息").finish()

    user_info = await search_user(name)

    if "error" in user_info:
        await UniMessage.at(event.get_user_id()).text(user_info['error']).finish()
    else:
        msg = "\n"
        for user in user_info['data']['users']:
            avatar_url = user['avatar']
            username = user['nickname']
            domain = user['steam_id']
            msg += f"\n用户名: {username}\nSteam ID: {domain}\n---------------"
        await UniMessage.at(event.get_user_id()).text(msg).finish()