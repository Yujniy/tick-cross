import logging
import requests  # Не забудьте импортировать requests
from models import User, Game, Player, Move, GameStatus

class HttpClient:
    def __init__(self):
        self.host = "http://localhost:8000"

    def get_user(self, user_id: str) -> User | None:
        try:
            # Имитация ответа сервера для локального запуска
            return User(
                user_id=user_id,
                tg_id=12345,
                username="TestUser"
            )
        except Exception as e:
            logging.error(f"Исключение при получении пользователя: {e}")
            return None

    def get_active_game_by_user_id(self, user_id: str) -> tuple[Game, list[Player], list[Move]] | None:
        try:
            response = requests.get(f"{self.host}/get_active_game_by_user_id?user_id={user_id}").json()
            if response["status"] != 200:
                return None
            game = Game(**response["body"]["game"])
            players = [Player(**user) for user in response["body"]["users"]]
            moves = [Move(**move) for move in response["body"]["moves"]]
            return game, players, moves
        except Exception as e:
            logging.error(f"Исключение при получении активной игры: {e}")
            return None

    def get_game_info(self, game_id: int) -> tuple[Game, list[Player], list[Move]] | None:
        try:
            response = requests.get(f"{self.host}/get_game_info?game_id={game_id}").json()
            if response["status"] != 200:
                return None
            game = Game(**response["body"]["game"])
            players = [Player(**user) for user in response["body"]["users"]]
            moves = [Move(**move) for move in response["body"]["moves"]]
            return game, players, moves
        except Exception as e:
            logging.error(f"Исключение при получении информации об игре: {e}")
            return None

    def join_game(self, user_id: str) -> tuple[Game, list[Player]] | None:
        try:
            response = requests.get(f"{self.host}/join_game?user_id={user_id}").json()
            if response["status"] != 200:
                return None
            game = Game(**response["body"]["game"])
            users = [Player(**user) for user in response["body"]["users"]]
            return game, users
        except Exception as e:
            logging.error(f"Исключение при присоединении к игре: {e}")
            return None

    def leave_game(self, user_id: str, game_id: str) -> bool:
        try:
            response = requests.get(f"{self.host}/leave_game?user_id={user_id}&game_id={game_id}").json()
            return response["status"] == 200
        except Exception as e:
            logging.error(f"Исключение при выходе из игры: {e}")
            return False

    def make_move(self, user_id: str, game_id: int, row: int, col: int, sign: str) -> Move | None:
        try:
            url = f"{self.host}/make_move?user_id={user_id}&game_id={game_id}&row={row}&col={col}&sign={sign}"
            response = requests.get(url).json()
            if response["status"] != 200:
                return None
            return Move(**response["body"]["move"])
        except Exception as e:
            logging.error(f"Исключение при совершении хода: {e}")
            return None