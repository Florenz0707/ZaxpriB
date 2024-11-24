
import logging
import datetime
from .match_images import get_images
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from collections import defaultdict
from .api_requests import download_image,get_card_info,get_match_info
from .grade_image_processing import create_hexagon_image
import base64
import io
# 初始化日志
import uuid

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
    
def assign_marks(members):
    # 初始化每个阵营的标记字典
    camp_team_count = defaultdict(lambda: defaultdict(list))
    
    # 统计每个阵营中不同 team_id 下的人数
    for member in members:
        camp_team_count[member['camp']][member['team_id']].append(member)
    
    # 结果标记
    result = []
    
    # 为每个阵营分配标记
    for camp, teams in camp_team_count.items():
        # 按人数从多到少排序 team_id
        sorted_teams = sorted(teams.items(), key=lambda x: len(x[1]), reverse=True)
        
        # 标记分配
        mark_assignment = {}
        # 优先处理人数情况
        group_count = sum(1 for _, members_list in sorted_teams if len(members_list) > 1)
        
        if group_count >= 2:
            # 分配标记给人数最多的两个组队，其余单人组分配3号标记
            mark_assignment[sorted_teams[0][0]] = 1
            mark_assignment[sorted_teams[1][0]] = 2
            for team_id, members_list in sorted_teams[2:]:
                mark_assignment[team_id] = 3
        elif group_count == 1:
            # 只有一个多人的组队，分配1号，其他单人分配3号
            mark_assignment[sorted_teams[0][0]] = 1
            for team_id, members_list in sorted_teams[1:]:
                mark_assignment[team_id] = 3
        else:
            # 全是单人队伍，全部标记为3
            for team_id, members_list in sorted_teams:
                mark_assignment[team_id] = 3

        # 分配标记给每个成员
        for team_id, members_list in teams.items():
            mark = mark_assignment.get(team_id, 3)
            for member in members_list:
                result.append({**member, "mark": mark})
    
    return result
def save_html(rendered_html: str, filename: str):
    # 将 HTML 保存至指定文件路径
    output_path = Path(__file__).parent / filename
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    print(f"HTML saved to {output_path}")

def get_match_type_image(match_type, is_green):
    if match_type == "12":
        return get_images("green_elo" if is_green == "1" else "normal_elo")
    return get_images({"41": "official", "27": "weekend"}.get(match_type, ""))

def get_map_name_cn(map_name):
    maps = {
        'dust2': "炙热沙城II", 'mirage': "荒漠迷城", 'nuke': "核子危机",
        'inferno': "炼狱小镇", 'overpass': "死亡游乐园", 'vertigo': "殒命大厦",
        'ancient': "远古遗迹", 'anubis': "阿努比斯", 'mills': "风情磨坊",
        'thera': "假日锡拉"
    }
    for key, name in maps.items():
        if key in map_name:
            return name
    return "未知地图"

def get_zone_name(zone_id):
    zones = {
        "601": "北方", "604": "华东", "612": "华东", 
        "605": "南方", "609": "南方", "603": "西南", "611": "北京"
    }
    return zones.get(zone_id, "未知")


import asyncio
#is-me-back -> {{team1.isme5}}
async def get_match_info_data(match_id:str,my_steam_id:str):
    result = await get_match_info(match_id)
    match_info = {
            'win_team_id': result.get('data',{}).get('report', {}).get('win_team_id',''),
            'lose_team_id': result.get('data',{}).get('report', {}).get('lose_team_id',''),
            'match_id': result.get('data',{}).get('report', {}).get('match_id',''),
            'zone_id': get_zone_name(result.get('data',{}).get('report', {}).get('zone_id','')),#https://gwapi.pwesports.cn/pvparc/arc/csgo/regionList服务器列表,zoneid是服务器地区
            #611北京，612华东，604华东，605南方，603西南，609南方，601北方
            'match_end_time': datetime.datetime.fromtimestamp(int(result.get('data',{}).get('report', {}).get('match_endtime','')) / 1000.0).strftime("%Y-%m-%d %H:%M:%S"),#比赛日期
            'team1_score': result.get('data',{}).get('report', {}).get('ct_win_times',''),#
            'team2_score': result.get('data',{}).get('report', {}).get('t_win_times',''),
            'is_green': result.get('data',{}).get('report', {}).get('is_green',''),#是否为天梯绿色比赛
            'match_type': result.get('data',{}).get('report', {}).get('match_type',''),#12为天梯，41为官匹pro，27为周末联赛
            'win_team': result.get('data',{}).get('report', {}).get('win_camp','1'),
            'map_name_cn':get_map_name_cn(result.get('data',{}).get('report', {}).get('map', 'de_dust2'))
        }
    
    match_info['match_type_img'] = get_match_type_image(match_info['match_type'], match_info['is_green'])


    
    #比赛数据解析
    team1, team2 = (
    {"iswin": False, "score": f""},
    {"iswin": False, "score": f""}
)
    if result['data']['report']['win_camp'] == "3":
        team1['iswin'] = True
        team1['scorecolor'] = "score-ind f40 pt8 ctb"
        team2['scorecolor'] = "score-ind f40 pb8 tb"
        team1['score'] = f"{max(int(result['data']['report']['t_win_times']),int(result['data']['report']['ct_win_times'])):02d}"
        team2['score'] = f"{min(int(result['data']['report']['t_win_times']),int(result['data']['report']['ct_win_times'])):02d}"
    elif result['data']['report']['win_camp'] == "2":
        team2['iswin'] = True
        team1['scorecolor'] = "score-ind f40 pt8 tb"
        team2['scorecolor'] = "score-ind f40 pb8 ctb"
        team2['score'] = f"{max(int(result['data']['report']['t_win_times']),int(result['data']['report']['ct_win_times'])):02d}"
        team1['score'] = f"{min(int(result['data']['report']['t_win_times']),int(result['data']['report']['ct_win_times'])):02d}"
    else:
        team1['scorecolor'] = "score-ind f40 pt8 def"
        team2['scorecolor'] = "score-ind f40 pb8 def"
        team2['score'] = f"{max(int(result['data']['report']['t_win_times']),int(result['data']['report']['ct_win_times'])):02d}"
        team1['score'] = f"{min(int(result['data']['report']['t_win_times']),int(result['data']['report']['ct_win_times'])):02d}"
        result["data"]["report"]["win_camp"] = "3"
    
    #获取背景图
    pic = await download_image("https://t.alcy.cc/moe")
    # 玩家排序并分组
    players = result["data"]["report"]["players"]
    sorted_players = assign_marks(players)
    sorted_players = sorted(sorted_players, key=lambda x: -float(x["pri"]))
    # 分配玩家到 team1 或 team2
    for idx, player in enumerate(sorted_players):
        if "3" == result["data"]["report"]["win_camp"]:
            if player["camp"] == result["data"]["report"]["win_camp"]:
                team_info = team1
            else:
                team_info = team2
        elif "2" == result["data"]["report"]["win_camp"]:
            if player["camp"] == result["data"]["report"]["win_camp"]:
                team_info = team2
            else:
                team_info = team1
        team_key = "player" + str(len(team_info) - 2)  # player1, player2, ...


        #获取玩家信息
        card_info = await get_card_info(player["user_id"])
        # 添加玩家信息
        rankimg =  io.BytesIO()
        if match_info["match_type"] == "41":
            player['mm_score'] = "0"
        create_hexagon_image(200, float(int(player['mm_score'])%200) / 200,calculate_grade(int(player['mm_score'])),'resources/fonts/CS.ttf').save(rankimg, format='PNG')
        rankimg = rankimg.getvalue()
        team_info[team_key] = {
            "mark": f"team-{player['mark']}",
            "nickname": player["steam_nick"],
            "we": str(round(float(player["pri"]), 1)),
            "isme": "",
            "avatar_url": card_info.get('data', {}).get('card_info', '').get('avatar', ''),
            "isgreen": "",
            "kda": f"{player['kill']}/{player['death']}/{player['assist']}",
            "headshot": f"{int(float(player['headshot_kill_count']) / max(1, int(player['kill'])) * 100)}%",
            "first_kill": player["first_kill"],
            "twomorekills": str(sum(int(player[kill_type]) for kill_type in ['two_kill', 'three_kill', 'four_kill', 'five_kill'])),
            "onevmorecount": str(sum(int(player[kill_type]) for kill_type in ['1v1', '1v2', '1v3', '1v4', '1v5'])),
            "adr": str(int(int(player['dmg_health']) / max(1, int(match_info['team1_score']) + int(match_info['team2_score'])))),
            "rws": str(round(float(player['rws']), 2)),
            "rating": player['pw_rating'],
            "rankimg": f"data:image/png;base64,{base64.b64encode(rankimg).decode('utf-8')}"
        }
        if card_info.get('data',{}).get('card_info','').get('is_green','') == 1:
            if card_info.get('data',{}).get('card_info','').get('isVip','') == True:
                team_info[team_key]["isgreen"] = get_images("green_vip_player")
            else:
                team_info[team_key]["isgreen"] = get_images("green_player")
        else:
            if card_info.get('data',{}).get('card_info','').get('isVip','') == True:
                team_info[team_key]["isgreen"] = get_images("vip_player")
            else:
                team_info[team_key]["isgreen"] = ""
                
        if float(team_info[team_key]['rating']) > 1.00:
            team_info[team_key]['ratingcolor'] = "color: rgb(0, 182, 146);"
        else:
            team_info[team_key]['ratingcolor'] = "color: rgb(223, 1, 64);"
        if float(team_info[team_key]['we']) > 8.00:
            team_info[team_key]['wecolor'] = "pril win"
        else:
            team_info[team_key]['wecolor'] = "pril loss"

        if player["user_id"] == my_steam_id:
            team_info[team_key]["isme"] = "is-me-back"

    # 解析 JSON 数据
    scores = result["data"]["report"]["results"]

    # 初始化半场比分
    half_scores = []
    current_half_scores = {"2": 0, "3": 0}

    # 遍历每一轮次
    for results1 in scores:
        win_camp = results1["win_camp"]
        half_match_type = results1["half_match_type"]
        
        # 更新当前半场的比分
        current_half_scores[win_camp] += 1
        
        # 如果是半场结束，记录当前半场的比分并重置计数器
        if half_match_type == "1":
            half_scores.append(current_half_scores.copy())
            current_half_scores = {"2": 0, "3": 0}
    half_scores.append(current_half_scores)
    # 记录最后一个半场的比分
    team2["score1"] = str(half_scores[0]["3"]).zfill(2)
    team2["score2"] = str(half_scores[1]["2"]).zfill(2)
    team1["score1"] = str(half_scores[0]["2"]).zfill(2)
    team1["score2"] = str(half_scores[1]["3"]).zfill(2)
    # 获取当前文件所在目录
    current_dir = Path(__file__).parent

    # 加载模板
    env = Environment(loader=FileSystemLoader(current_dir))
    html_path = current_dir / generate_hex_filename()
    template = env.get_template("layout.html")

    # 渲染模板并传入参数
    html_output = template.render(match_info=match_info,team1=team1,team2=team2,bakcground_base64=pic)
    
    # 保存渲染后的 HTML
    save_html(html_output, html_path)
    return html_path
