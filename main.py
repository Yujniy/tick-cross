import sys
import pygame
import time
import os
import logging
from threading import Thread
from http_client import HttpClient
from models import User, Game, Player, Move, GameStatus
import random

pygame.init()
pygame.display.set_caption("Крестики-нолики")

# Параметры окна
W, H = 400, 650  # Увеличили высоту еще больше
BG_COLOR = (28, 170, 156)
LINE_COLOR = (23, 145, 135)
X_COLOR = (84, 84, 84)
O_COLOR = (242, 235, 211)
BUTTON_COLOR = (52, 152, 219)
BUTTON_HOVER_COLOR = (41, 128, 185)
screen = pygame.display.set_mode((W, H))

clock = pygame.time.Clock()
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Проверка наличия файла с идентификатором пользователя
user_file_name = ".user"
user_file_exists = os.path.isfile(user_file_name)
if not user_file_exists:
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
user = None

# Игровое поле
board = [['' for _ in range(3)] for _ in range(3)]
current_player = 'X'

def check_winner(board):
    # Проверка по горизонтали и вертикали
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != '':
            return board[i][0], [(i, 0), (i, 1), (i, 2)]
        if board[0][i] == board[1][i] == board[2][i] != '':
            return board[0][i], [(0, i), (1, i), (2, i)]
    # Проверка по диагоналям
    if board[0][0] == board[1][1] == board[2][2] != '':
        return board[0][0], [(0, 0), (1, 1), (2, 2)]
    if board[0][2] == board[1][1] == board[2][0] != '':
        return board[0][2], [(0, 2), (1, 1), (2, 0)]
    # Проверка на ничью
    if all(board[i][j] != '' for i in range(3) for j in range(3)):
        return 'Tie', []
    return None, []

def prepare():
    global user
    while user is None:
        fetched_user = http_client.get_user(user_id)
        if fetched_user is None:
            logging.error(f"Пользователь с таким идентификатором не найден. Проверьте файл {user_file_name}")
            time.sleep(1)
            continue
        user = fetched_user
        logging.info(f"Пользователь успешно загружен: {user}")

def draw_board(winning_line=None):
    board_size = min(W, H - 200)  # Оставляем место для кнопки и текста
    cell_size = board_size // 3
    board_top = (H - board_size) // 2 - 50  # Сдвигаем доску немного вверх

    for i in range(1, 3):
        pygame.draw.line(screen, LINE_COLOR, (i * cell_size, board_top), (i * cell_size, board_top + board_size), 7)
        pygame.draw.line(screen, LINE_COLOR, (0, board_top + i * cell_size), (board_size, board_top + i * cell_size), 7)
    
    for row in range(3):
        for col in range(3):
            x = col * cell_size
            y = board_top + row * cell_size
            if board[row][col] == 'X':
                pygame.draw.line(screen, X_COLOR, (x + 30, y + 30), (x + cell_size - 30, y + cell_size - 30), 4)
                pygame.draw.line(screen, X_COLOR, (x + cell_size - 30, y + 30), (x + 30, y + cell_size - 30), 4)
            elif board[row][col] == 'O':
                pygame.draw.circle(screen, O_COLOR, (x + cell_size // 2, y + cell_size // 2), cell_size // 3, 4)
    
    if winning_line:
        start = (winning_line[0][1] * cell_size + cell_size // 2, board_top + winning_line[0][0] * cell_size + cell_size // 2)
        end = (winning_line[2][1] * cell_size + cell_size // 2, board_top + winning_line[2][0] * cell_size + cell_size // 2)
        pygame.draw.line(screen, (255, 0, 0), start, end, 4)

def make_mistake():
    return random.random() < 0.3  # 30% шанс сделать ошибку

def ai_move():
    global board, current_player
    
    # Проверяем, можем ли мы выиграть на следующем ходу
    for row in range(3):
        for col in range(3):
            if board[row][col] == '' and not make_mistake():
                board[row][col] = 'O'
                if check_winner(board)[0] == 'O':
                    current_player = 'X'
                    return
                board[row][col] = ''
    
    # Проверяем, нужно ли блокировать ход игрока
    for row in range(3):
        for col in range(3):
            if board[row][col] == '' and not make_mistake():
                board[row][col] = 'X'
                if check_winner(board)[0] == 'X':
                    board[row][col] = 'O'
                    current_player = 'X'
                    return
                board[row][col] = ''
    
    # Пытаемся занять центр
    if board[1][1] == '' and not make_mistake():
        board[1][1] = 'O'
        current_player = 'X'
        return
    
    # Пытаемся занять угол
    corners = [(0,0), (0,2), (2,0), (2,2)]
    random.shuffle(corners)
    for row, col in corners:
        if board[row][col] == '' and not make_mistake():
            board[row][col] = 'O'
            current_player = 'X'
            return
    
    # Занимаем любую свободную клетку
    empty_cells = [(row, col) for row in range(3) for col in range(3) if board[row][col] == '']
    if empty_cells:
        row, col = random.choice(empty_cells)
        board[row][col] = 'O'
        current_player = 'X'

def reset_game():
    global board, current_player, game_over, winner, winning_line
    board = [['' for _ in range(3)] for _ in range(3)]
    current_player = 'X'
    game_over = False
    winner = None
    winning_line = None

def draw_button(text, x, y, w, h, color, hover_color, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    if x + w > mouse[0] > x and y + h > mouse[1] > y:
        pygame.draw.rect(screen, hover_color, (x, y, w, h))
        if click[0] == 1 and action is not None:
            action()
    else:
        pygame.draw.rect(screen, color, (x, y, w, h))

    font = pygame.font.SysFont("Arial", 20)
    text_surf = font.render(text, True, WHITE)
    text_rect = text_surf.get_rect()
    text_rect.center = ((x + (w / 2)), (y + (h / 2)))
    screen.blit(text_surf, text_rect)

def game_loop():
    global current_player, board, game_over, winner, winning_line
    prepare_thread = Thread(target=prepare)
    prepare_thread.daemon = True
    prepare_thread.start()

    run = True
    game_over = False
    winner = None
    winning_line = None

    while run:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN and user is not None:
                x, y = pygame.mouse.get_pos()
                board_size = min(W, H - 200)
                cell_size = board_size // 3
                board_top = (H - board_size) // 2 - 50
                col = x // cell_size
                row = (y - board_top) // cell_size
                if not game_over and current_player == 'X' and 0 <= row < 3 and 0 <= col < 3 and board[row][col] == '':
                    board[row][col] = current_player
                    current_player = 'O'
                    winner, winning_line = check_winner(board)
                    if winner:
                        game_over = True
                    else:
                        ai_move()
                        winner, winning_line = check_winner(board)
                        if winner:
                            game_over = True

        screen.fill(BG_COLOR)

        if user is None:
            font = pygame.font.SysFont("Arial", 36, True)
            text = font.render("Загрузка...", True, WHITE)
            screen.blit(text, text.get_rect(center=(W // 2, H // 2)))
        else:
            draw_board(winning_line)
            pygame.display.set_caption(f"Крестики-нолики ({user.username})")

            if game_over:
                font = pygame.font.SysFont("Arial", 36, True)
                if winner == 'Tie':
                    text = font.render("Ничья!", True, WHITE)
                else:
                    text = font.render(f"Победитель: {winner}!", True, WHITE)
                screen.blit(text, text.get_rect(center=(W // 2, H - 100)))

            draw_button("Новая игра", W // 2 - 75, H - 75, 150, 50, BUTTON_COLOR, BUTTON_HOVER_COLOR, reset_game)

        pygame.display.update()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    game_loop()