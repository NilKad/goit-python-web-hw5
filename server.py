import asyncio
from datetime import datetime
import json
import logging

# from random import randint

import names
from websockets import WebSocketProtocolError, WebSocketServerProtocol, serve
from aiofile import async_open

from get_currency import main as req_currency


logging.basicConfig(level=logging.INFO)


async def logger_file(message):
    async with async_open("server.log", mode="a") as f:
        await f.write(f"{message}\n")


class ChatServer:

    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        # ws.name = randint(0, 100)
        self.clients.add(ws)
        await ws.send(f"hello, {ws.name}")
        logging.info(f"{ws.remote_address} connects")

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f"{ws.remote_address} disconnects")

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def distribute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            message_, *other_params = message.split(" ")
            if message_ == "exchange":
                template = ["1", ""]
                days, *currency = other_params + template[len(other_params) :]
                exchange = await req_currency([days, *currency])
                date_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message_logging = f"{date_stamp}: {ws.name} - {message}"

                await logger_file(message_logging)
                # asyncio.create_task(logger(message_logging))
                # logging.info("send to client currency")

                await self.send_to_clients(json.dumps(exchange, indent=2))
                # logging.info("send to client currency")
            elif message_ == "Hello server":
                await self.send_to_clients("Hello client")
            else:
                await self.send_to_clients(f"{ws.name}: {message}")

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distribute(ws)
        except WebSocketProtocolError as err:
            logging.error(err)
        finally:
            await self.unregister(ws)


async def main():
    chat_server = ChatServer()
    async with serve(chat_server.ws_handler, "localhost", 4000):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
