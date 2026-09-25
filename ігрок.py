from pygame import *
import math
import random

WIDTH = 1400
HEIGHT = 777
FPS = 140

MAP_SIZE = 3000


init()
window = display.set_mode((WIDTH, HEIGHT))
clock = time.Clock()

class Person:
    def __init__(self, x, y, r, color, nickname):
        self.x = x
        self.y = y
        self.r = r
        self.color = color
        self.nickname = nickname

    def update(self):
        pass

    def check_collision(self, other):
        if self.r <= other.r * 1.10:
            return False

        distance = math.hypot(self.x - other.x, self.y - other.y)
        return distance <= self.r



    def draw(self, screen, person, scale):
        def draw(self, screen, person, scale):
            sx = int((self.x - person.x) * scale + WIDTH // 2)
            sy = int((self.y - person.y) * scale + HEIGHT // 2)
            sr = int(self.r - person.r)

            draw.circle(screen, self.color, (sx, sy), max(1, sr))
        # todo add nickname

class Player(Person):
    def __init__(self, x, y, r, color, nickname):
        super().__init__(x, y, r, color, nickname)

    def update(self):
        mx, my = mouse.get_pos()
        self.x = mx
        self.y = my

class Bot(Person):
    def __init__(self, x, y, r, color, nickname, speed=2):
        super().__init__(x, y, r, color, nickname)
        self.speed = speed
        # Випадковий напрямок руху по осях X та Y
        self.dx = random.choice([-1, 1]) * self.speed
        self.dy = random.choice([-1, 1]) * self.speed

    def update(self):
        # Рухаємо бота
        self.x += self.dx
        self.y += self.dy

        # Відскок від меж вікна, щоб боти не вилітали за екрани
        if self.x - self.r <= 0 or self.x + self.r >= WIDTH:
            self.dx *= -1
        if self.y - self.r <= 0 or self.y + self.r >= HEIGHT:
            self.dy *= -1


class Eat(Person):
    def __init__(self, x, y, r, color, nickname):
        super().__init__(x, y, r, color, nickname)

    def check_collision(self, player_x, player_y, player_r):
        distance = math.hypot(self.x - player_x, self.y - player_y)
        return distance <= self.r + player_r

# Створюємо гравця
player = Player(WIDTH // 2, HEIGHT // 2, 10, "red", "dsdjsusfu")

# Створюємо їжу
eats = [
    Eat(
        random.randint(-MAP_SIZE, MAP_SIZE),
        random.randint(-MAP_SIZE, MAP_SIZE),
        10,
        ((random.randint(0,255)), (random.randint(0,255)), (random.randint(0,255))),
        None
    )
    for i in range(300)
]

# Створюємо список ботів
bots = [
    Bot(
        random.randint(100, WIDTH - 100),
        random.randint(100, HEIGHT - 100),
        10,
        "blue",
        f"Bot_{i}"
    )
    for i in range(5)
]

running = True
while running:
    for e in event.get():
        if e.type == QUIT:
            running = False

    # 1. Обновляем позиції
    player.update()
    for bot in bots:
        bot.update()

    persons = [player] + bots
    for person in persons:
        for eat in eats:
            if eat.check_collision(person.x, person.y, person.r):
                person.r *= 1.05

                eat.x = random.randint(-MAP_SIZE, MAP_SIZE)
                eat.y = random.randint(-MAP_SIZE, MAP_SIZE)

        if player.check_collision(person):
            person.r = math.sqrt(person.x ** 2 + person.y ** 2 * 0.5)
            persons.remove(person)
            bots.remove(person)

    # 2. Очищаем экран
    window.fill("white")

    # 3. Рисуем объекты поверх очищенного экрана

    scale = max(0,25, min(50.0 / player.r, 1.2))

    for bot in bots:
        bot.draw(window,player, scale)

    for eat in eats:
        eat.draw(window, player, scale)

    player.draw(window, player, scale)

    # 4. Обновляем дисплей
    display.update()
    clock.tick(FPS)
quit()