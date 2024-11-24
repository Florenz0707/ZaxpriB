import httpx
import json
from nonebot.log import logger

async def download_image(url: str):
    """直接下载并返回图片的字节数据"""
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, timeout=15.0)
            response.raise_for_status()
            return response.content  # 直接返回图片的字节数据
    except httpx.HTTPStatusError:
        return None
    except Exception as e:
        logger.error(f"Error downloading image: {str(e)}")
        return None