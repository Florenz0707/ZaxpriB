import httpx
import base64
from nonebot.log import logger
async def download_image(url: str) -> str:
    """下载图片并返回其 Base64 编码，包含数据头"""
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, timeout=15.0)
            response.raise_for_status()
            
            # 获取图片的字节数据
            image_bytes = response.content
            
            # 确定图片的 MIME 类型
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            
            # 将字节数据转换为 Base64 编码
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            # 构建带有数据头的 Base64 字符串
            data_header = f"data:{content_type};base64,"
            base64_with_header = data_header + base64_image
            
            return base64_with_header  # 返回带有数据头的 Base64 编码字符串
    except httpx.HTTPStatusError as http_err:
        logger.error(f"HTTP error downloading image from {url}: {http_err}")
        return None
    except Exception as e:
        logger.error(f"Error downloading image: {str(e)}")
        return None

async def get_match_info(match_id: str) -> dict:
    url = "https://pwaweblogin.wmpvp.com/match-api/report"
    
    # 请求的 payload 和 headers
    payload = {"match_id": match_id}
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) perfectworldarena/1.0.24110811 Chrome/80.0.3987.163 Electron/8.5.5 Safari/537.36",
        'sec-fetch-site': "none",
        'sec-fetch-mode': "no-cors",
        'accept-language': "zh-CN"
    }

    try:
        # 发送异步 POST 请求
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()  # 检查状态码，非 200 会触发异常
            
            # 解析 JSON 响应
            data = response.json()
            # logger.info(data)  # 记录返回的 JSON 数据
            
            # 检查返回的数据是否符合预期
            if not data.get('data'):
                return {"error": "未找到匹配的比赛信息！"}
            
            return data

    except httpx.HTTPStatusError:
        # logger.error("HTTP 请求失败")  # 记录请求失败的情况
        return {"error": "Failed to fetch data"}
    except Exception as e:
        # logger.error(f"获取比赛信息时出错: {str(e)}")  # 记录一般错误
        return {"error": str(e)}

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