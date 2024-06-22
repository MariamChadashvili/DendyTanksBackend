import dataclasses
import json
import threading
import time
from copy import copy
from dataclasses import dataclass
from enum import Enum


class Color(str, Enum):
    BLACK = "BLACK"
    WHITE = "WHITE"
    RED = "RED"
    BLUE = "BLUE"
    PINK = "PINK"


class WallType(str, Enum):
    BRICK = "BRICK"
    IRON = "IRON"


class Direction(str, Enum):
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'


@dataclass
class Position:
    x_position: float
    y_position: float


@dataclass
class Bullet:
    position: Position
    direction: Direction


@dataclass
class Wall:
    type: WallType
    position: Position


@dataclass
class Base:
    position: Position
    player_spawn_position: Position


@dataclass
class Map:
    id: str
    name: str
    description: str
    width: float
    height: float
    block_size: float
    bullet_size: float
    bases: list[Base]
    walls: list[Wall]


@dataclass
class Player:
    id: str
    nickname: str
    color: Color
    base: Base
    position: Position
    bullet: Bullet
    is_moving: bool = False
    is_shooting: bool = False
    hearts: int = 3
    direction: Direction = Direction.DOWN


class GameStatus(str, Enum):
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"


@dataclass
class GameConfig:
    player_initial_hearts: int
    player_speed: float
    bullet_speed: float


@dataclass
class Game:
    id: str
    map: Map
    players: dict[str, Player]
    status: GameStatus
    config: GameConfig


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


@dataclass
class Simulation:
    game: Game

    def _move_players(self):
        for idx, player in self.game.players.items():
            if not player.is_moving:
                continue
            player_speed = self.game.config.player_speed
            block_size = self.game.map.block_size

            new_x = copy(player.position.x_position) + block_size/2
            new_y = copy(player.position.y_position) + block_size/2

            if player.direction == Direction.UP:
                new_y -= player_speed
            elif player.direction == Direction.DOWN:
                new_y += player_speed
            elif player.direction == Direction.LEFT:
                new_x -= player_speed
            elif player.direction == Direction.RIGHT:
                new_x += player_speed

            if not ((0 - block_size/2) < new_x < (self.game.map.width + block_size/2) and (0 - block_size/2) < new_y < (self.game.map.height + block_size/2)):
                print(f'{player.id} hit boundary')
                player.is_moving = False
                continue


            for _, pl in self.game.players.items():
                if (pl.base.position.x_position <= new_x <= pl.base.position.x_position + block_size and
                        pl.base.position.y_position <= new_y <= pl.base.position.y_position + block_size or
                        pl.position.x_position <= new_x <= pl.position.x_position + block_size and
                        pl.position.y_position <= new_y <= pl.position.y_position + block_size):
                    print(f'{player.id} hit {pl.id}\'s base or tank')
                    player.is_moving = False
                    break

            for wall in self.game.map.walls:
                if (wall.position.x_position <= new_x <= (wall.position.x_position + block_size) and
                        wall.position.y_position <= new_y <= (wall.position.y_position + block_size)):
                    print(f'{player.id} hit the wall')
                    player.is_moving = False
                    break

            if not player.is_moving:
                continue

            player.position.x_position = new_x - block_size/2
            player.position.y_position = new_y - block_size/2
            print(f'{player.id} moved -- x: {player.position.x_position }, y: {player.position.y_position}')

    def _move_bullets(self):
        for idx, player in self.game.players.items():
            if not player.is_shooting:
                continue
            bullet_speed = self.game.config.bullet_speed
            block_size = self.game.map.block_size

            new_x = copy(player.bullet.position.x_position)
            new_y = copy(player.bullet.position.y_position)

            if player.bullet.direction == Direction.UP:
                new_y -= bullet_speed
            elif player.bullet.direction == Direction.DOWN:
                new_y += bullet_speed
            elif player.bullet.direction == Direction.LEFT:
                new_x -= bullet_speed
            elif player.bullet.direction == Direction.RIGHT:
                new_x += bullet_speed

            if not (0 < new_x < self.game.map.width and 0 < new_y < self.game.map.height):
                print(f'{player.id}\'s bullet hit boundary')
                player.is_shooting = False
                player.bullet = None
                continue

            broken_wall = None
            walls = self.game.map.walls
            if walls:
                for wall in walls:
                    if (wall.position.x_position <= new_x <= wall.position.x_position + block_size and
                            wall.position.y_position <= new_y <= wall.position.y_position + block_size):
                        if wall.type == WallType.IRON:
                            print(f'{player.id} hit iron wall')
                            player.is_shooting = False
                            player.bullet = None
                            break
                        if wall.type == WallType.BRICK:
                            broken_wall = wall
                            print(f'{player.id} broke the wall')
                            player.is_shooting = False
                            player.bullet = None
                            break

            if broken_wall:
                walls.remove(broken_wall)  # ValueError: list.remove(x): x not in list
                continue

            for _, pl in self.game.players.items():
                if ((pl.base.position.x_position <= new_x <= pl.base.position.x_position + block_size and
                        pl.base.position.y_position <= new_y <= pl.base.position.y_position + block_size) or
                        (pl.position.x_position <= new_x <= pl.position.x_position + block_size and
                        pl.position.y_position <= new_y <= pl.position.y_position + block_size)):
                    pl.hearts -= 1
                    pl.bullet = None
                    pl.is_shooting = False
                    if pl.hearts <= 0:
                        # TODO: Who wins?
                        print(f"{player.id} shoot {pl.id}")
                        # player.is_shooting = False
                        self.stop()

            if not player.is_shooting:
                player.bullet = None
                continue

            player.bullet.position.x_position = new_x
            player.bullet.position.y_position = new_y
            print(f'{player.id} bullet -- x: {new_x}, y: {new_y}')

    def update(self):
        Simulation._move_players(self)
        Simulation._move_bullets(self)
        # print(json.dumps(self.game, cls=EnhancedJSONEncoder))

    def start(self):
        def loop():
            self.game.status = GameStatus.IN_PROGRESS

            last_time = time.time_ns()
            ns = 1000000000.0 / 60.0
            delta = 0

            while self.game.status != GameStatus.FINISHED:
                now = time.time_ns()
                delta += (now - last_time) / ns
                last_time = now

                while delta >= 1:
                    # The code you want to be executed
                    self.update()
                    delta -= 1

        t1 = threading.Thread(target=loop, args=())
        t1.start()

    def stop(self):
        self.game.status = GameStatus.FINISHED

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
