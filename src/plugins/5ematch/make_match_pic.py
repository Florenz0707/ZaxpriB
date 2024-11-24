from .api_requests import get_match_list, get_user_info, get_dress_info
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from nonebot import require
from nonebot.log import logger
require("nonebot_plugin_htmlrender")
from nonebot_plugin_htmlrender import get_new_page
import uuid
import os
from datetime import datetime
from .database import bind_match

def timestamp_to_datetime(timestamp) -> str:
    """
    将秒时间戳转换为年-月-日 时:分的格式。

    :param timestamp: 秒时间戳
    :return: 格式化的日期时间字符串
    """
    dt = datetime.fromtimestamp(int(timestamp))
    formatted_date = dt.strftime("%m-%d %H:%M")
    return formatted_date

async def take_screenshot(page, file_path):
    await page.goto(f"file://{file_path}", wait_until="domcontentloaded")
    await page.wait_for_timeout(500)
    pic = await page.screenshot(full_page=True)
    os.remove(file_path)
    return pic

def generate_hex_filename():
    return f"{uuid.uuid4().hex}.html"

def save_html(rendered_html: str, filename: str):
    # 将 HTML 保存至指定文件路径
    output_path = Path(__file__).parent / filename
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    logger.info(f"HTML saved to {output_path}")

async def format_user_data(user_info, dress_info, base_img_url):
    user_data = user_info.get("data", {}).get("header", {}).get("user_data", {})
    disguise_data = user_info.get("data", {}).get("disguise", {})
    plus_data = user_info.get("data", {}).get("plus", {})
    dress_card_data = dress_info.get("data", {}).get("card", {})
    dress_box_data = dress_info.get("data", {}).get("avatarBox", {})

    user = {
        "name": user_data.get("username", "未知用户"),
        "avatar_img_url": base_img_url + user_data.get("avatar_url", ""),  # 用户头像链接
        "certify_status": int(user_data.get("certify_status", 0)),  # 受信账户状态
        "is_plus": int(plus_data.get("is_plus", 0)),  # VIP 状态
        "plus_img_url": base_img_url + plus_data.get("plus_icon_short", ""),  # VIP 图标链接
        "frame_img_type": disguise_data.get("dressBoxId", ""),  # 头像框类型
        "background_img_type": disguise_data.get("dressCardId", ""),  # 背景类型
    }

    # 用户名样式
    if user["is_plus"]:
        user["name"] = f'<p class="gold___tX5S9">{user["name"]}</p>'
        user["plus"] = ""  # VIP 用户不需要 noColor 样式
    else:
        user["name"] = f'<p>{user["name"]}</p>'
        user["plus"] = " noColor___W5rhn"

    # 认证图标
    user["certify"] = (
        '<img src="https://oss-arena.5eplay.com/ya_static/images/userInfo/shouxinrenzheng.png" '
        'alt="" class="shouxinrenzheng___hpk3O">' if user["certify_status"] == 1 else ""
    )

    # 背景图片
    user["background_img_url"] = (
        base_img_url + dress_card_data.get(str(user["background_img_type"]), {}).get("user_info_image_url", "")
        if user["background_img_type"]
        else "https://arena-next.5eplaycdn.com/static/js/../../static/morens.71c8a70b.png"
    )
    user["background_img_url"] = f'&quot;{user["background_img_url"]}&quot;'
    
    # 头像框图片
    user["frame_img_url"] = (
        f'<img class="position-center" src="{base_img_url + dress_box_data.get(str(user["frame_img_type"]), {}).get("iconLogoUrl", "")}" '
        'width="140" height="140" style="z-index: 10;">'
        if user["frame_img_type"]
        else ""
    )

    return user


def format_match_list(match_list):
    match_list = match_list.get("data", {})
    return_match = []
    gamemode_dict = {
        "103": {"type": "优先排位", "match_color": "priorityBox___JzC8F"},
        "1812": {"type": "1v1约战", "match_color": "league___mdIQW"},
        "30": {"type": "全民联赛", "match_color": "league___mdIQW"},
        "1811": {"type": "1v1约战", "match_color": "league___mdIQW"},
    }

    for match in match_list:
        # 基础信息
        temp = {
            "id": match["match_id"],  # 添加 match ID
            "date": timestamp_to_datetime(match["start_time"]),
            "mapname": match["map_name"],
            "kills": match["kill"],
            "score1": match["group1_all_score"],
            "score2": match["group2_all_score"],
            "rating": match["rating"],
            "rws": match["rws"],
        }

        # 比赛类型和颜色
        gamemode_info = gamemode_dict.get(match["game_mode"], {"type": "未知比赛类型", "match_color": "league___mdIQW"})
        temp["type"] = gamemode_info["type"]
        temp["match_color"] = gamemode_info["match_color"]

        # 胜负状态
        if match["is_win"]:
            temp["result"] = "胜"
            temp["match_status"] = "winIcon___lmvRU"
        elif match["is_tie"]:
            temp["result"] = "平"
            temp["match_status"] = "tieIcon___fhp9z"
        else:
            temp["result"] = "负"
            temp["match_status"] = "lossIcon___kKKup"

        # 评分状态
        temp["rating_status"] = "true" if float(temp["rating"]) > 1 else "false"

        # ELO 值及相关信息
        elo = int(float(match["origin_elo"]) + float(match["change_elo"]))
        temp["left_elo"] = str(elo // 100)
        temp["right_elo"] = str(elo % 100).zfill(2)
        def get_elo_color(elo: int) -> str:
            if elo >= 28 and elo < 30:
                return "255, 231, 95"
            elif elo >= 25 and elo < 28:
                return "255, 127, 126"
            elif elo >= 20 and elo < 25: 
                return "213, 144, 255"
            elif elo >= 15 and elo < 20:
                return "179, 136, 255"
            elif elo >= 10 and elo < 15:
                return "150, 185, 255"
            elif elo < 10:
                return "135, 171, 226"
        
        def get_elo_bg(elo: int) -> str:
            if elo >= 28 and elo < 30:
                return "120"
            elif elo >= 25 and elo < 28:
                return "114"
            elif elo >= 23 and elo < 25:
                return "112"
            elif elo >= 20 and elo < 23: 
                return "110"
            elif elo >= 15 and elo < 20:
                return "109"
            elif elo >= 10 and elo < 15:
                return "105"
            elif elo < 10:
                return "103"
        temp["left_elo_rgb"] = get_elo_color(int(temp["left_elo"]))  # 默认颜色 (可根据需求动态生成)
        temp["right_elo_rgb"] = get_elo_color(int(temp["left_elo"]))  # 默认颜色 (可根据需求动态生成)
        elo_bg = get_elo_bg(int(temp["left_elo"]))
        temp["elo_background"] = f"https://oss-arena.5eplay.com/ya_static/images/common/level_elo2/{elo_bg}.png"  # 需要替换为真实路径
        temp["elo_img"] = f'<div class="flex-horizontal flex-justify-cneter flex-align-center" style="height: 100%; position: relative;"><span class="noUnderline___mYnP0 noScale___qj8gQ flex-align-center"><div><div class="ya-levelelo" style="width: 80px; height: 53.3333px;"><div class="ya-fonts" style="transform: translate(-50%, -50%) scale(0.8); align-items: baseline;"><span class="bigspan" style="color: rgb({temp["left_elo_rgb"]});">{temp["left_elo"]}</span><span style="color: rgb({temp["right_elo_rgb"]});">{temp["right_elo"]}</span></div><img src="{temp["elo_background"]}" alt=""></div></div></span><div class="challenge_status_icon"></div></div>'
        temp["id"] =  bind_match(temp["id"])

        #特殊处理
        if match["game_mode"] != "103" and match["game_mode"] != "30":
            temp["rating"] = "--"
            temp["rws"] = "--"
            temp["elo_img"] = "--"

        # 成就信息
        achievements = []
        if match["is_mvp"]:
            achievements.append('<i class="prizeIcon___RN0Z_ icon___lXHK1 most-mvp___fsqCD" title="MVP"></i>')
        if match["is_most_headshot"]:
            achievements.append('<i class="prizeIcon___RN0Z_ icon___lXHK1 most-headshot___oD0tp" title="枪法之最"></i>')
        if match["is_most_first_kill"]:
            achievements.append('<i class="prizeIcon___RN0Z_ icon___lXHK1 most-first-kill___x62cE" title="突破之最"></i>')
        if match["is_most_end"]:
            achievements.append('<i class="prizeIcon___RN0Z_ icon___lXHK1 most-end___qQ5PD" title="残局之最"></i>')
        temp["achievements"] = "".join(achievements)

        #特殊处理
        return_match.append(temp)

    return return_match


async def make_match_pic(uuid: str):
    base_img_url = "https://oss-arena.5eplay.com/"

    # 获取用户信息和比赛列表
    user_info = await get_user_info(uuid)
    match_list = await get_match_list(uuid)
    if "error" in user_info or "error" in match_list:
        return {"error": "\n获取数据失败..."}

    # 获取装扮信息
    dress_info = await get_dress_info()

    # 格式化数据
    user = await format_user_data(user_info, dress_info, base_img_url)
    match_list = format_match_list(match_list)
    logger.info(f"比赛数据长度:{len(match_list)}")
    # 设置当前目录
    current_dir = Path(__file__).parent

    # 加载模板
    env = Environment(loader=FileSystemLoader(current_dir))
    html_path = current_dir / generate_hex_filename()
    template = env.get_template("layout.html")

    # 渲染模板并传入参数
    html_output = template.render(user=user,matches=match_list)
    save_html(html_output, html_path)

    # 截图
    async with get_new_page(viewport={"width": 1200, "height": 559 + len(match_list)*55}) as page:
        picture = await take_screenshot(page, html_path)

    return picture