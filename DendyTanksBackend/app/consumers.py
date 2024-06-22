import json
import threading
from asyncio import sleep
from copy import copy
from datetime import time


from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import async_to_sync

from .game_models import Simulation, Game, GameStatus, EnhancedJSONEncoder, Direction, Bullet, GameConfig, Map, Base, \
    Position, Player, Color, Wall, WallType


game_states = {}


class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.game_group_name = f'game_{self.game_id}'  # this should be room id ?
        await self.channel_layer.group_add(
            self.game_group_name,
            self.channel_name
        )
        await self.accept()

        game_state = game_states.get(self.game_id)
        if not game_state:
            game_state = self.initialize_game_state()
            game_states[self.game_id] = game_state

        self.game = game_state['game']
        game_config = self.game.config

        # game_config = GameConfig(
        #     player_initial_hearts=3,
        #     player_speed=20,
        #     bullet_speed=30
        # )


        self.player_id = str(len(self.game.players) + 1)
        print(self.player_id)
        self.game.players[self.player_id] = Player(
            id=self.player_id,
            nickname=f"Player-{self.player_id}",
            color=Color.PINK if self.player_id == '1' else Color.BLUE,
            base=self.game.map.bases[int(self.player_id) - 1],
            position=self.game.map.bases[int(self.player_id) - 1].player_spawn_position,
            hearts=game_config.player_initial_hearts,
            bullet=None
        )

        await self.send_json({
            'action': 'assign_player_id',
            'player_id': self.player_id
        })


        self.simulation = Simulation(game=self.game)
        self.simulation.start()

        self.update_task = threading.Thread(target=self.send_periodic_updates)
        self.update_task.start()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.game_group_name,
            self.channel_name
        )
        self.simulation.stop()

    async def receive_json(self, content):
        action = content.get('action')
        player_id = content.get('player_id')

        if action == 'start_move':
            direction = content.get('direction')
            self.start_move(player_id, direction)
        elif action == 'stop_move':
            self.stop_move(player_id)
        elif action == 'shoot':
            self.shoot(player_id)

        # await self.channel_layer.group_send(
        #     self.game_group_name,
        #     {
        #         'type': 'game_update',
        #         'message': json.dumps(self.simulation.game, cls=EnhancedJSONEncoder)
        #     }
        # )

    def send_periodic_updates(self):
        while self.game.status != GameStatus.FINISHED:
            sleep(1 / 60)
            game_data = json.dumps(self.simulation.game, cls=EnhancedJSONEncoder)
            # print(type(game_data))
            async_to_sync(self.channel_layer.group_send)(
                self.game_group_name,
                {
                    'type': 'game_update',
                    'message': game_data
                }
            )

    async def game_update(self, event):
        # print(event)
        await self.send_json(event['message'])
        # game_data = json.dumps(self.game, cls=EnhancedJSONEncoder)
        # print(game_data)

    def start_move(self, player_id, direction):
        player = self.game.players.get(player_id)
        player.is_moving = True
        player.direction = direction

    def stop_move(self, player_id):
        player = self.game.players.get(player_id)
        player.is_moving = False

    def shoot(self, player_id):
        player = self.game.players.get(player_id)
        player.is_shooting = True
        bullet_position = copy(player.position)
        block_size = self.game.map.block_size
        if player.direction == Direction.UP:
            bullet_position.x_position += block_size/2
            bullet_position.y_position -= 5
        elif player.direction == Direction.DOWN:
            bullet_position.x_position += block_size/2
            bullet_position.y_position += block_size + 5
        elif player.direction == Direction.LEFT:
            bullet_position.y_position += block_size/2
            bullet_position.x_position -= 5
        elif player.direction == Direction.RIGHT:
            bullet_position.x_position += block_size + 5
            bullet_position.y_position += block_size/2
        player.bullet = Bullet(bullet_position, player.direction)

    def initialize_game_state(self):
        game_config = GameConfig(
            player_initial_hearts=3,
            player_speed=20,
            bullet_speed=25
        )

        bases = [
            Base(Position(0.0, 0.0), Position(0.0, 20.0)),
            Base(Position(780.0, 780.0), Position(760.0, 780.0))
        ]

        walls = [
            Wall(
                type=WallType.BRICK,
                position=Position(700.0, 0.0)
            ),
            Wall(
                type=WallType.IRON,
                position=Position(0.0, 700.0)
            )
        ]

        map = Map(
            id="1",
            name="Test Map",
            description="Test Map",
            width=800.0,
            height=800.0,
            block_size=20.0,
            bullet_size=5.0,
            bases=bases,
            walls=walls
        )

        # players = {
        #     '1': Player(
        #         id="1",
        #         nickname="P1",
        #         color=Color.PINK,
        #         base=bases[0],
        #         position=bases[0].player_spawn_position,
        #         hearts=game_config.player_initial_hearts,
        #         bullet=None
        #     ),
        #     '2': Player(
        #         id="2",
        #         nickname="P2",
        #         color=Color.BLUE,
        #         base=bases[1],
        #         position=bases[1].player_spawn_position,
        #         hearts=game_config.player_initial_hearts,
        #         bullet=None
        #     )
        # }

        players = {}

        game = Game(
            id=self.game_id,
            map=map,
            players=players,
            status=GameStatus.CREATED,
            config=game_config
        )
        return {'game': game}


    # async def connect(self):
    #     await self.accept()
    #     self.simulation = Simulation()
    #
    # async def receive(self, text_data=None, bytes_data=None, **kwargs):
    #     if text_data == 'PING':
    #         await self.send('PONG')

    # async def receive_json(self, content):
    #     message = content.get('message', '')
    #     await self.send_json({
    #         'message': f'Received: {message}'
    #     })
