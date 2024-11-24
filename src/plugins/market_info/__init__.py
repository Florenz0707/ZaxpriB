from nonebot import require
require("nonebot_plugin_htmlrender")
from nonebot_plugin_htmlrender import (
    template_to_pic,
    get_new_page,
    html_to_pic
)
import uuid
from nonebot import on_command
from nonebot.adapters import Message, Event
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot import require, logger
require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from .databse import query_database
import re
import os
from nonebot.plugin import PluginMetadata
__plugin_meta__ = PluginMetadata(
    name="CS饰品",
    description="可查询饰品大盘数据，饰品详细信息，饰品涨、跌幅等排行榜",
    usage="使用 /帮助 获取更多信息",
    type="application",
    extra={},
)
# 常量定义
MARKETS = ["BUFF", "悠悠有品", "C5", "IGXE"]
RANK_TYPES = ["周涨幅", "周跌幅", "周热销", "周热租"]
TEMPLATE_DIR = Path(__file__).parent / "templates"

def generate_hex_filename():
    return f"{uuid.uuid4().hex}.html"

def fuzzy_case_match(s1: str, s2: str) -> bool:
    """
    模糊大小写匹配函数。
    
    参数:
    s1 (str): 第一个字符串。
    s2 (str): 第二个字符串。
    
    返回:
    bool: 如果忽略大小写后的字符串相等则返回 True，否则返回 False。
    """
    return s1.lower() == s2.lower()

async def take_screenshot(page, file_path):
    await page.goto(f"file://{file_path}", wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    pic = await page.screenshot(full_page=True)
    await UniMessage.image(raw=pic).send(reply_to=True)
    os.remove(file_path)

# CS大盘数据命令
cs_market_info = on_command("CS大盘数据", aliases={"Cs大盘数据", "cS大盘数据", "cs大盘数据"}, block=True)
@cs_market_info.handle()
async def _(matcher: Matcher, event: Event, arg: Message = CommandArg()):
    name = arg.extract_plain_text().strip()
    if name == "":
        await UniMessage.at(event.get_user_id()).text("\n请输入要查询的市场名!\n\n可查询市场：BUFF|悠悠有品|IGXE|C5\n\n示例： CS大盘数据 BUFF").finish(reply_to=True)

    market_type = next((i for i, market in enumerate(MARKETS) if fuzzy_case_match(name, market)), None)
    if market_type is None:
        await UniMessage.at(event.get_user_id()).text("\n请输入正确的市场名!\n\n可查询市场：BUFF|悠悠有品|IGXE|C5\n\n示例： CS大盘数据 BUFF").finish(reply_to=True)

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("markets.html.jinja2")
    rendered_html = template.render(page_now=market_type)
    new_html = generate_hex_filename()
    output_path = TEMPLATE_DIR / new_html
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(rendered_html)

    async with get_new_page(viewport={"width": 500, "height": 300}) as page:
        await take_screenshot(page, output_path)

# 搜索饰品命令
cs_market_search = on_command("搜索饰品", block=True)
@cs_market_search.handle()
async def _(matcher: Matcher, event: Event, arg: Message = CommandArg()):
    name = arg.extract_plain_text().strip()
    if name == "" or len(name) < 2:
        await UniMessage.at(event.get_user_id()).text("请输入要搜索的饰品名称").finish(reply_to=True)

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("search.html.jinja2")
    rendered_html = template.render(data_value=name)
    new_html = generate_hex_filename()
    output_path = TEMPLATE_DIR / new_html
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(rendered_html)

    async with get_new_page(viewport={"width": 500, "height": 300}) as page:
        await take_screenshot(page, output_path)

# 饰品查询命令
cs_goods_search = on_command("饰品查询", aliases={"查询饰品"}, block=True)
@cs_goods_search.handle()
async def _(matcher: Matcher, event: Event, arg: Message = CommandArg()):
    name = arg.extract_plain_text().strip()
    if name == "":
        await UniMessage.at(event.get_user_id()).text("\n请输入要搜索的饰品名称 \n\n可使用 搜索饰品 饰品名 命令查询").finish(reply_to=True)
    elif not name.isdigit():
        await UniMessage.at(event.get_user_id()).text("\n请输入正确的饰品ID \n\n可使用 搜索饰品 饰品名 命令查询").finish(reply_to=True)

    goods_name, goods_hash_name = query_database(int(name))
    if goods_name is None or goods_hash_name is None:
        await UniMessage.at(event.get_user_id()).text("\n未找到该饰品").finish(reply_to=True)

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("item.html.jinja2")
    logger.info(goods_name)
    rendered_html = template.render(data_value=goods_name)
    new_html = generate_hex_filename()
    output_path = TEMPLATE_DIR / new_html
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(rendered_html)

    async with get_new_page(viewport={"width": 750, "height": 900}) as page:
        await take_screenshot(page, output_path)

# 饰品排行命令
cs_goods_rank = on_command("饰品排行", block=True)
def parse_input(input_str):
    pattern = r'^(周涨幅|周跌幅|周热销|周热租)?\s*(\d+)?$'
    match = re.match(pattern, input_str)
    rank_type, page_num = match.groups() if match else ("", 1)
    page_num = int(page_num) if page_num else 1
    return rank_type, page_num

@cs_goods_rank.handle()
async def _(matcher: Matcher, event: Event, arg: Message = CommandArg()):
    name = arg.extract_plain_text().strip()
    if name == "":
        await UniMessage.at(event.get_user_id()).text("\n请输入要查询的排行榜 \n\n可查询排行榜：周涨幅|周跌幅|周热销|周热租\n\n示例： 饰品排行 周涨幅").finish(reply_to=True)

    rank_type_, page_num = parse_input(name)
    if rank_type_ not in RANK_TYPES:
        await UniMessage.at(event.get_user_id()).text("\n请输入正确的排行榜名称！ \n\n可查询排行榜：周涨幅|周跌幅|周热销|周热租\n\n示例： 饰品排行 周涨幅").finish(reply_to=True)

    rank_type_num = RANK_TYPES.index(rank_type_)
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("rank.html.jinja2")
    rendered_html = template.render(rank_type=rank_type_num, page=page_num)
    new_html = generate_hex_filename()
    output_path = TEMPLATE_DIR / new_html
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(rendered_html)

    async with get_new_page(viewport={"width": 650, "height": 900}) as page:
        await take_screenshot(page, output_path)