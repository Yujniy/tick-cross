import logging
from models import User, Game, Player, Move, GameStatus

class HttpClient:
    def __init__(self):
        # Для локального запуска используем фиктивный хост
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

    # Здесь вы можете добавить дополнительные методы взаимодействия с сервером
    # Для локального запуска они могут возвращать тестовые данные