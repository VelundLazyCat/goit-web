
import sys
import platform
import aiohttp
import asyncio
import pprint
from datetime import datetime, timedelta


def get_date_list(delta: int) -> list:
    today = datetime.today()
    result = []

    if delta == 0:
        return [today.strftime('%d.%m.%Y')]
    result = [(today - timedelta(days=i)).strftime('%d.%m.%Y')
              for i in range(delta)]
    result.reverse()
    return result


def get_delta():
    try:
        if len(sys.argv) < 2:
            delta = 0
        else:
            delta = int(sys.argv[1])
    except:
        print(
            f'<{sys.argv[1]}> - некоректні дані. Використовуйте числа від 0 до 10\n')
        sys.exit()

    if delta > 10 or delta < 0:
        print('Запит повинен бути в межах від 0 до 10 днів\n')
        sys.exit()
    return delta


def sanitise_course(course: dict, currensy: tuple) -> dict[dict]:
    result = {}
    result['date'] = course['date']
    result['exchangeRate'] = list(filter(lambda m:  m['currency']
                                         in currensy, course['exchangeRate']))
    return result


def get_course_per_day(course: dict[dict], *args) -> dict:
    '''if not args:
        currensy = ('USD', 'EUR')
    else:
        currensy = args'''
    currency = [m.upper() for m in args]
    course = sanitise_course(course, currency)
    res = {}
    for i in course['exchangeRate']:
        try:
            res[i['currency']] = {'sale': i['saleRate'],
                                  'purchase': i['purchaseRate']}
        except:
            res[i['currency']] = {'sale NB': i['saleRateNB'],
                                  'purchase NB': i['purchaseRateNB']}

    result = {course['date']: res}
    return result


async def get_data_from_pb(session, url):
    async with session.get(url) as response:
        result = await response.json()
        return result


def print_result(result):
    if len(sys.argv) > 2:
        currency = sys.argv[1:]
    else:
        currency = 'eur', 'usd'

    for res in result:
        r = get_course_per_day(res, *currency)
        pp = pprint.PrettyPrinter()
        pp.pprint(r)


async def main():
    delta = get_delta()
    # delta = 3
    url = 'https://api.privatbank.ua/p24api/exchange_rates?json&date='
    urls = [url+i for i in get_date_list(delta)]
    result = []
    async with aiohttp.ClientSession() as session:
        for url in urls:
            print(f'Starting {url}')
            try:
                result.append(get_data_from_pb(session, url))
            except aiohttp.ClientConnectorError as err:
                print(f'Connection error: {url}', str(err))

        result = await asyncio.gather(*result)
    return result


if __name__ == "__main__":

    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    result = asyncio.run(main())
    print_result(result)
