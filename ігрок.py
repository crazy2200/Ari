import pygame
import math
import random
import socket
import pickle
import os

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
    (255, 80, 80),  # Класичний
    (80, 200, 120),  # Очі
    (255, 165, 0),  # Мішень
    (0, 255, 255),  # Неон
    (255, 215, 0),  # Зірочка
    (238, 130, 238),  # Усмішка
    (147, 112, 219),  # Котеня
    (70, 130, 180),  # Пірат
    (255, 69, 0),  # Сонце
    (50, 50, 50)  # Чорна діра
]

# Збереження та завантаження прогресу
SAVE_FILE = "savegame.dat"
coins = 0
unlocked_skins = {0}
selected_skin = 0
difficulty = "Нормальний"  # Легкий, Нормальний, Складний


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
        if self.is_boosting:
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

    def draw_hud(self, screen, coins_val):
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
            coin_surf = game_font.render(f"Монети: {coins_val} | Складність: {difficulty}", True, (200, 150, 0))
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

    def respawn(self):
        self.x = random.randint(-MAP_SIZE // 2, MAP_SIZE // 2)
        self.y = random.randint(-MAP_SIZE // 2, MAP_SIZE // 2)
        self.r = float(random.randint(12, 18))
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


# Налаштування
game_state = "MENU"
use_internet = False
use_bots = True

skin_prices = [0, 50, 100, 150, 200, 250, 300, 350, 400, 450]

nickname = "dsdjsusfu"
server_ip = "localhost"

checkbox_net_rect = pygame.Rect(WIDTH // 2 - 180, HEIGHT // 2 - 90, 30, 30)
checkbox_bots_rect = pygame.Rect(WIDTH // 2 - 180, HEIGHT // 2 - 30, 30, 30)

diff_btn_rect = pygame.Rect(WIDTH // 2 - 180, HEIGHT // 2 + 30, 360, 45)
play_btn_rect = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 + 90, 260, 45)
shop_btn_rect = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 + 145, 260, 45)

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
]
back_btn_rect = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 + 135, 260, 45)

sock = None
player = None
eats = []
bots = []
world_data = {"clients": {}, "bots": [], "eats": []}


def start_game_session():
    global sock, player, eats, bots
    player = Player(0, 0, 15.0, (255, 80, 80), nickname, skin_type=selected_skin)

    eats = [
        Eat(random.randint(-MAP_SIZE, MAP_SIZE), random.randint(-MAP_SIZE, MAP_SIZE), 10,
            (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        for _ in range(300)
    ]

    if use_bots:
        if difficulty == "Легкий":
            bot_speed = 1.0
        elif difficulty == "Складний":
            bot_speed = 2.2
        else:
            bot_speed = 1.5

        bots = [
            Bot(random.randint(-MAP_SIZE // 2, MAP_SIZE // 2), random.randint(-MAP_SIZE // 2, MAP_SIZE // 2),
                float(random.randint(12, 25)), (80, 120, 255), random.choice(ALL_BOT_NAMES), speed=bot_speed,
                skin_type=random.randint(0, 9))
            for _ in range(30)
        ]
    else:
        bots = []

    if use_internet:
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

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if game_state == "PLAYING":
                    if e.key == pygame.K_SPACE:
                        if player:
                            player.toggle_boost()
                    elif e.key in (pygame.K_LALT, pygame.K_RALT):
                        coins += 1000
                        save_game_data()
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if game_state == "MENU":
                    if checkbox_net_rect.collidepoint(mouse_pos):
                        use_internet = not use_internet
                    elif checkbox_bots_rect.collidepoint(mouse_pos):
                        use_bots = not use_bots
                    elif diff_btn_rect.collidepoint(mouse_pos):
                        if difficulty == "Легкий":
                            difficulty = "Нормальний"
                        elif difficulty == "Нормальний":
                            difficulty = "Складний"
                        else:
                            difficulty = "Легкий"
                    elif play_btn_rect.collidepoint(mouse_pos):
                        start_game_session()
                        game_state = "PLAYING"
                    elif shop_btn_rect.collidepoint(mouse_pos):
                        game_state = "SHOP"
                elif game_state == "SHOP":
                    for idx, rect in enumerate(skin_btn_rects):
                        if rect.collidepoint(mouse_pos):
                            if idx in unlocked_skins:
                                selected_skin = idx
                                save_game_data()
                            else:
                                price = skin_prices[idx]
                                if coins >= price:
                                    coins -= price
                                    unlocked_skins.add(idx)
                                    selected_skin = idx
                                    save_game_data()
                    if back_btn_rect.collidepoint(mouse_pos):
                        game_state = "MENU"

        if game_state == "MENU":
            window.fill((240, 245, 250))

            if title_font:
                title_surf = title_font.render("SNOWY HELL", True, (20, 20, 50))
                if title_surf:
                    window.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 3 - 40)))

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

                shop_color = (70, 130, 200) if shop_btn_rect.collidepoint(mouse_pos) else (50, 100, 170)
                pygame.draw.rect(window, shop_color, shop_btn_rect, border_radius=10)
                shop_surf = menu_font.render("SKINS SHOP", True, (255, 255, 255))
                if shop_surf:
                    window.blit(shop_surf, shop_surf.get_rect(center=shop_btn_rect.center))

        elif game_state == "SHOP":
            window.fill((230, 235, 245))

            if title_font:
                title_surf = title_font.render(f"SKINS SHOP (Монети: {coins})", True, (20, 20, 50))
                if title_surf:
                    window.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 12 + 10)))

            skin_names = [
                "Класичний", "Очі", "Мішень", "Неон", "Зірочка",
                "Усмішка", "Котеня", "Пірат", "Сонце", "Чорна діра"
            ]

            for idx, rect in enumerate(skin_btn_rects):
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
                        label = f"{skin_names[idx]} - {skin_prices[idx]} м."
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
            if player:
                player.update()

            all_persons = [player] + bots if player else bots
            if use_bots:
                for bot in bots:
                    bot.update(all_persons)

            if use_internet and sock:
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
            if player:
                for person in all_persons:
                    for eat in eats:
                        dist = math.hypot(eat.x - person.x, eat.y - person.y)
                        if dist <= eat.r + person.r:
                            person.r = math.sqrt(person.r ** 2 + 3.0)
                            eat.x = random.randint(-MAP_SIZE, MAP_SIZE)
                            eat.y = random.randint(-MAP_SIZE, MAP_SIZE)

            # 2. Безпечне взаємне поїдання через копію списку
            persons_copy = list(all_persons)
            for p1 in persons_copy:
                for p2 in persons_copy:
                    if p1 == p2:
                        continue
                    if hasattr(p1, 'r') and hasattr(p2, 'r') and p1.r > p2.r * 1.05:
                        distance = math.hypot(p1.x - p2.x, p1.y - p2.y)
                        if distance <= p1.r:
                            p1.r = math.sqrt(p1.r ** 2 + p2.r ** 2)

                            if player and p1 == player:
                                if difficulty == "Легкий":
                                    coins += 3
                                elif difficulty == "Складний":
                                    coins += 10
                                else:
                                    coins += 5
                                save_game_data()

                            if p2 == player:
                                game_state = "MENU"
                            elif isinstance(p2, Bot):
                                p2.respawn()

            # Очищення екрана та малювання
            window.fill((255, 255, 255))
            if player:
                scale = max(0.25, min(50.0 / player.r, 1.2))
            else:
                scale = 1.0

            # Малюємо їжу
            if player:
                for eat in eats:
                    eat.draw(window, player, scale)

                # Малюємо ботів
                if use_bots:
                    for bot in bots:
                        bot.draw(window, player, scale)

                # Малюємо інших гравців по мережі
                if use_internet and "clients" in world_data:
                    for addr, client in world_data["clients"].items():
                        if client["nickname"] != nickname:
                            net_person = Person(client["x"], client["y"], client["r"], client["color"],
                                                client["nickname"], client.get("skin_type", 0))
                            net_person.draw(window, player, scale)

                # Малюємо себе та HUD з монетами
                player.draw(window, player, scale)
                player.draw_hud(window, coins)

        pygame.display.update()
        clock.tick(FPS)
    except Exception as e:
        print("Помилка в ігровому циклі:", e)
        break

pygame.quit()