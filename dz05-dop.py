import asyncio
import logging
import websockets
import names
import httpx
import aiohttp
from datetime import datetime, timedelta
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
import asyncio


logging.basicConfig(level=logging.INFO)


def get_date_list(delta: int) -> list:
    today = datetime.today()
    result = []

    if delta == 0:
        return [today.strftime('%d.%m.%Y')]
    result = [(today - timedelta(days=i)).strftime('%d.%m.%Y')
              for i in range(delta)]
    result.reverse()
    return result


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


async def get_exchange(*args):
    if len(args) > 1:
        delta = args[1]
    else:
        delta = '0'

    base_url = 'https://api.privatbank.ua/p24api/exchange_rates?json&date='
    try:
        urls = [base_url+i for i in get_date_list(int(delta))]
    except:
        print('некоректні дані. Використовуйте числа від 0 до 10\n')
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


def get_result(result, *args):
    if len(args) > 2:
        currency = args[2:]
    else:
        currency = 'eur', 'usd'
    r = []
    for res in result:
        r.append(get_course_per_day(res, *currency))
    return r


def course_to_str(courses):
    result = ''
    for item in courses:
        for key, value in item.items():
            result += f'Date: {key}\n'
            for k, val in value.items():
                result += f'{k}: {str(val)}\n'
    return result


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            message_list = message.split()
            if message_list[0] == "exchange":
                exchange = await get_exchange(*message_list)
                logging.info('exchange request')

                exchange = get_result(exchange, *message_list)
                # text = course_to_str(exchange)
                for text in exchange:
                    await self.send_to_clients(str(text))
            elif message == 'Hello server':
                await self.send_to_clients("Привіт мої улюблені людиська!")
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())
