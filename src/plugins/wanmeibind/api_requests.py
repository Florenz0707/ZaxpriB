import httpx
import json
from nonebot.log import logger

async def search_user(id: str) -> dict:
    headers = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) perfectworldarena/1.0.24092611 Chrome/80.0.3987.163 Electron/8.5.5 Safari/537.36",
    'sec-fetch-site': "none",
    'sec-fetch-mode': "no-cors",
    'accept-language': "zh-CN",
    }
    data = json.dumps({"keyword": id,"page": 1})

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("https://pwaweblogin.wmpvp.com/api-user/search", headers=headers, data=data)
            response.raise_for_status()
            if len(response.json()['data']['users']) == 0:
                return {"error": "未找到该用户！"}
            return response.json()
    except httpx.HTTPStatusError:
        return {"error": "Failed to fetch data"}
    except Exception as e:
        return {"error": str(e)}

async def info_wm(id: str) -> dict:
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.82",
        "device": "undefined",
        "platform": "h5_web",
    }
    data = json.dumps({"steamId64": id, "csgoSeasonId": ""})

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.wmpvp.com/api/v2/csgo/pvpDetailDataStats", headers=headers, data=data)
            response.raise_for_status()
            if response.json()["statusCode"] != 200:
                return response.json()
            return {"error": "未查找到用户的比赛记录！"}
    except httpx.HTTPStatusError:
        return {"error": "Failed to fetch data"}
    except Exception as e:
        return {"error": str(e)}
    
async def download_image(url: str):
    """直接下载并返回图片的字节数据"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=15.0)
            response.raise_for_status()
            return response.content  # 直接返回图片的字节数据
    except httpx.HTTPStatusError:
        return None
    except Exception as e:
        logger.error(f"Error downloading image: {str(e)}")
        return None
    
async def get_card_info(uid: str) -> dict:
    url = "https://pwaweblogin.wmpvp.com/api-user/card"
    
    # 请求的参数和 headers
    params = {
        'uid': uid
    }
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) perfectworldarena/1.0.24110811 Chrome/80.0.3987.163 Electron/8.5.5 Safari/537.36",
        'sec-fetch-site': "none",
        'sec-fetch-mode': "no-cors",
        'accept-language': "zh-CN",
        'Cookie': "path=/; HttpOnly; Max-Age=1800"
    }

    try:
        # 发送异步 GET 请求
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()  # 检查状态码，非 200 会触发异常
            
            # 解析 JSON 响应
            data = response.json()
            # logger.info(data)  # 记录返回的 JSON 数据
            
            # 检查返回的数据是否符合预期
            if not data.get('data'):
                return {"error": "未找到用户信息！"}
            
            return data

    except httpx.HTTPStatusError as e:
        # logger.error(f"HTTP 请求失败: {e.response.status_code}")  # 记录请求失败的情况
        return {"error": f"HTTP 请求失败: {e.response.status_code}"}
    except Exception as e:
        # logger.error(f"获取用户信息时出错: {str(e)}")  # 记录一般错误
        return {"error": str(e)}