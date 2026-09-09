from pygame import *
import pygame

WIDTH = 1588
HEIGHT = 1000
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
        # Исправлено: убран extra-аргумент self
        super().__init__(x, y, r, color, nickname)

    def update(self):
        mx, my = mouse.get_pos()
        self.x = mx
        self.y = my

player = Player(WIDTH // 2, HEIGHT // 2, 10, "red", "dsdjsusfu")

running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

    # 1. Обновляем позицию
    player.update()

    # 2. Очищаем экран
    window.fill("white")

    # 3. Рисуем объекты поверх очищенного экрана
    player.draw(window)

    # 4. Обновляем дисплей
    display.update()
    clock.tick(FPS)

pygame.quit()