import httpx
from nonebot.log import logger
import nonebot
config = nonebot.get_driver().config
async def search_user(id: str) -> dict:
    url = "https://app.5eplay.com/api/csgo/data/search"
    params = {
        'keywords': id,
        'page': "1"
    }
    headers = {
        'User-Agent': "okhttp/4.10.0",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'token': config.fiveetoken
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            logger.info(response.json())
            if not response.json().get('data', {}).get('list', []):
                return {"error": "未找到该用户！"}
            return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {str(e)}")
        return {"error": "Failed to fetch data"}
    except Exception as e:
        logger.error(f"Error fetching user info: {str(e)}")
        return {"error": str(e)}
    
async def get_uuid(domain: str) -> dict:
    url = f"https://app.5eplay.com/api/csgo/friend/check_friend/{domain}"
    headers = {
        'User-Agent': "okhttp/4.10.0",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'token': config.fiveetoken
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            logger.info(response.json())
            return response.json()["data"]["uuid"]
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {str(e)}")
        return {"error": "Failed to fetch data"}
    except Exception as e:
        logger.error(f"Error fetching friend status: {str(e)}")
        return {"error": str(e)}
async def info_5e(id: str) -> dict:
    params = {
        'domain': id
    }
    
    headers = {
        'User-Agent': "okhttp/3.14.9",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'mobileModel': "{\"systemName\":\"Android\",\"mobileFactory\":\"Xiaomi\",\"platform\":\"23049RAD8C\",\"systermVersion\":\"13\"}",
        'version': "6.2.1",
        'equipment': "android",
        'channel': "xiaomi",
        'dispmod': "1",
        'school': "false",
        'games': ""
    }
    
    try:
        # 第一次请求：获取比赛记录
        async with httpx.AsyncClient() as client:
            response = await client.get("https://ya-api-app.5eplay.com/v0/mars/api/csgo/data/common_match", params=params, headers=headers)
            response.raise_for_status()
            response_data = response.json()  # 将响应转换为 JSON 格式
            logger.info(response_data)

        # 检查返回的 errcode 字段
        if response_data.get("errcode") != 0:
            return {"error": "未查找到用户的比赛记录！"}

        # 获取年份和赛季信息
        year = str(response_data['data']['season_data'][0]['year'])
        season = str(response_data['data']['season_data'][0]['season'])
        #https://ya-api-app.5eplay.com/v0/mars/api/csgo/data/player_home/
        # 获取用户的 avatar_url 和 username

        async with httpx.AsyncClient() as client:
            user_response = await client.get(f"https://ya-api-app.5eplay.com/v0/mars/api/csgo/data/player_home/{id}", params=params, headers=headers)
            user_response.raise_for_status()
            user_response_data = user_response.json()  # 将响应转换为 JSON 格式

            logger.info(user_response_data)

        avatar_url = user_response_data['data']['user']['avatar_url']
        username = user_response_data['data']['user']['username']

        logger.info(avatar_url)
        logger.info(username)

        # 第二次请求：获取用户的比赛信息
        params = {
            'year': year,
            'season': season,
            'matchType': '9'
        }
        async with httpx.AsyncClient() as client:
            userinfo_response = await client.get(f"https://ya-api-app.5eplay.com/v0/mars/api/csgo/data/player_match_v1/{id}", params=params, headers=headers)
            userinfo_response.raise_for_status()
            userinfo_data = userinfo_response.json()  # 将响应转换为 JSON 格式

        # 将 avatar_url 和 username 添加到 userinfo_data
        userinfo_data['data']['user'] = {}
        userinfo_data['data']['user']['avatar_url'] = avatar_url
        userinfo_data['data']['user']['username'] = username
        logger.info(userinfo_data)
        
        return userinfo_data

    except httpx.HTTPStatusError:
        logger.error(f"Failed to fetch match data")
        return {"error": "Failed to fetch match data"}
    except Exception as e:
        logger.error(f"Error fetching match data: {str(e)}")
        return {"error": str(e)}