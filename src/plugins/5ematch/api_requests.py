import httpx
from nonebot.log import logger
import nonebot


from dateutil.relativedelta import relativedelta
import datetime
import calendar
import time

config = nonebot.get_driver().config
async def get_uuid(domain: str) -> dict:
    url = f"https://gate.5eplay.com/userinterface/http/v1/userinterface/idTransfer"
    headers = {

    }

    body = {
        "trans": {
            "domain": domain
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            #logger.info(response.json())
            return response.json()["data"]["uuid"]
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {str(e)}")
        return {"error": "Failed to fetch data"}
    except Exception as e:
        logger.error(f"Error fetching friend status: {str(e)}")
        return {"error": str(e)}
    
async def get_match_list(uuid:str) -> dict:
    today = datetime.datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
    # 计算三个月前的日期
    three_months_ago = today + relativedelta(months=-3)
    # 将时间调整到当天的00:00:00
    three_months_ago = three_months_ago.replace(hour=0, minute=0, second=0, microsecond=0)

    url = f"https://gate.5eplay.com/crane/http/api/data/match/list?match_type=-1&page=2&date=0&start_time={three_months_ago.timestamp()}&end_time={today.timestamp()}&uuid={uuid}&limit=30&cs_type=0"
    headers = {

    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            #logger.info(response.json())
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {str(e)}")
        return {"error": "Failed to fetch data"}
    except Exception as e:
        logger.error(f"Error fetching friend status: {str(e)}")
        return {"error": str(e)}

async def get_user_info(uuid:str) -> dict:
    url = f"https://gate.5eplay.com/userinterface/pt/v1/userinterface/header/{uuid}"

    headers = {
        
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            #logger.info(response.json())
            return response.json()
    except Exception as e:
        logger.error(f"Error fetching friend status: {str(e)}")
        return {"error": str(e)}

async def get_dress_info() -> dict:
    url = "https://gate.5eplay.com/reddot_proxy/http/api/home"

    headers = {

    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            #logger.info(response.json())
            return response.json()
    except Exception as e:
        logger.error(f"Error fetching friend status: {str(e)}")
        return {"error": str(e)}