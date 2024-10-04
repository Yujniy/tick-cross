import sys
import pygame
import time
import os
import logging
import traceback
from threading import Thread
from http_client import HttpClient
from models import User, Game, Player, Move, GameStatus

pygame.init()
pygame.display.set_caption("Крестики-нолики")

# Параметры окна
WIDTH, HEIGHT = 400, 650
BOARD_ROWS = 3
BOARD_COLS = 3
BG_COLOR = (28, 170, 156)
WHITE = (255, 255, 255)
BUTTON_COLOR = (52, 152, 219)
BUTTON_HOVER_COLOR = (41, 128, 185)
FONT_SIZE = 30

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Проверка наличия файла с идентификатором пользователя
user_file_name = ".user"
if not os.path.isfile(user_file_name):
    logging.error(f"Файл {user_file_name} не найден. Создаю новый...")
    user_id_input = input("Введи идентификатор пользователя: ")
    with open(user_file_name, "w") as user_file:
        user_file.write(user_id_input)

with open(user_file_name, "r") as user_file:
    user_id = user_file.read().strip()
    if user_id == "":
        logging.error(f"Идентификатор пользователя не найден. Положи его в файл {user_file_name}")
        sys.exit(1)

# Создание экземпляра HTTP клиента
http_client = HttpClient()

# Определение состояний игры
class State:
    MENU = 0
    GAME_WAITING = 1
    GAME_RUNNING = 2
    GAME_FINISHED = 3

class GameApp:
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.current_state = State.MENU
        self.board = [[None] * BOARD_ROWS for _ in range(BOARD_COLS)]
        self.player = None  # храним информацию об игроке
        self.enemy = None  # храним информацию о противнике
        self.game = None  # храним информацию о текущей игре
        self.players = []  # храним информацию обо всех игроках
        self.moves = []  # храним информацию о ходах
        self.can_make_move = False  # флаг, который показывает, можно ли делать ход
        self.user = None
        self.http_client = http_client

        # Инициализация play_button_rect здесь
        self.play_button_rect = pygame.Rect(WIDTH // 2 - 75, HEIGHT // 2, 150, 50)

    def prepare(self):
        while self.user is None:
            fetched_user = self.http_client.get_user(user_id)
            if fetched_user is None:
                logging.error(f"Пользователь с таким идентификатором не найден. Проверьте файл {user_file_name}")
                time.sleep(1)
                continue
            self.user = fetched_user
            logging.info(f"Пользователь успешно загружен: {self.user}")
            # Проверяем, есть ли уже активная игра
            already_running_game = self.http_client.get_active_game_by_user_id(self.user.user_id)
            if already_running_game is not None:
                game, players, moves = already_running_game
                self.update_game_info(game, players, moves, State.GAME_RUNNING)

    def refill_board(self, moves):
        new_board = [[None] * BOARD_ROWS for _ in range(BOARD_COLS)]
        if moves is not None:
            for move in moves:
                new_board[move.row][move.col] = move.sign
        self.board = new_board

    def update_game_info(self, game: Game, players: list[Player], moves: list[Move], current_state: State):
        self.game = game
        self.moves = moves
        self.refill_board(moves)
        self.player = next((user for user in players if user.user_id == self.user.user_id), None) if len(players) == 2 else None
        self.enemy = next((user for user in players if user.user_id != self.user.user_id), None) if len(players) == 2 else None
        self.players = players
        self.current_state = current_state

    def check_game_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and self.can_make_move:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                cell_size = WIDTH // 3
                col = (mouse_x - 0) // cell_size
                row = (mouse_y - 0) // cell_size
                if row < BOARD_ROWS and col < BOARD_COLS and self.board[row][col] is None:
                    self.can_make_move = False
                    self.board[row][col] = self.player.sign
                    self.http_client.make_move(self.user.user_id, self.game.game_id, row, col, self.player.sign)

    def reset_game(self):
        self.game = None
        self.players = []
        self.moves = []
        self.board = [[None] * BOARD_ROWS for _ in range(BOARD_COLS)]
        self.can_make_move = False
        self.player = None
        self.enemy = None
        self.current_state = State.MENU

    def check_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                if self.game is not None and self.user is not None and self.current_state != State.GAME_FINISHED:
                    self.http_client.leave_game(self.user.user_id, self.game.game_id)
                pygame.quit()
                sys.exit(0)
        if self.current_state == State.MENU:
            self.check_button_events()
        if self.current_state == State.GAME_RUNNING:
            self.check_game_events(events)
        if self.current_state == State.GAME_FINISHED:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.reset_game()

    def check_button_events(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()
        if self.play_button_rect.collidepoint(mouse_pos) and mouse_click[0]:
            self.current_state = State.GAME_WAITING

    def draw_menu(self):
        font = pygame.font.SysFont("Arial", 36, True)
        text = font.render("Крестики-нолики", True, WHITE)
        self.screen.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100)))
        # Кнопка "Играть"
        self.play_button_rect = pygame.Rect(WIDTH // 2 - 75, HEIGHT // 2, 150, 50)  # Это можно оставить
        mouse_pos = pygame.mouse.get_pos()
        if self.play_button_rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, BUTTON_HOVER_COLOR, self.play_button_rect)
        else:
            pygame.draw.rect(self.screen, BUTTON_COLOR, self.play_button_rect)
        play_text = font.render("Играть", True, WHITE)
        self.screen.blit(play_text, play_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 25)))

    def get_info(self):
        while True:
            try:
                time.sleep(0.5)
                if self.current_state == State.GAME_WAITING:
                    game, players, moves = None, [], []
                    if self.game is None:
                        response = self.http_client.join_game(self.user.user_id)
                        if response is None:
                            continue
                        game, players = response
                        self.game = game
                        self.players = players
                    else:
                        game_info = self.http_client.get_game_info(self.game.game_id)
                        if game_info is None:
                            continue
                        game, players, moves = game_info
                    if game is not None:
                        state = State.GAME_RUNNING if len(players) == 2 else State.GAME_WAITING
                        self.update_game_info(game, players, moves, state)
                    continue
                if self.current_state == State.GAME_RUNNING:
                    game_info = self.http_client.get_game_info(self.game.game_id)
                    if game_info is None:
                        continue
                    game, players, moves = game_info
                    state = State.GAME_RUNNING if game.status == GameStatus.ACTIVE.value else State.GAME_FINISHED
                    self.update_game_info(game, players, moves, state)
            except Exception:
                logging.error(f"Ошибка при получении информации: {traceback.format_exc()}")

    def draw_nicknames(self, players):
        font = pygame.font.SysFont("Arial", FONT_SIZE, True)
        user1, user2 = players
        # Делаем так, чтобы крестики всегда были слева
        if user1.sign == '0':
            user1, user2 = user2, user1
        text = font.render(f"X {user1.username} VS {user2.username} O", True, WHITE)
        self.screen.blit(text, text.get_rect(center=(WIDTH // 2, 450)))
        if self.can_make_move:
            text = font.render("Твой ход!", True, WHITE)
            self.screen.blit(text, text.get_rect(center=(WIDTH // 2, 400)))

    def draw_game_waiting(self):
        font = pygame.font.SysFont("Arial", FONT_SIZE, True)
        text = font.render("Ожидание второго игрока...", True, WHITE)
        self.screen.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

    def check_can_make_move(self):
        can_make_move = True
        sign = self.player.sign
        count_x = sum([1 for row in self.board for cell in row if cell == 'X'])
        count_0 = sum([1 for row in self.board for cell in row if cell == '0'])
        if sign == 'X' and count_x > count_0:
            can_make_move = False
        if sign == '0' and count_0 >= count_x:
            can_make_move = False
        return can_make_move

    def draw_lines(self):
        # Отрисовка линий сетки
        line_color = (23, 145, 135)
        for i in range(1, 3):
            # Вертикальные линии
            pygame.draw.line(self.screen, line_color, (i * WIDTH // 3, 0), (i * WIDTH // 3, WIDTH), 7)
            # Горизонтальные линии
            pygame.draw.line(self.screen, line_color, (0, i * WIDTH // 3), (WIDTH, i * WIDTH // 3), 7)

    def draw_figures(self):
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                if self.board[row][col] == '0':
                    self.draw_circle(row, col)
                elif self.board[row][col] == 'X':
                    self.draw_cross(row, col)

    def draw_cross(self, row, col):
        x_color = (84, 84, 84)
        x_start_x = col * WIDTH // 3 + 55
        x_start_y = row * WIDTH // 3 + 55
        x_end_x = col * WIDTH // 3 + WIDTH // 3 - 55
        x_end_y = row * WIDTH // 3 + WIDTH // 3 - 55
        pygame.draw.line(self.screen, x_color, (x_start_x, x_start_y), (x_end_x, x_end_y), 15)
        pygame.draw.line(self.screen, x_color, (x_start_x, x_end_y), (x_end_x, x_start_y), 15)

    def draw_circle(self, row, col):
        o_color = (242, 235, 211)
        center_x = col * WIDTH // 3 + WIDTH // 6
        center_y = row * WIDTH // 3 + WIDTH // 6
        pygame.draw.circle(self.screen, o_color, (center_x, center_y), WIDTH // 6 - 55, 15)

    def draw_game_running(self):
        if self.game is None:
            return
        if self.game.status == GameStatus.FINISHED.value:
            self.current_state = State.GAME_FINISHED
            self.refill_board(self.moves)
            return
        self.can_make_move = self.check_can_make_move()
        self.draw_nicknames(self.players)
        self.draw_lines()
        self.draw_figures()

    def draw_game_finished(self):
        winner = None
        if self.game.winner_id is not None:
            winner = self.user if self.game.winner_id == self.user.user_id else self.enemy
        font = pygame.font.SysFont("Arial", FONT_SIZE, True)
        if winner is None:
            text = font.render("Ничья!", True, WHITE)
        else:
            text = font.render(f"Победитель — {winner.username}!", True, WHITE)
        self.screen.blit(text, text.get_rect(center=(WIDTH // 2, 450)))
        self.draw_lines()
        self.draw_figures()

    def run(self):
        info_thread = Thread(target=self.get_info)
        info_thread.daemon = True
        info_thread.start()
        prepare_thread = Thread(target=self.prepare)
        prepare_thread.daemon = True
        prepare_thread.start()
        while True:
            self.clock.tick(60)
            self.screen.fill(BG_COLOR)
            self.check_events()
            if self.current_state == State.MENU:
                self.draw_menu()
            if self.current_state == State.GAME_WAITING:
                self.draw_game_waiting()
            if self.current_state == State.GAME_RUNNING:
                self.draw_game_running()
            if self.current_state == State.GAME_FINISHED:
                self.draw_game_finished()
            pygame.display.flip()

if __name__ == "__main__":
    game_app = GameApp()
    game_app.run()