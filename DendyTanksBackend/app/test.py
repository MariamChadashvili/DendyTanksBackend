import asyncio
from channels.testing import WebsocketCommunicator
from .consumers import GameConsumer  # Replace with your consumer class name
from DendyTanksBackend.DendyTanksBackend.asgi import application

async def test_game_consumer_ping_pong():
    async with WebsocketCommunicator(application=application) as communicator:
        communicator.connect('ws//socket-server/')  # Replace with your path
        await communicator.wait_for_accept()
        await communicator.send_text_data('PING')
        response = await communicator.receive_text_data()
        assert response == 'PONG'

# Replace 'your_application' with the actual ASGI application object from your asgi.py
