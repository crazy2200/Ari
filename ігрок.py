import pygame
import math
import random
import socket
import pickle
import os
import traceback

WIDTH = 1400
HEIGHT = 777
FPS = 140
MAP_SIZE = 3000

pygame.init()
pygame.font.init()

window = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

try:
    game_font = pygame.font.Font(None, 24)
    hud_font = pygame.font.Font(None, 20)
    menu_font = pygame.font.Font(None, 32)
    title_font = pygame.font.Font(None, 65)
except:
    game_font = hud_font = menu_font = title_font = None

ALL_BOT_NAMES = [
    "Shadow", "ProGamer", "Killer2006", "Storm", "Vortex",
    "Ghost", "CyberNinja", "Phoenix", "Titan", "Neon",
    "Alpha", "Omega", "Spectre", "Zero", "Bober",
    "Sniper", "Hunter", "Legend", "Master", "Flash",
    "Viper", "Matrix", "Cyber", "King", "Demon"
]

SKIN_COLORS = [
    (255, 80, 80),  # 0: Класичний
    (80, 200, 120),  # 1: Очі
    (255, 165, 0),  # 2: Мішень
    (0, 255, 255),  # 3: Неон
    (255, 215, 0),  # 4: Зірочка
    (238, 130, 238),  # 5: Усмішка
    (147, 112, 219),  # 6: Котеня
    (70, 130, 180),  # 7: Пірат
    (255, 69, 0),  # 8: Сонце
    (50, 50, 50),  # 9: Чорна діра
    (220, 20, 60)  # 10: Динаміт (Секретний скін)
]

# Збереження та завантаження прогресу
SAVE_FILE = "savegame.dat"
coins = 0
unlocked_skins = {0}
selected_skin = 0
difficulty = "Нормальний"

# Загальний лічильник вбивств для всіх режимів
total_kills = 0

# Здібності арени
shield_timer = 0
shield_cooldown = 0
dynamite_unlocked = False
dynamite_active = False
card_selection_active = False
last_milestone_checked = 0
current_cards = []
selected_card_ability = None  # Зберігає обрану картку для арени
ability_cooldown_timer = 0  # Таймер перезарядки здатності
laser_active_timer = 0  # Таймер тривалості анімації червоного променя

ALL_ARENA_CARDS = [
    "Промінь (ЛКМ)",
    "Щит (5 сек)",
    "Бронежилет",
    "Меч",
    "Динаміт (E)",
    "Перезарядка"
]


def save_game_data():
    global coins, unlocked_skins, selected_skin
    data = {
        "coins": coins,
        "unlocked_skins": unlocked_skins,
        "selected_skin": selected_skin
    }
    try:
        with open(SAVE_FILE, "wb") as f:
            pickle.dump(data, f)
    except:
        pass


def load_game_data():
    global coins, unlocked_skins, selected_skin
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "rb") as f:
                data = pickle.load(f)
                coins = data.get("coins", 0)
                unlocked_skins = data.get("unlocked_skins", {0})
                selected_skin = data.get("selected_skin", 0)
        except:
            pass


load_game_data()


class Person:
    def __init__(self, x, y, r, color, nickname, skin_type=0):
        self.x = x
        self.y = y
        self.r = r
        self.color = color
        self.nickname = nickname
        self.skin_type = skin_type

    def draw(self, screen, person, scale):
        sx = int((self.x - person.x) * scale + WIDTH // 2)
        sy = int((self.y - person.y) * scale + HEIGHT // 2)
        sr = int(self.r * scale)

        if sr > 0:
            skin_color = SKIN_COLORS[self.skin_type % len(SKIN_COLORS)]
            pygame.draw.circle(screen, skin_color, (sx, sy), sr)
            pygame.draw.circle(screen, (30, 30, 30), (sx, sy), sr, max(1, int(sr * 0.08)))

            if self.nickname and game_font:
                try:
                    text_surface = game_font.render(self.nickname, True, (0, 0, 0))
                    text_rect = text_surface.get_rect(center=(sx, sy - sr - 15))
                    screen.blit(text_surface, text_rect)
                except:
                    pass


class Player(Person):
    def __init__(self, x, y, r, color, nickname, skin_type=0):
        super().__init__(x, y, r, color, nickname, skin_type)
        self.base_speed = 2
        self.speed = self.base_speed
        self.max_energy = 100.0
        self.energy = 100.0
        self.is_boosting = False

    def toggle_boost(self):
        if self.is_boosting:
            self.is_boosting = False
            self.speed = self.base_speed
        else:
            if self.energy > 5:
                self.is_boosting = True
                self.speed = self.base_speed * 2

    def update(self):
        if dynamite_active:
            self.speed = self.base_speed * 3.5
        elif self.is_boosting:
            self.energy -= 100.0 / (5 * FPS)
            if self.energy <= 0:
                self.energy = 0
                self.is_boosting = False
                self.speed = self.base_speed
        else:
            if self.energy < self.max_energy:
                self.energy += 100.0 / (10 * FPS)
                if self.energy > self.max_energy:
                    self.energy = self.max_energy

        mx, my = pygame.mouse.get_pos()
        dx = mx - WIDTH // 2
        dy = my - HEIGHT // 2
        dist = math.hypot(dx, dy)

        if dist > 10:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        self.x = max(-MAP_SIZE, min(MAP_SIZE, self.x))
        self.y = max(-MAP_SIZE, min(MAP_SIZE, self.y))

    def draw_hud(self, screen, coins_val, kills_val):
        bar_width = 300
        bar_height = 22
        bar_x = (WIDTH - bar_width) // 2
        bar_y = HEIGHT - 45

        pygame.draw.rect(screen, (220, 220, 220), (bar_x, bar_y, bar_width, bar_height), border_radius=6)
        fill_width = int(bar_width * (self.energy / self.max_energy))

        if self.is_boosting:
            bar_color = (255, 140, 0)
        elif self.energy < self.max_energy:
            bar_color = (220, 50, 50)
        else:
            bar_color = (0, 200, 0)

        if fill_width > 0:
            pygame.draw.rect(screen, bar_color, (bar_x, bar_y, fill_width, bar_height), border_radius=6)
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height), 2, border_radius=6)

        if game_font:
            coin_surf = game_font.render(f"Монети: {coins_val} | Вбито: {kills_val}", True, (200, 150, 0))
            if coin_surf:
                screen.blit(coin_surf, (20, 20))


class Bot(Person):
    def __init__(self, x, y, r, color, nickname, speed=1.5, skin_type=0):
        super().__init__(x, y, r, color, nickname, skin_type)
        self.base_speed = speed
        self.speed = speed
        self.angle = random.uniform(0, 2 * math.pi)
        self.change_dir_timer = random.randint(100, 300)

    def update(self, all_persons):
        closest_target = None
        min_dist = 800

        for other in all_persons:
            if other == self:
                continue
            dist = math.hypot(self.x - other.x, self.y - other.y)
            if dist < min_dist:
                min_dist = dist
                closest_target = other

        if closest_target:
            if hasattr(closest_target, 'r') and closest_target.r > self.r * 1.05:
                escape_angle = math.atan2(self.y - closest_target.y, self.x - closest_target.x)
                self.speed = self.base_speed * 2
                self.x += math.cos(escape_angle) * self.speed
                self.y += math.sin(escape_angle) * self.speed
            elif hasattr(closest_target, 'r') and self.r > closest_target.r * 1.05:
                hunt_angle = math.atan2(closest_target.y - self.y, closest_target.x - self.x)
                self.speed = self.base_speed * 1.7
                self.x += math.cos(hunt_angle) * self.speed
                self.y += math.sin(hunt_angle) * self.speed
            else:
                self.normal_movement()
        else:
            self.normal_movement()

        self.x = max(-MAP_SIZE, min(MAP_SIZE, self.x))
        self.y = max(-MAP_SIZE, min(MAP_SIZE, self.y))

    def respawn(self, player_r=15.0):
        self.x = random.randint(-MAP_SIZE // 2, MAP_SIZE // 2)
        self.y = random.randint(-MAP_SIZE // 2, MAP_SIZE // 2)
        self.r = float(max(10, random.randint(int(player_r * 0.8), int(player_r))))
        self.nickname = random.choice(ALL_BOT_NAMES)
        self.skin_type = random.randint(0, 9)

    def normal_movement(self):
        self.speed = self.base_speed
        self.change_dir_timer -= 1
        if self.change_dir_timer <= 0:
            self.angle = random.uniform(0, 2 * math.pi)
            self.change_dir_timer = random.randint(150, 350)

        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed


class Eat:
    def __init__(self, x, y, r, color):
        self.x = x
        self.y = y
        self.r = r
        self.color = color

    def draw(self, screen, person, scale):
        sx = int((self.x - person.x) * scale + WIDTH // 2)
        sy = int((self.y - person.y) * scale + HEIGHT // 2)
        sr = int(self.r * scale)
        if sr > 0:
            pygame.draw.circle(screen, self.color, (sx, sy), sr)


game_state = "MENU"
use_internet = False
use_bots = True

skin_prices = [0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500]

nickname = "dsdjsusfu"
server_ip = "localhost"

checkbox_net_rect = pygame.Rect(WIDTH // 2 - 180, HEIGHT // 2 - 130, 30, 30)
checkbox_bots_rect = pygame.Rect(WIDTH // 2 - 180, HEIGHT // 2 - 80, 30, 30)

diff_btn_rect = pygame.Rect(WIDTH // 2 - 180, HEIGHT // 2 - 30, 360, 45)
play_btn_rect = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 + 20, 260, 40)
arena_btn_rect = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 + 65, 260, 40)
shop_btn_rect = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 + 110, 260, 40)
exit_btn_rect = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 + 155, 260, 40)

arena_easy_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 60, 300, 50)
arena_norm_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 5, 300, 50)
arena_hard_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 70, 300, 50)
arena_back_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 135, 300, 45)

skin_btn_rects = [
    pygame.Rect(WIDTH // 2 - 330, HEIGHT // 2 - 210, 310, 55),
    pygame.Rect(WIDTH // 2 + 20, HEIGHT // 2 - 210, 310, 55),
    pygame.Rect(WIDTH // 2 - 330, HEIGHT // 2 - 145, 310, 55),
    pygame.Rect(WIDTH // 2 + 20, HEIGHT // 2 - 145, 310, 55),
    pygame.Rect(WIDTH // 2 - 330, HEIGHT // 2 - 80, 310, 55),
    pygame.Rect(WIDTH // 2 + 20, HEIGHT // 2 - 80, 310, 55),
    pygame.Rect(WIDTH // 2 - 330, HEIGHT // 2 - 15, 310, 55),
    pygame.Rect(WIDTH // 2 + 20, HEIGHT // 2 - 15, 310, 55),
    pygame.Rect(WIDTH // 2 - 330, HEIGHT // 2 + 50, 310, 55),
    pygame.Rect(WIDTH // 2 + 20, HEIGHT // 2 + 50, 310, 55),
    pygame.Rect(WIDTH // 2 - 155, HEIGHT // 2 + 115, 310, 55),
]
back_btn_rect = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 + 135, 260, 45)

in_game_exit_rect = pygame.Rect(WIDTH - 140, 20, 120, 40)
game_over_menu_btn = pygame.Rect(WIDTH // 2 - 160, HEIGHT // 2 + 10, 140, 50)
game_over_restart_btn = pygame.Rect(WIDTH // 2 + 20, HEIGHT // 2 + 10, 140, 50)

card_rects = [
    pygame.Rect(WIDTH // 2 - 320, HEIGHT // 2 - 50, 200, 120),
    pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 120),
    pygame.Rect(WIDTH // 2 + 120, HEIGHT // 2 - 50, 200, 120)
]

sock = None
player = None
eats = []
bots = []
world_data = {"clients": {}, "bots": [], "eats": []}

arena_mode = False
arena_total_bots = 100
arena_wave_stage = 1
is_game_over = False


def start_game_session(is_arena=False, arena_diff="Легкий"):
    global sock, player, eats, bots, arena_mode, arena_total_bots, total_kills, arena_wave_stage, card_selection_active, last_milestone_checked, dynamite_active, current_cards, is_game_over, selected_card_ability, ability_cooldown_timer, laser_active_timer
    arena_mode = is_arena
    total_kills = 0
    arena_wave_stage = 1
    card_selection_active = False
    last_milestone_checked = 0
    dynamite_active = False
    current_cards = []
    is_game_over = False
    selected_card_ability = None
    ability_cooldown_timer = 0
    laser_active_timer = 0

    if arena_mode:
        if arena_diff == "Легкий":
            arena_total_bots = 100
        elif arena_diff == "Складний":
            arena_total_bots = 200
        else:
            arena_total_bots = 150
    else:
        arena_total_bots = 30

    player = Player(0, 0, 15.0, (255, 80, 80), nickname, skin_type=selected_skin)

    eats = [
        Eat(random.randint(-MAP_SIZE, MAP_SIZE), random.randint(-MAP_SIZE, MAP_SIZE), 10,
            (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        for _ in range(300)
    ]

    if use_bots or arena_mode:
        if difficulty == "Легкий" or (arena_mode and arena_diff == "Легкий"):
            bot_speed = 1.0
        elif difficulty == "Складний" or (arena_mode and arena_diff == "Складний"):
            bot_speed = 2.2
        else:
            bot_speed = 1.5

        initial_count = 10 if arena_mode else 30
        bots = []
        for _ in range(initial_count):
            b_r = float(max(10, random.randint(int(player.r * 0.8), int(player.r))))
            bots.append(
                Bot(random.randint(-MAP_SIZE // 2, MAP_SIZE // 2), random.randint(-MAP_SIZE // 2, MAP_SIZE // 2), b_r,
                    (80, 120, 255), random.choice(ALL_BOT_NAMES), speed=bot_speed, skin_type=random.randint(0, 9)))
    else:
        bots = []

    if use_internet and not arena_mode:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setblocking(False)
        except:
            sock = None
    else:
        sock = None


running = True
while running:
    try:
        mouse_pos = pygame.mouse.get_pos()

        if arena_mode:
            if ability_cooldown_timer > 0:
                ability_cooldown_timer -= 1 / FPS
            if laser_active_timer > 0:
                laser_active_timer -= 1 / FPS

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if game_state == "PLAYING" and not card_selection_active and not is_game_over:
                    if e.key == pygame.K_SPACE:
                        if player:
                            player.toggle_boost()
                    elif e.key == pygame.K_e and dynamite_unlocked:
                        dynamite_active = True
                    elif e.key in (pygame.K_LALT, pygame.K_RALT):
                        coins += 1000
                        save_game_data()
                    # --- ЧІТ ДЛЯ АРЕНИ: Ctrl + 0 додає 10 вбивств ---
                    elif (e.key == pygame.K_0 or e.key == pygame.K_KP0) and arena_mode:
                        mods = pygame.key.get_mods()
                        if mods & pygame.KMOD_CTRL:
                            total_kills += 10
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if game_state == "PLAYING" and arena_mode and not card_selection_active and not is_game_over:
                    if e.button == 1 and selected_card_ability == "Промінь (ЛКМ)":
                        if ability_cooldown_timer <= 0:
                            laser_active_timer = 0.3  # Тривалість спалаху променя (секунди)
                            ability_cooldown_timer = 5.0  # Перезарядка 5 секунд

                            # Постріл променем: вбиваємо ботів на лінії променя
                            mx, my = pygame.mouse.get_pos()
                            # Позиція гравця на екрані завжди центр
                            px_screen, py_screen = WIDTH // 2, HEIGHT // 2
                            # Перевірка зіткнення променя з ботами
                            for bot in list(bots):
                                scale = max(0.25, min(50.0 / player.r, 1.2)) if player else 1.0
                                bx_screen = int((bot.x - player.x) * scale + WIDTH // 2)
                                by_screen = int((bot.y - player.y) * scale + HEIGHT // 2)
                                # Відстань від центру екрана до бота і чим ближче до вектора миші
                                d_bot = math.hypot(bx_screen - px_screen, by_screen - py_screen)
                                if d_bot < 600:  # Дальність променя
                                    total_kills += 1
                                    bot.respawn(player.r if player else 15.0)

            elif e.type == pygame.MOUSEBUTTONUP:
                click_pos = pygame.mouse.get_pos()
                if game_state == "MENU":
                    if checkbox_net_rect.collidepoint(click_pos):
                        use_internet = not use_internet
                    elif checkbox_bots_rect.collidepoint(click_pos):
                        use_bots = not use_bots
                    elif diff_btn_rect.collidepoint(click_pos):
                        if difficulty == "Легкий":
                            difficulty = "Нормальний"
                        elif difficulty == "Нормальний":
                            difficulty = "Складний"
                        else:
                            difficulty = "Легкий"
                    elif play_btn_rect.collidepoint(click_pos):
                        start_game_session(is_arena=False)
                        game_state = "PLAYING"
                    elif arena_btn_rect.collidepoint(click_pos):
                        game_state = "ARENA_MENU"
                    elif shop_btn_rect.collidepoint(click_pos):
                        game_state = "SHOP"
                    elif exit_btn_rect.collidepoint(click_pos):
                        running = False
                elif game_state == "ARENA_MENU":
                    if arena_easy_rect.collidepoint(click_pos):
                        difficulty = "Легкий"
                        start_game_session(is_arena=True, arena_diff="Легкий")
                        game_state = "PLAYING"
                    elif arena_norm_rect.collidepoint(click_pos):
                        difficulty = "Нормальний"
                        start_game_session(is_arena=True, arena_diff="Нормальний")
                        game_state = "PLAYING"
                    elif arena_hard_rect.collidepoint(click_pos):
                        difficulty = "Складний"
                        start_game_session(is_arena=True, arena_diff="Складний")
                        game_state = "PLAYING"
                    elif arena_back_rect.collidepoint(click_pos):
                        game_state = "MENU"
                elif game_state == "SHOP":
                    for idx, rect in enumerate(skin_btn_rects):
                        if rect.collidepoint(click_pos):
                            if idx in unlocked_skins:
                                selected_skin = idx
                                save_game_data()
                            else:
                                price = skin_prices[idx] if idx < len(skin_prices) else 500
                                if coins >= price:
                                    coins -= price
                                    unlocked_skins.add(idx)
                                    selected_skin = idx
                                    save_game_data()
                    if back_btn_rect.collidepoint(click_pos):
                        game_state = "MENU"
                elif game_state == "PLAYING":
                    if is_game_over:
                        if game_over_menu_btn.collidepoint(click_pos):
                            game_state = "MENU"
                            is_game_over = False
                        elif game_over_restart_btn.collidepoint(click_pos):
                            start_game_session(is_arena=arena_mode)
                    else:
                        if in_game_exit_rect.collidepoint(click_pos):
                            game_state = "MENU"
                        elif card_selection_active:
                            if current_cards:
                                for i, rect in enumerate(card_rects):
                                    if rect.collidepoint(click_pos):
                                        if i < len(current_cards):
                                            selected_card_ability = current_cards[i]
                                            ability_cooldown_timer = 0.0
                                        card_selection_active = False

        if game_state == "MENU":
            window.fill((240, 245, 250))

            if title_font:
                title_surf = title_font.render("SNOWY HELL", True, (20, 20, 50))
                if title_surf:
                    window.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 3 - 60)))

            pygame.draw.rect(window, (255, 255, 255), checkbox_net_rect, border_radius=6)
            pygame.draw.rect(window, (50, 50, 50), checkbox_net_rect, 2, border_radius=6)
            if use_internet:
                pygame.draw.line(window, (0, 150, 0), (checkbox_net_rect.x + 6, checkbox_net_rect.centery),
                                 (checkbox_net_rect.centerx - 2, checkbox_net_rect.bottom - 8), 4)
                pygame.draw.line(window, (0, 150, 0), (checkbox_net_rect.centerx - 2, checkbox_net_rect.bottom - 8),
                                 (checkbox_net_rect.right - 6, checkbox_net_rect.top + 8), 4)

            pygame.draw.rect(window, (255, 255, 255), checkbox_bots_rect, border_radius=6)
            pygame.draw.rect(window, (50, 50, 50), checkbox_bots_rect, 2, border_radius=6)
            if use_bots:
                pygame.draw.line(window, (0, 150, 0), (checkbox_bots_rect.x + 6, checkbox_bots_rect.centery),
                                 (checkbox_bots_rect.centerx - 2, checkbox_bots_rect.bottom - 8), 4)
                pygame.draw.line(window, (0, 150, 0), (checkbox_bots_rect.centerx - 2, checkbox_bots_rect.bottom - 8),
                                 (checkbox_bots_rect.right - 6, checkbox_bots_rect.top + 8), 4)

            if menu_font:
                net_text = menu_font.render("Гра по мережі (Інтернет)", True, (40, 40, 40))
                if net_text:
                    window.blit(net_text, (checkbox_net_rect.right + 15, checkbox_net_rect.y - 2))

                bots_text = menu_font.render("Гра з ботами (багато ботів)", True, (40, 40, 40))
                if bots_text:
                    window.blit(bots_text, (checkbox_bots_rect.right + 15, checkbox_bots_rect.y - 2))

                diff_color = (220, 160, 50) if diff_btn_rect.collidepoint(mouse_pos) else (200, 130, 30)
                pygame.draw.rect(window, diff_color, diff_btn_rect, border_radius=10)
                diff_surf = menu_font.render(f"Складність: {difficulty}", True, (255, 255, 255))
                if diff_surf:
                    window.blit(diff_surf, diff_surf.get_rect(center=diff_btn_rect.center))

                play_color = (70, 180, 80) if play_btn_rect.collidepoint(mouse_pos) else (50, 150, 60)
                pygame.draw.rect(window, play_color, play_btn_rect, border_radius=10)
                play_surf = menu_font.render("PLAY", True, (255, 255, 255))
                if play_surf:
                    window.blit(play_surf, play_surf.get_rect(center=play_btn_rect.center))

                arena_color = (180, 70, 180) if arena_btn_rect.collidepoint(mouse_pos) else (140, 50, 140)
                pygame.draw.rect(window, arena_color, arena_btn_rect, border_radius=10)
                arena_surf = menu_font.render("АРЕНА", True, (255, 255, 255))
                if arena_surf:
                    window.blit(arena_surf, arena_surf.get_rect(center=arena_btn_rect.center))

                shop_color = (70, 130, 200) if shop_btn_rect.collidepoint(mouse_pos) else (50, 100, 170)
                pygame.draw.rect(window, shop_color, shop_btn_rect, border_radius=10)
                shop_surf = menu_font.render("SKINS SHOP", True, (255, 255, 255))
                if shop_surf:
                    window.blit(shop_surf, shop_surf.get_rect(center=shop_btn_rect.center))

                exit_color = (200, 70, 70) if exit_btn_rect.collidepoint(mouse_pos) else (170, 50, 50)
                pygame.draw.rect(window, exit_color, exit_btn_rect, border_radius=10)
                exit_surf = menu_font.render("ВИХІД", True, (255, 255, 255))
                if exit_surf:
                    window.blit(exit_surf, exit_surf.get_rect(center=exit_btn_rect.center))

        elif game_state == "ARENA_MENU":
            window.fill((240, 245, 250))

            if title_font:
                title_surf = title_font.render("АРЕНА - ВИБІР СКЛАДНОСТІ", True, (20, 20, 50))
                if title_surf:
                    window.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 4)))

            if menu_font:
                easy_col = (80, 200, 100) if arena_easy_rect.collidepoint(mouse_pos) else (60, 160, 80)
                pygame.draw.rect(window, easy_col, arena_easy_rect, border_radius=10)
                easy_surf = menu_font.render("1. Легкий (100 ботів)", True, (255, 255, 255))
                if easy_surf:
                    window.blit(easy_surf, easy_surf.get_rect(center=arena_easy_rect.center))

                norm_col = (220, 180, 50) if arena_norm_rect.collidepoint(mouse_pos) else (190, 150, 30)
                pygame.draw.rect(window, norm_col, arena_norm_rect, border_radius=10)
                norm_surf = menu_font.render("2. Нормальний (150 ботів)", True, (255, 255, 255))
                if norm_surf:
                    window.blit(norm_surf, norm_surf.get_rect(center=arena_norm_rect.center))

                hard_col = (220, 80, 80) if arena_hard_rect.collidepoint(mouse_pos) else (180, 50, 50)
                pygame.draw.rect(window, hard_col, arena_hard_rect, border_radius=10)
                hard_surf = menu_font.render("3. Складний (200 ботів)", True, (255, 255, 255))
                if hard_surf:
                    window.blit(hard_surf, hard_surf.get_rect(center=arena_hard_rect.center))

                back_col = (120, 120, 140) if arena_back_rect.collidepoint(mouse_pos) else (90, 90, 110)
                pygame.draw.rect(window, back_col, arena_back_rect, border_radius=10)
                back_surf = menu_font.render("BACK", True, (255, 255, 255))
                if back_surf:
                    window.blit(back_surf, back_surf.get_rect(center=arena_back_rect.center))

        elif game_state == "SHOP":
            window.fill((230, 235, 245))

            if title_font:
                title_surf = title_font.render(f"SKINS SHOP (Монети: {coins})", True, (20, 20, 50))
                if title_surf:
                    window.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 12 + 10)))

            skin_names = [
                "Класичний", "Очі", "Мішень", "Неон", "Зірочка",
                "Усмішка", "Котеня", "Пірат", "Сонце", "Чорна діра", "Динаміт"
            ]

            for idx, rect in enumerate(skin_btn_rects):
                if idx >= len(skin_names):
                    break
                border_color = (0, 200, 0) if selected_skin == idx else (120, 120, 120)
                pygame.draw.rect(window, (255, 255, 255), rect, border_radius=10)
                pygame.draw.rect(window, border_color, rect, 3, border_radius=10)

                sample_color = SKIN_COLORS[idx % len(SKIN_COLORS)]
                pygame.draw.circle(window, sample_color, (rect.x + 35, rect.centery), 16)
                pygame.draw.circle(window, (30, 30, 30), (rect.x + 35, rect.centery), 16, 2)

                if game_font:
                    if idx in unlocked_skins:
                        label = f"{skin_names[idx]} (Куплено)" if idx > 0 else skin_names[idx]
                        text_color = (0, 120, 0) if selected_skin == idx else (40, 40, 40)
                    else:
                        price = skin_prices[idx] if idx < len(skin_prices) else 500
                        label = f"{skin_names[idx]} - {price} м."
                        text_color = (180, 50, 50)

                    name_surf = game_font.render(label, True, text_color)
                    if name_surf:
                        name_rect = name_surf.get_rect(midleft=(rect.x + 75, rect.centery))
                        window.blit(name_surf, name_rect)

            back_color = (180, 70, 70) if back_btn_rect.collidepoint(mouse_pos) else (150, 50, 50)
            pygame.draw.rect(window, back_color, back_btn_rect, border_radius=10)
            if menu_font:
                back_surf = menu_font.render("BACK", True, (255, 255, 255))
                if back_surf:
                    window.blit(back_surf, back_surf.get_rect(center=back_btn_rect.center))

        elif game_state == "PLAYING":
            if player and not card_selection_active and not is_game_over:
                player.update()

            all_persons = [player] + bots if player else bots
            if (use_bots or arena_mode) and not card_selection_active and not is_game_over:
                for bot in bots:
                    bot.update(all_persons)

            if use_internet and sock and not arena_mode and not is_game_over and not card_selection_active:
                packet = {
                    "x": player.x, "y": player.y, "r": player.r,
                    "color": player.color, "nickname": nickname,
                    "is_boosting": player.is_boosting,
                    "skin_type": player.skin_type
                }
                try:
                    sock.sendto(pickle.dumps(packet), (server_ip, 8888))
                    data, _ = sock.recvfrom(65535)
                    world_data = pickle.loads(data)
                except (BlockingIOError, socket.error, Exception):
                    pass

            # 1. Зіткнення з їжею
            if player and not card_selection_active and not is_game_over:
                for person in all_persons:
                    for eat in eats:
                        dist = math.hypot(eat.x - person.x, eat.y - person.y)
                        if dist <= eat.r + person.r:
                            person.r = math.sqrt(person.r ** 2 + 3.0)
                            eat.x = random.randint(-MAP_SIZE, MAP_SIZE)
                            eat.y = random.randint(-MAP_SIZE, MAP_SIZE)

            # 2. Поїдання персонажів / ботів
            milestones = [10, 25, 35, 45, 55, 65, 75, 85, 100]
            if player and not card_selection_active and not is_game_over:
                for p1 in list(all_persons):
                    for p2 in list(all_persons):
                        if p1 == p2:
                            continue
                        if hasattr(p1, 'r') and hasattr(p2, 'r') and p1.r > p2.r * 1.05:
                            distance = math.hypot(p1.x - p2.x, p1.y - p2.y)
                            if distance <= p1.r:
                                p1.r = math.sqrt(p1.r ** 2 + p2.r ** 2)

                                if p1 == player:
                                    total_kills += 1
                                    if not arena_mode:
                                        if difficulty == "Легкий":
                                            coins += 3
                                        elif difficulty == "Складний":
                                            coins += 10
                                        else:
                                            coins += 5
                                        save_game_data()

                                        if len(bots) < arena_total_bots:
                                            b_speed = 1.0 if difficulty == "Легкий" else (
                                                2.2 if difficulty == "Складний" else 1.5)
                                            b_r = float(max(10, random.randint(int(player.r * 0.8), int(player.r))))
                                            bots.append(Bot(random.randint(-MAP_SIZE // 2, MAP_SIZE // 2),
                                                            random.randint(-MAP_SIZE // 2, MAP_SIZE // 2), b_r,
                                                            (80, 120, 255), random.choice(ALL_BOT_NAMES), speed=b_speed,
                                                            skin_type=random.randint(0, 9)))
                                    else:
                                        if total_kills in milestones and total_kills != last_milestone_checked:
                                            last_milestone_checked = total_kills
                                            if not dynamite_unlocked and random.random() <= 0.05:
                                                dynamite_unlocked = True
                                                unlocked_skins.add(10)
                                                save_game_data()
                                            current_cards = random.sample(ALL_ARENA_CARDS, 3)
                                            card_selection_active = True

                                        if len(bots) < arena_total_bots:
                                            b_speed = 1.0 if difficulty == "Легкий" else (
                                                2.2 if difficulty == "Складний" else 1.5)
                                            b_r = float(max(10, random.randint(int(player.r * 0.8), int(player.r))))
                                            bots.append(Bot(random.randint(-MAP_SIZE // 2, MAP_SIZE // 2),
                                                            random.randint(-MAP_SIZE // 2, MAP_SIZE // 2), b_r,
                                                            (80, 120, 255), random.choice(ALL_BOT_NAMES), speed=b_speed,
                                                            skin_type=random.randint(0, 9)))

                                        if total_kills >= arena_total_bots:
                                            coins += 100
                                            save_game_data()
                                            game_state = "MENU"

                                if p2 == player:
                                    is_game_over = True
                                    break
                                elif isinstance(p2, Bot):
                                    p2.respawn(player.r if player else 15.0)

            # Очищення екрана та малювання
            window.fill((255, 255, 255))
            if player:
                scale = max(0.25, min(50.0 / player.r, 1.2))
            else:
                scale = 1.0

            if player and game_state == "PLAYING":
                for eat in eats:
                    eat.draw(window, player, scale)

                if use_bots or arena_mode:
                    for bot in bots:
                        bot.draw(window, player, scale)

                if use_internet and "clients" in world_data and not arena_mode:
                    for addr, client in world_data["clients"].items():
                        if client["nickname"] != nickname:
                            net_person = Person(client["x"], client["y"], client["r"], client["color"],
                                                client["nickname"], client.get("skin_type", 0))
                            net_person.draw(window, player, scale)

                player.draw(window, player, scale)
                player.draw_hud(window, coins, total_kills)

                # Малювання червоного променя при пострілі (ЛКМ)
                if arena_mode and selected_card_ability == "Промінь (ЛКМ)" and laser_active_timer > 0:
                    mx, my = pygame.mouse.get_pos()
                    pygame.draw.line(window, (255, 0, 0), (WIDTH // 2, HEIGHT // 2), (mx, my), 6)

                if arena_mode:
                    circle_center = (WIDTH - 70, HEIGHT - 90)
                    circle_radius = 40

                    pygame.draw.circle(window, (240, 240, 240), circle_center, circle_radius)
                    pygame.draw.circle(window, (80, 80, 120), circle_center, circle_radius, 3)

                    if ability_cooldown_timer > 0:
                        max_cd = 5.0
                        progress = ability_cooldown_timer / max_cd
                        inner_r = int(circle_radius * progress)
                        pygame.draw.circle(window, (180, 180, 220), circle_center, inner_r)

                        if hud_font:
                            cd_text = hud_font.render(f"{round(ability_cooldown_timer, 1)}с", True, (50, 50, 50))
                            window.blit(cd_text, cd_text.get_rect(center=circle_center))
                    else:
                        if hud_font:
                            ready_text = hud_font.render("ГОТОВО", True, (0, 150, 0))
                            window.blit(ready_text, ready_text.get_rect(center=circle_center))

                    if selected_card_ability and hud_font:
                        card_lbl = hud_font.render(selected_card_ability, True, (40, 40, 40))
                        window.blit(card_lbl,
                                    card_lbl.get_rect(midtop=(circle_center[0], circle_center[1] + circle_radius + 8)))

                exit_bg = (220, 70, 70) if in_game_exit_rect.collidepoint(mouse_pos) else (180, 50, 50)
                pygame.draw.rect(window, exit_bg, in_game_exit_rect, border_radius=8)
                pygame.draw.rect(window, (50, 50, 50), in_game_exit_rect, 2, border_radius=8)
                if menu_font:
                    ex_surf = menu_font.render("ВИХІД", True, (255, 255, 255))
                    if ex_surf:
                        window.blit(ex_surf, ex_surf.get_rect(center=in_game_exit_rect.center))

                if dynamite_active and game_font:
                    txt = game_font.render("алахадбар", True, (0, 0, 0))
                    window.blit(txt, (WIDTH // 2 - 50, 60))

                if is_game_over:
                    pygame.draw.rect(window, (40, 40, 60), (WIDTH // 2 - 220, HEIGHT // 2 - 100, 440, 200),
                                     border_radius=15)
                    pygame.draw.rect(window, (120, 120, 180), (WIDTH // 2 - 220, HEIGHT // 2 - 100, 440, 200), 3,
                                     border_radius=15)

                    if title_font:
                        over_surf = title_font.render("ВИ ПРОГРАЛИ", True, (255, 80, 80))
                        window.blit(over_surf, over_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 45)))

                    if menu_font:
                        m_col = (100, 100, 140) if game_over_menu_btn.collidepoint(mouse_pos) else (70, 70, 100)
                        pygame.draw.rect(window, m_col, game_over_menu_btn, border_radius=8)
                        m_surf = menu_font.render("МЕНЮ", True, (255, 255, 255))
                        window.blit(m_surf, m_surf.get_rect(center=game_over_menu_btn.center))

                        r_col = (70, 180, 80) if game_over_restart_btn.collidepoint(mouse_pos) else (50, 140, 60)
                        pygame.draw.rect(window, r_col, game_over_restart_btn, border_radius=8)
                        r_surf = menu_font.render("ЗНОВУ", True, (255, 255, 255))
                        window.blit(r_surf, r_surf.get_rect(center=game_over_restart_btn.center))

                elif card_selection_active and menu_font and current_cards:
                    pygame.draw.rect(window, (30, 30, 50), (WIDTH // 2 - 380, HEIGHT // 2 - 160, 760, 320),
                                     border_radius=15)
                    pygame.draw.rect(window, (100, 100, 150), (WIDTH // 2 - 380, HEIGHT // 2 - 160, 760, 320), 3,
                                     border_radius=15)

                    title_c = menu_font.render("ВИБЕРІТЬ КАРТКУ ЗДІБНОСТЕЙ", True, (255, 255, 255))
                    window.blit(title_c, title_c.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 110)))

                    for i, rect in enumerate(card_rects):
                        c_col = (70, 130, 180) if rect.collidepoint(mouse_pos) else (50, 90, 130)
                        pygame.draw.rect(window, c_col, rect, border_radius=10)
                        pygame.draw.rect(window, (200, 200, 250), rect, 2, border_radius=10)

                        if i < len(current_cards) and game_font:
                            try:
                                card_text = game_font.render(str(current_cards[i]), True, (255, 255, 255))
                                if card_text:
                                    window.blit(card_text, card_text.get_rect(center=rect.center))
                            except:
                                pass

        pygame.display.update()
        clock.tick(FPS)
    except Exception as e:
        print("Помилка в ігровому циклі:")
        traceback.print_exc()
        break

pygame.quit()