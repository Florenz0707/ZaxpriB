from nonebot import on_command
from nonebot.adapters import Event, Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot_plugin_alconna import UniMessage
from .api_requests import download_image
from .database import init_db, add_server_address, get_server_addresses, delete_server_address
import a2s
import re
import time
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
__plugin_meta__ = PluginMetadata(
    name="起源服务器查询",
    description="用于查询起源服务器状态，或是添加群聊服务器",
    usage="示例: 查服 地址:端口 或 添加服务器 地址:端口 或 删除服务器 地址:端口 或 群服务器",
    type="application",
    extra={},
)
init_db()
def parse_address_port(text):
    # 使用正则表达式解析地址和端口
    pattern = r'^(?P<address>[a-zA-Z0-9.-]+):(?P<port>\d+)$'
    match = re.match(pattern, text)
    
    if match:
        address = match.group('address')
        port = int(match.group('port'))
        if port == None:
            port = 27015
        return address, port
    else:
        return None, None

# 注册命令
server_query = on_command("查服", aliases={}, block=True, priority=17)

@server_query.handle()
async def _(event: Event, matcher: Matcher, arg: Message = CommandArg()):
    # 获取服务器地址和端口
    server_string_address = arg.extract_plain_text().strip()
    address, port = parse_address_port(server_string_address)
    
    if address is None or port is None:
        await UniMessage.text("\n请输入正确的服务器地址！").finish(reply_to=True)
    
    server_address = (address, port)
    
    # 获取服务器信息
    try:
        # 计算 ping
        start_time = time.time()
        info = a2s.info(server_address)
        end_time = time.time()
        players = a2s.players(server_address)
        ping = int((end_time - start_time) * 1000)  # 转换为毫秒
        
        # 下载图片
        pic = await download_image("https://t.alcy.cc/moe")
        
        # 格式化信息
        msg = UniMessage.image(raw=pic)
        msg += UniMessage.text(
            f"\n———————————————\n"
            f"服务器名称：{info.server_name}\n"
            f"服务器人数：{info.player_count}/{info.max_players}\n"
            f"当前地图：{info.map_name}\n"
            f"———————————————\n"
            f"分数 | 玩家 | 时间\n"
        )
        
        # 添加玩家信息
        for player in players:
            msg += UniMessage.text(
                f"({player.score}) {player.name}  {int(player.duration // 3600):02}:{int((player.duration % 3600) // 60):02}:{int(player.duration % 60):02}\n"
            )
        
        msg += UniMessage.text("———————————————")
        
        await msg.send()
    except Exception as e:
        await UniMessage.text(f"\n服务器查询失败，报错信息: {e}").finish(reply_to=True)

save_server = on_command("添加服务器", aliases={}, block=True, priority=17)

@save_server.handle()
async def _(event: Event, matcher: Matcher, arg: Message = CommandArg()):
    group_id = getattr(event, 'group_id', None)
    address,port = parse_address_port(arg.extract_plain_text().strip())
    if address is None or port is None:
        await UniMessage.text("\n请输入正确的服务器地址！").finish(reply_to=True)
    add_server_address(group_id=group_id, address=arg.extract_plain_text().strip())

    server_address = (address, port)
    
    # 获取服务器信息
    try:
        # 计算 ping
        start_time = time.time()
        info = a2s.info(server_address)
        end_time = time.time()
        players = a2s.players(server_address)
        ping = int((end_time - start_time) * 1000)  # 转换为毫秒
        
        # 下载图片
        pic = await download_image("https://t.alcy.cc/moe")
        
        # 格式化信息
        msg = UniMessage.at(event.get_user_id()).image(raw=pic).text(f"服务器添加成功！\n")
        msg += UniMessage.text(
            f"\n———————————————\n"
            f"服务器地址：{arg.extract_plain_text().strip()}\n"
            f"服务器名称：{info.server_name}\n"
            f"服务器人数：{info.player_count}/{info.max_players}\n"
            f"当前地图：{info.map_name}\n"
            f"———————————————\n"
            f"分数 | 玩家 | 时间\n"
        )
        
        # 添加玩家信息
        for player in players:
            msg += UniMessage.text(
                f"({player.score}) {player.name}  {int(player.duration // 3600):02}:{int((player.duration % 3600) // 60):02}:{int(player.duration % 60):02}\n"
            )
        
        msg += UniMessage.text("———————————————")
        
        await msg.send()
    except Exception as e:
        await UniMessage.text(f"\n服务器查询失败，报错信息: {e}").finish(reply_to=True)

delete_server = on_command("删除服务器", aliases={}, block=True, priority=17)

@delete_server.handle()
async def _(event: Event, matcher: Matcher, arg: Message = CommandArg()):
    group_id = getattr(event, 'group_id', None)
    address,port = parse_address_port(arg.extract_plain_text().strip())
    if address is None or port is None:
        await UniMessage.at(event.get_user_id()).text("\n请输入正确的服务器地址！").finish(reply_to=True)
    status = delete_server_address(group_id=group_id, address=arg.extract_plain_text().strip() )
    if status:
        await UniMessage.at(event.get_user_id()).text(f"\n服务器删除成功！").finish(reply_to=True)
    else:
        await UniMessage.at(event.get_user_id()).text(f"\n服务器删除失败！").finish(reply_to=True)

query_server_list = on_command("群服务器", aliases={}, block=True, priority=17)

@query_server_list.handle()
async def _(event: Event, matcher: Matcher, arg: Message = CommandArg()):
    group_id = getattr(event, 'group_id', None)
    server_lists = get_server_addresses(group_id)
    for server in server_lists:
        logger.info(server)
        address,port = parse_address_port(server)

        server_address = (address, port)
        
        # 获取服务器信息
        try:
            # 计算 ping
            start_time = time.time()
            info = a2s.info(server_address)
            end_time = time.time()
            players = a2s.players(server_address)
            ping = int((end_time - start_time) * 1000)  # 转换为毫秒
            
            # 下载图片
            pic = await download_image("https://t.alcy.cc/moe")
            msg = UniMessage.at(event.get_user_id()).image(raw=pic)
            # 格式化信息
            msg += UniMessage.text(
                f"\n———————————————\n"
                f"服务器地址：{server}\n"
                f"服务器名称：{info.server_name}\n"
                f"服务器人数：{info.player_count}/{info.max_players}\n"
                f"当前地图：{info.map_name}\n"
                f"———————————————\n"
                f"分数 | 玩家 | 时间\n"
            )
            
            # 添加玩家信息
            for player in players:
                msg += UniMessage.text(
                    f"({player.score}) {player.name}  {int(player.duration // 3600):02}:{int((player.duration % 3600) // 60):02}:{int(player.duration % 60):02}\n"
                )
            
            msg += UniMessage.text("———————————————\n")
            msg += UniMessage.text(f"连接指令: connect {server}\n")
            await msg.send()
        except Exception as e:
            await UniMessage.at(event.get_user_id()).text(f"\n服务器查询失败，报错信息: {e}").finish(reply_to=True)
