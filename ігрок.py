from pygame import *
import pygame
import random

WIDTH = 1588
HEIGHT = 999
FPS = 140

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

    def draw(self, screen):
        draw.circle(screen, self.color, (self.x, self.y), self.r)
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
        ...


# Створюємо гравця
player = Player(WIDTH // 2, HEIGHT // 2, 10, "red", "dsdjsusfu")

# Створюємо їжу
eats = [
    Eat(
        random.randint(-3000, 3000),
        random.randint(-3000, 3000),
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
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

    # 1. Обновляем позиції
    player.update()
    for bot in bots:
        bot.update()

    # 2. Очищаем экран
    window.fill("white")

    # 3. Рисуем объекты поверх очищенного экрана
    for bot in bots:
        bot.draw(window)

    for eat in eats:
        eat.draw(window)

    player.draw(window)

    # 4. Обновляем дисплей
    display.update()
    clock.tick(FPS)

pygame.quit()