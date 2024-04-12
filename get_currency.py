from datetime import datetime, timedelta
import logging
import sys

# from urllib import response
# from collections import defaultdict

from timing import async_timed

import aiohttp
import asyncio


CURRENCY = ["USD", "EUR"]
PB_URL = "https://api.privatbank.ua/p24api/exchange_rates?date="


class HttpError(Exception):
    pass


days_limit = 10
logging.basicConfig(level=logging.INFO)


@async_timed("timers request: ")
async def request(url: str):
    logging.info("start request)")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result
                else:
                    raise HttpError(f"Error status: {resp.status} for {url}")
        except (aiohttp.ClientConnectorError, aiohttp.InvalidURL) as err:
            raise HttpError(f"Connection error: {url}", str(err))


def extract_currency(response, other_currency):
    # print(other_currensy)
    # logging.info(f"get_currency response: {response}\n\n")
    list_currency = CURRENCY + other_currency
    # logging.info(f"list_currency: {list_currency}")
    result = {response["date"]: {}}
    for el in response["exchangeRate"]:
        # print(f"el: {el}")
        response_date = response["date"]
        cur_currency = el["currency"]
        if cur_currency in list_currency:
            result[response_date][cur_currency] = {
                "sale": el["saleRate"],
                "purchase": el["purchaseRate"],
            }
    # print(result)
    return result


async def get_currency(days_added, other_currency=None):

    date_request = datetime.now() - timedelta(days=days_added)
    date_request_str = date_request.strftime("%d.%m.%Y")
    full_url = PB_URL + date_request_str
    # print(full_url)
    try:
        # logging.info(f"start request to get currency, days {days_added}")
        response = await request(full_url)
        # logging.info(f"end request to get currency, days {days_added}")
        # print(f"received currency on date {date_request_str}")
        res = extract_currency(response, other_currency)
        return res

    except HttpError as err:
        print(f"Error: {err}")
        return None


@async_timed("Total time: ")
async def main(params=[1]):
    days_request, *other_currency = params
    # other_currency = None if len(other_currency) == 0 else other_currency
    # print(f"main other currency: {other_currency}")
    days_request = int(days_request)
    tasks = []
    for i in range(days_request):
        if i > days_limit:
            logging.info("request limit days")
            break
        task = asyncio.create_task(get_currency(i, other_currency))
        tasks.append(task)
    result = await asyncio.gather(*tasks)
    return result


if __name__ == "__main__":
    # if platform.system() == "Windows":
    #     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    r = asyncio.run(main(sys.argv[1:]))
    print(f"!!!!! r: {r}")
